"""Servicio de Recomendaciones — módulo de la Capa 2 (ADD It.5).

- Precálculo asíncrono: consume `reserva.cambiada` y `recomendacion.solicitada`
  y guarda las sugerencias ya puntuadas. La API solo lee (no penaliza QA-R2).
- Disrupciones: si una reserva se cancela, propone alternativas y avisa al viajero.
- Human-in-the-loop: aceptar, rechazar (con motivo) o ajustar parámetros
  publica `recomendacion.feedback`; un consumidor actualiza los pesos del viajero
  y recalcula, fuera del camino crítico.
- Privacidad: usa el historial propio del viajero y agregados anonimizados del OLAP.
- Disponibilidad: si un catálogo no responde se omite (el resto sigue); el
  módulo entero es una función no crítica que se suspende bajo sobrecarga.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import asdict
from typing import Any

from trotamundos.asincrono.bus_eventos import BusEventos
from trotamundos.datos.almacen_analitico import AlmacenAnalitico
from trotamundos.datos.repositorios import RepositorioNotificaciones, RepositorioReservas, RepositorioViajes
from trotamundos.dominio import eventos
from trotamundos.dominio.modelo import FuenteReserva, Reserva, ahora_utc
from trotamundos.gestion_viajes.servicio_reservas import ServicioReservas
from trotamundos.integracion.puertos import BusquedaOfertas, ErrorProveedor, Oferta
from trotamundos.integracion.registro import RegistroAdaptadores
from trotamundos.recomendacion.estrategias import (
    ContextoUsuario,
    EstrategiaPuntuacion,
    Puntuacion,
    actualizar_pesos,
)
from trotamundos.recomendacion.generador import detectar_necesidades
from trotamundos.recomendacion.modelo import (
    SUGERENCIAS_POR_GRUPO,
    EstadoRecomendacion,
    Motivo,
    Necesidad,
    Parametros,
    Recomendacion,
    id_recomendacion,
    promedio,
)
from trotamundos.recomendacion.repositorio import RepositorioRecomendaciones

log = logging.getLogger(__name__)


class RecomendacionNoDisponible(LookupError):
    pass


class ServicioRecomendaciones:
    def __init__(self, repo: RepositorioRecomendaciones, viajes: RepositorioViajes, reservas: RepositorioReservas,
                 servicio_reservas: ServicioReservas, adaptadores: RegistroAdaptadores, almacen: AlmacenAnalitico,
                 bus: BusEventos, notificaciones: RepositorioNotificaciones, estrategia: EstrategiaPuntuacion) -> None:
        self.repo = repo
        self.viajes = viajes
        self.reservas = reservas
        self.servicio_reservas = servicio_reservas
        self.adaptadores = adaptadores
        self.almacen = almacen
        self.bus = bus
        self.notificaciones = notificaciones
        self.estrategia = estrategia

    # ---- Precálculo ------------------------------------------------------- #

    def _contexto(self, usuario_id: str) -> ContextoUsuario:
        parametros, pesos = self.repo.preferencias(usuario_id)
        historial = self.reservas.de_usuario(usuario_id)
        total = max(len(historial), 1)
        return ContextoUsuario(
            pesos=pesos, parametros=parametros,
            proveedores_usados={k: v / total for k, v in Counter(r.proveedor for r in historial).items()},
            tipos_usados={k: v / total for k, v in Counter(r.tipo for r in historial).items()},
            aceptaciones_globales=self.almacen.aceptaciones_por_producto(),
        )

    def _buscar(self, necesidad: Necesidad) -> list[Oferta]:
        ofertas: list[Oferta] = []
        for catalogo in self.adaptadores.catalogos.todos():
            if catalogo.tipo_reserva not in necesidad.tipos:
                continue
            try:
                ofertas += catalogo.buscar(BusquedaOfertas(catalogo.tipo_reserva, necesidad.ciudad_destino,
                                                           necesidad.desde, necesidad.hasta, necesidad.ciudad_origen))
            except ErrorProveedor as e:  # un catálogo caído no impide sugerir con los demás
                log.warning("Catálogo %s no disponible: %s", catalogo.codigo, e)
        return ofertas

    @staticmethod
    def _diversificar(puntuadas: list[Puntuacion]) -> list[Puntuacion]:
        """Una sugerencia por producto (no el mismo tren en tres días distintos).

        Ante igual puntaje se prefiere la salida más tardía: más tiempo en la ciudad.
        """
        elegidas: dict[str, Puntuacion] = {}
        for p in sorted(puntuadas, key=lambda p: (p.puntaje, p.oferta.inicio), reverse=True):
            elegidas.setdefault(p.oferta.titulo, p)
        return list(elegidas.values())[:SUGERENCIAS_POR_GRUPO]

    def recalcular_usuario(self, usuario_id: str) -> int:
        ahora = ahora_utc()
        contexto = self._contexto(usuario_id)
        rechazadas = self.repo.ofertas_rechazadas(usuario_id)
        activos = {v.id: v for v in self.viajes.de_usuario(usuario_id) if v.fin >= ahora}
        self.repo.eliminar_pendientes_de_viajes_inactivos(usuario_id, set(activos))
        total = 0
        for viaje in activos.values():
            nuevas: list[Recomendacion] = []
            for necesidad in detectar_necesidades(viaje, self.reservas.de_viaje(viaje.id), ahora):
                candidatas = [o for o in self._buscar(necesidad)
                              if o.id not in rechazadas and contexto.parametros.admite(o)]
                for p in self._diversificar(self.estrategia.puntuar(candidatas, contexto)):
                    nuevas.append(Recomendacion(
                        id=id_recomendacion(usuario_id, necesidad.grupo, p.oferta.id), usuario_id=usuario_id,
                        viaje_id=viaje.id, grupo=necesidad.grupo, motivo=necesidad.motivo,
                        descripcion=necesidad.descripcion, oferta=p.oferta, puntaje=p.puntaje,
                        caracteristicas=p.caracteristicas, reserva_origen_id=necesidad.reserva_origen_id,
                        explicacion=p.explicacion,
                    ))
            grupos_nuevos = self.repo.reemplazar_pendientes(usuario_id, viaje.id, nuevas)
            total += len(nuevas)
            for grupo in grupos_nuevos:
                rec = next(r for r in nuevas if r.grupo == grupo)
                if rec.motivo == Motivo.DISRUPCION:
                    self.notificaciones.notificar(
                        f"usuario:{usuario_id}", "recomendacion.disrupcion",
                        f"{rec.descripcion}: tenemos alternativas para tu viaje «{viaje.nombre}».")
        return total

    def solicitar(self, usuario_id: str, origen: str) -> str:
        return self.bus.publicar(eventos.RECOMENDACION_SOLICITADA, {"usuario_id": usuario_id, "origen": origen})

    def solicitar_para_todos(self) -> int:
        usuarios = {v.usuario_id for v in self.viajes.no_archivados()}
        for usuario_id in usuarios:
            self.solicitar(usuario_id, "planificador")
        return len(usuarios)

    # ---- Consultas -------------------------------------------------------- #

    def listar(self, usuario_id: str, viaje_id: str | None = None) -> list[Recomendacion]:
        return self.repo.pendientes(usuario_id, viaje_id)

    def preferencias(self, usuario_id: str) -> tuple[Parametros, dict[str, float]]:
        return self.repo.preferencias(usuario_id)

    # ---- Human-in-the-loop ------------------------------------------------ #

    def _pendiente(self, usuario_id: str, rec_id: str) -> Recomendacion:
        rec = self.repo.obtener(rec_id)
        if rec is None or rec.usuario_id != usuario_id or rec.estado != EstadoRecomendacion.PENDIENTE:
            raise RecomendacionNoDisponible(rec_id)
        return rec

    def aceptar(self, usuario_id: str, email: str, rec_id: str) -> Reserva:
        """Reserva la oferta en el proveedor y la incorpora al viaje."""
        rec = self._pendiente(usuario_id, rec_id)
        catalogo = self.adaptadores.catalogos.obtener(rec.oferta.proveedor)
        codigo = catalogo.reservar(rec.oferta.id, email)  # puede lanzar ErrorProveedor
        confirmacion = self.adaptadores.proveedores.obtener(rec.oferta.proveedor).consultar_reserva(codigo)
        reserva = self.servicio_reservas.aplicar_actualizacion_externa(usuario_id, confirmacion,
                                                                      FuenteReserva.PROVEEDOR)
        otras = [r for r in self.repo.del_grupo(usuario_id, rec.grupo)
                 if r.id != rec.id and r.estado == EstadoRecomendacion.PENDIENTE]
        self.repo.resolver(rec.id, EstadoRecomendacion.ACEPTADA)
        self.repo.descartar_resto_del_grupo(usuario_id, rec.grupo, rec.id)
        self._publicar_feedback(usuario_id, rec, "aceptada", otras)
        return reserva

    def rechazar(self, usuario_id: str, rec_id: str, motivo_rechazo: str | None) -> None:
        rec = self._pendiente(usuario_id, rec_id)
        otras = [r for r in self.repo.del_grupo(usuario_id, rec.grupo)
                 if r.id != rec.id and r.estado == EstadoRecomendacion.PENDIENTE]
        self.repo.resolver(rec.id, EstadoRecomendacion.RECHAZADA)
        self._publicar_feedback(usuario_id, rec, "rechazada", otras, motivo_rechazo)

    def ajustar(self, usuario_id: str, parametros: Parametros) -> Parametros:
        _, pesos = self.repo.preferencias(usuario_id)
        self.repo.guardar_preferencias(usuario_id, parametros, pesos)
        self.bus.publicar(eventos.RECOMENDACION_FEEDBACK, {
            "usuario_id": usuario_id, "accion": "ajuste", "momento": ahora_utc().isoformat(),
            "parametros": {k: v for k, v in asdict(parametros).items() if v is not None},
        })
        return parametros

    def _publicar_feedback(self, usuario_id: str, rec: Recomendacion, accion: str, otras: list[Recomendacion],
                           motivo_rechazo: str | None = None) -> None:
        carga: dict[str, Any] = {
            "usuario_id": usuario_id, "accion": accion, "momento": ahora_utc().isoformat(),
            "recomendacion_id": rec.id, "motivo": rec.motivo.value, "tipo": rec.oferta.tipo,
            "proveedor": rec.oferta.proveedor, "producto": rec.oferta.titulo,
            "ciudad": rec.oferta.destino.ciudad, "precio": rec.oferta.precio,
            "caracteristicas": rec.caracteristicas,
            "promedio_grupo": promedio([r.caracteristicas for r in otras]) if otras else rec.caracteristicas,
        }
        if motivo_rechazo:
            carga["motivo_rechazo"] = motivo_rechazo
        self.bus.publicar(eventos.RECOMENDACION_FEEDBACK, carga)

    # ---- Consumidores (procesamiento asíncrono) --------------------------- #

    def al_cambiar_reserva(self, sobre: dict[str, Any]) -> None:
        self.recalcular_usuario(sobre["carga"]["usuario_id"])

    def al_solicitar(self, sobre: dict[str, Any]) -> None:
        self.recalcular_usuario(sobre["carga"]["usuario_id"])

    def al_recibir_feedback(self, sobre: dict[str, Any]) -> None:
        """Aprendizaje online: actualiza los pesos del viajero y recalcula sus sugerencias."""
        c = sobre["carga"]
        if c["accion"] in ("aceptada", "rechazada"):
            parametros, pesos = self.repo.preferencias(c["usuario_id"])
            nuevos = actualizar_pesos(pesos, c["caracteristicas"], c["promedio_grupo"],
                                      aceptada=c["accion"] == "aceptada", motivo_rechazo=c.get("motivo_rechazo"))
            self.repo.guardar_preferencias(c["usuario_id"], parametros, nuevos)
        self.almacen.registrar_feedback(sobre["evento_id"], c)
        self.recalcular_usuario(c["usuario_id"])

