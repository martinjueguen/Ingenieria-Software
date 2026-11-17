"""Servicio de Itinerarios — submódulo de "Gestión de viajes y reservas".

ADD It.2, Concepto 1 (ADR-0003), US-05: agrupa las reservas dentro de viajes
según fechas y destinos, y construye el consolidado del itinerario para las
vistas del usuario (panel web y resumen móvil).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from trotamundos.datos.repositorios import RepositorioReservas, RepositorioViajes
from trotamundos.dominio.modelo import (
    ErrorDominio,
    EstadoReserva,
    EstadoViaje,
    Reserva,
    Viaje,
    ahora_utc,
    estado_por_fechas,
    nuevo_id,
)

# Dos reservas separadas por menos de este margen pertenecen al mismo viaje.
MARGEN_AGRUPACION = timedelta(days=2)
# Un traslado que sale de una ciudad del viaje dentro de este plazo es su regreso/continuación.
MARGEN_REGRESO = timedelta(days=15)


@dataclass(frozen=True)
class ItinerarioConsolidado:
    viaje: Viaje
    reservas: list[Reserva]


class ServicioItinerarios:
    def __init__(self, viajes: RepositorioViajes, reservas: RepositorioReservas) -> None:
        self.viajes = viajes
        self.reservas = reservas

    def asignar_viaje(self, reserva: Reserva) -> str:
        """Devuelve el id del viaje al que pertenece la reserva (creándolo si hace falta)."""
        if reserva.viaje_id:
            viaje = self.viajes.obtener(reserva.viaje_id)
            if viaje is None or viaje.usuario_id != reserva.usuario_id:
                raise ErrorDominio("El viaje indicado no existe")
            return viaje.id
        viajes = self.viajes.de_usuario(reserva.usuario_id)
        # Regla 1 (fechas): el tramo cae dentro del viaje o a menos del margen.
        for viaje in viajes:
            if viaje.inicio - MARGEN_AGRUPACION <= reserva.inicio <= viaje.fin + MARGEN_AGRUPACION:
                return viaje.id
        # Regla 2 (destinos y secuencia): un traslado que parte desde una ciudad visitada en el
        # viaje, poco después de su fin, es el tramo de continuación o regreso de ese viaje.
        if reserva.origen and reserva.origen.ciudad:
            for viaje in viajes:
                ciudades = {r.destino.ciudad for r in self.reservas.de_viaje(viaje.id)}
                if (reserva.origen.ciudad in ciudades
                        and viaje.fin <= reserva.inicio <= viaje.fin + MARGEN_REGRESO):
                    return viaje.id
        ciudad = reserva.destino.ciudad or reserva.destino.nombre
        viaje = Viaje(
            id=nuevo_id(),
            usuario_id=reserva.usuario_id,
            nombre=f"Viaje a {ciudad}",
            destino=ciudad,
            inicio=reserva.inicio,
            fin=reserva.fin,
            estado=estado_por_fechas(reserva.inicio, reserva.fin),
        )
        self.viajes.guardar(viaje)
        return viaje.id

    def recalcular(self, viaje_id: str) -> Viaje | None:
        """Ajusta el rango del viaje a sus tramos; elimina el viaje si quedó sin tramos."""
        viaje = self.viajes.obtener(viaje_id)
        if viaje is None:
            return None
        tramos = self.reservas.de_viaje(viaje_id)
        if not tramos:
            self.viajes.eliminar(viaje_id)
            return None
        vigentes = [r for r in tramos if r.estado != EstadoReserva.CANCELADA] or tramos
        inicio = min(r.inicio for r in vigentes)
        fin = max(r.fin for r in vigentes)
        estado = viaje.estado if viaje.estado == EstadoViaje.ARCHIVADO else estado_por_fechas(inicio, fin)
        actualizado = viaje.con(inicio=inicio, fin=fin, estado=estado)
        self.viajes.guardar(actualizado)
        return actualizado

    def renombrar(self, viaje: Viaje, nombre: str) -> Viaje:
        actualizado = viaje.con(nombre=nombre)
        self.viajes.guardar(actualizado)
        return actualizado

    # ---- Consolidados para las vistas ------------------------------------- #

    def panel(self, usuario_id: str, incluir_archivados: bool = False) -> list[ItinerarioConsolidado]:
        return [
            ItinerarioConsolidado(v, self.reservas.de_viaje(v.id))
            for v in self.viajes.de_usuario(usuario_id, incluir_archivados)
        ]

    def itinerario(self, viaje: Viaje) -> ItinerarioConsolidado:
        return ItinerarioConsolidado(viaje, self.reservas.de_viaje(viaje.id))

    def proximo_tramo(self, usuario_id: str, momento: datetime | None = None) -> tuple[Viaje, Reserva] | None:
        """Próximo tramo no cancelado (o en curso) del usuario: base del resumen móvil."""
        momento = momento or ahora_utc()
        candidatos: list[tuple[Viaje, Reserva]] = []
        for viaje in self.viajes.de_usuario(usuario_id):
            for r in self.reservas.de_viaje(viaje.id):
                if r.estado != EstadoReserva.CANCELADA and r.fin >= momento:
                    candidatos.append((viaje, r))
        return min(candidatos, key=lambda par: par[1].inicio) if candidatos else None
