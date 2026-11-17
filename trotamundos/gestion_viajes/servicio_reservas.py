"""Servicio de Reservas — submódulo de "Gestión de viajes y reservas".

ADD It.2, Concepto 1 (ADR-0003): alta, baja, modificación y consulta de
reservas (US-04), validando los datos antes de persistir.
ADD It.2 (ADR-0004): tras cada modificación confirmada invalida la caché del
usuario (política de invalidación) y notifica al Servicio de Itinerarios.
ADD It.3 (ADR-0007/0008): aplica las actualizaciones externas ya traducidas al
modelo canónico (desde correo o proveedores).
ADD It.4 (ADR-0014): publica `reserva.cambiada` para el exportador analítico.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import asdict
from typing import Any

from trotamundos.asincrono.bus_eventos import BusEventos
from trotamundos.datos.cache import GestorCache
from trotamundos.datos.repositorios import RepositorioReservas
from trotamundos.dominio import eventos
from trotamundos.dominio.modelo import (
    ErrorDominio,
    EstadoReserva,
    EstadoSincronizacion,
    FuenteReserva,
    Reserva,
    TIPOS_RESERVA,
    ahora_utc,
    nuevo_id,
)
from trotamundos.gestion_viajes.servicio_itinerarios import ServicioItinerarios
from trotamundos.integracion.puertos import ActualizacionCanonica


class ReservaNoEncontrada(LookupError):
    pass


class ServicioReservas:
    def __init__(self, repo: RepositorioReservas, itinerarios: ServicioItinerarios,
                 cache: GestorCache, bus: BusEventos) -> None:
        self.repo = repo
        self.itinerarios = itinerarios
        self.cache = cache
        self.bus = bus
        # Latencias fuente→persistencia de actualizaciones externas (medición de QA-R1)
        self._latencias: deque[float] = deque(maxlen=500)
        self._lock = threading.Lock()

    # ---- Gestión manual (US-04) ------------------------------------------ #

    def crear(self, reserva: Reserva) -> Reserva:
        reserva.validar(TIPOS_RESERVA)
        if self.repo.buscar_por_codigo(reserva.usuario_id, reserva.proveedor, reserva.codigo_confirmacion):
            raise ErrorDominio("Ya existe una reserva con ese proveedor y código de confirmación")
        reserva = reserva.con(viaje_id=self.itinerarios.asignar_viaje(reserva), ultima_actualizacion=ahora_utc())
        self.repo.guardar(reserva)
        self._tras_cambio(reserva, "creada")
        return reserva

    def obtener(self, usuario_id: str, reserva_id: str) -> Reserva:
        reserva = self.repo.obtener(reserva_id)
        if reserva is None or reserva.usuario_id != usuario_id:
            raise ReservaNoEncontrada(reserva_id)
        return reserva

    def actualizar(self, usuario_id: str, reserva_id: str, cambios: dict[str, Any]) -> Reserva:
        actual = self.obtener(usuario_id, reserva_id)
        cambios = {k: v for k, v in cambios.items() if v is not None}
        if "estado" in cambios:
            cambios["estado"] = EstadoReserva(cambios["estado"])
        nueva = actual.con(**cambios, ultima_actualizacion=ahora_utc())
        if "estado" not in cambios and nueva.estado == EstadoReserva.CONFIRMADA and cambios:
            nueva = nueva.con(estado=EstadoReserva.MODIFICADA)
        nueva.validar(TIPOS_RESERVA)
        if "viaje_id" in cambios or "inicio" in cambios:
            nueva = nueva.con(viaje_id=self.itinerarios.asignar_viaje(
                nueva if "viaje_id" in cambios else nueva.con(viaje_id=None)))
        self.repo.guardar(nueva)
        if actual.viaje_id != nueva.viaje_id and actual.viaje_id:
            self.itinerarios.recalcular(actual.viaje_id)
        self._tras_cambio(nueva, "cancelada" if nueva.estado == EstadoReserva.CANCELADA else "actualizada")
        return nueva

    def eliminar(self, usuario_id: str, reserva_id: str) -> None:
        reserva = self.obtener(usuario_id, reserva_id)
        self.repo.eliminar(reserva_id)
        self._tras_cambio(reserva, "eliminada")

    # ---- Actualizaciones externas (US-01, US-03) ------------------------- #

    def aplicar_actualizacion_externa(self, usuario_id: str, act: ActualizacionCanonica,
                                      fuente: FuenteReserva) -> Reserva:
        existente = self.repo.buscar_por_codigo(usuario_id, act.proveedor, act.codigo_confirmacion)
        datos = dict(
            tipo=act.tipo, proveedor=act.proveedor, codigo_confirmacion=act.codigo_confirmacion,
            titulo=act.titulo, inicio=act.inicio, fin=act.fin, destino=act.destino, origen=act.origen,
            estado=act.estado, sincronizacion=EstadoSincronizacion.AL_DIA,
            ultima_actualizacion=ahora_utc(),
        )
        if existente is None:
            nueva = Reserva(id=nuevo_id(), usuario_id=usuario_id, fuente=fuente, detalles=act.detalles, **datos)
            nueva.validar(TIPOS_RESERVA)
            nueva = nueva.con(viaje_id=self.itinerarios.asignar_viaje(nueva))
            operacion = "creada"
        else:
            nueva = existente.con(detalles={**existente.detalles, **act.detalles}, **datos)
            nueva.validar(TIPOS_RESERVA)
            if existente.inicio != nueva.inicio:
                nueva = nueva.con(viaje_id=self.itinerarios.asignar_viaje(nueva.con(viaje_id=None)))
            if nueva == existente.con(ultima_actualizacion=nueva.ultima_actualizacion):
                return existente  # idempotente: nada cambió (entrega al menos una vez)
            operacion = "cancelada" if act.estado == EstadoReserva.CANCELADA else "actualizada"
        self.repo.guardar(nueva)
        if existente and existente.viaje_id and existente.viaje_id != nueva.viaje_id:
            self.itinerarios.recalcular(existente.viaje_id)
        if act.generado_en:
            with self._lock:
                self._latencias.append((ahora_utc() - act.generado_en).total_seconds())
        self._tras_cambio(nueva, operacion)
        return nueva

    def marcar_desactualizada(self, proveedor: str, codigo: str) -> list[Reserva]:
        """El proveedor no responde: se conserva la última información conocida (QA-D2)."""
        marcadas = []
        for r in self.repo.buscar_por_proveedor(proveedor, codigo):
            if r.sincronizacion != EstadoSincronizacion.DESACTUALIZADA:
                r = r.con(sincronizacion=EstadoSincronizacion.DESACTUALIZADA)
                self.repo.guardar(r)
                self.cache.invalidar_usuario(r.usuario_id)
            marcadas.append(r)
        return marcadas

    # ---- Comunes ---------------------------------------------------------- #

    def _tras_cambio(self, reserva: Reserva, operacion: str) -> None:
        if reserva.viaje_id:
            self.itinerarios.recalcular(reserva.viaje_id)
        # Política de invalidación inmediata (ADR-0004)
        self.cache.invalidar_usuario(reserva.usuario_id)
        ahora = ahora_utc()
        self.bus.publicar(eventos.RESERVA_CAMBIADA, {
            "reserva_id": reserva.id,
            "usuario_id": reserva.usuario_id,
            "operacion": operacion,
            "tipo": reserva.tipo,
            "proveedor": reserva.proveedor,
            "estado": reserva.estado.value,
            "fuente": reserva.fuente.value,
            "inicio": reserva.inicio.isoformat(),
            "ciudad_destino": reserva.destino.ciudad or reserva.destino.nombre,
            "pais_destino": reserva.destino.pais,
            "anticipacion_dias": max(0, (reserva.inicio - ahora).days),
            "momento": ahora.isoformat(),
        })

    def metricas_propagacion(self) -> dict[str, Any]:
        with self._lock:
            datos = sorted(self._latencias)
        if not datos:
            return {"muestras": 0}
        p95 = datos[min(len(datos) - 1, int(len(datos) * 0.95))]
        return {"muestras": len(datos), "max_s": round(datos[-1], 3), "p95_s": round(p95, 3),
                "objetivo_s": 300, "cumple": datos[-1] <= 300}


def reserva_a_dict(r: Reserva) -> dict[str, Any]:
    d = asdict(r)
    for k in ("inicio", "fin", "ultima_actualizacion"):
        d[k] = getattr(r, k).isoformat()
    for k in ("estado", "fuente", "sincronizacion"):
        d[k] = getattr(r, k).value
    return d
