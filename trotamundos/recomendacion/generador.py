"""Detección de necesidades del viaje (ADD It.5).

Analiza el itinerario y detecta para qué conviene sugerir alternativas:
- Disrupción: una reserva cancelada que no tiene reemplazo.
- Ruta (transporte): el viajero llega a una ciudad pero su siguiente tramo sale de otra.
- Alojamiento: el viajero pasa la noche en una ciudad sin hotel reservado.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from trotamundos.dominio.modelo import EstadoReserva, Reserva, Viaje
from trotamundos.recomendacion.modelo import Motivo, Necesidad

TIPOS_TRANSPORTE = ("tren", "vuelo", "autobus")
ESTANCIA_MINIMA = timedelta(hours=10)


def _es_traslado(r: Reserva) -> bool:
    return bool(r.origen and r.origen.ciudad and r.destino.ciudad and r.origen.ciudad != r.destino.ciudad)


def _alternativas(tipo: str) -> tuple[str, ...]:
    return TIPOS_TRANSPORTE if tipo in TIPOS_TRANSPORTE else (tipo,)


def detectar_necesidades(viaje: Viaje, reservas: list[Reserva], momento: datetime) -> list[Necesidad]:
    vigentes = [r for r in reservas if r.estado != EstadoReserva.CANCELADA]
    necesidades: list[Necesidad] = []

    # 1. Disrupciones: reservas canceladas sin reemplazo
    for r in reservas:
        if r.estado != EstadoReserva.CANCELADA or r.fin < momento:
            continue
        reemplazo = any(
            v.tipo in _alternativas(r.tipo) and v.destino.ciudad == r.destino.ciudad
            and abs((v.inicio - r.inicio).total_seconds()) < 36 * 3600
            for v in vigentes
        )
        if reemplazo:
            continue
        if _es_traslado(r):
            desde, hasta = max(momento, r.inicio - timedelta(hours=12)), r.fin + timedelta(hours=36)
        else:
            desde, hasta = max(momento, r.inicio), r.fin
        necesidades.append(Necesidad(
            viaje.id, Motivo.DISRUPCION, _alternativas(r.tipo), r.destino.ciudad, desde, hasta,
            f"Alternativas a «{r.titulo}» (cancelada)",
            ciudad_origen=r.origen.ciudad if r.origen and _es_traslado(r) else None, reserva_origen_id=r.id,
        ))

    traslados = sorted((r for r in vigentes if _es_traslado(r)), key=lambda r: r.inicio)
    hoteles = [r for r in vigentes if r.tipo == "hotel"]

    for actual, siguiente in zip(traslados, traslados[1:]):
        ciudad = actual.destino.ciudad
        if siguiente.inicio < momento:
            continue
        # 2. Ruta: llega a una ciudad y el siguiente tramo sale de otra
        if siguiente.origen and siguiente.origen.ciudad != ciudad:
            desde = max(momento, actual.fin + timedelta(hours=2))
            hasta = siguiente.inicio - timedelta(hours=3)
            if hasta > desde:
                necesidades.append(Necesidad(
                    viaje.id, Motivo.TRANSPORTE, TIPOS_TRANSPORTE, siguiente.origen.ciudad, desde, hasta,
                    f"Cómo ir de {ciudad} a {siguiente.origen.ciudad}", ciudad_origen=ciudad,
                ))
        # 3. Alojamiento: noche(s) en la ciudad sin hotel
        if siguiente.inicio - actual.fin < ESTANCIA_MINIMA:
            continue
        cubierto = any(
            h.destino.ciudad == ciudad and h.inicio.date() <= actual.fin.date() + timedelta(days=1)
            and h.fin.date() >= siguiente.inicio.date() - timedelta(days=1)
            for h in hoteles
        )
        if not cubierto:
            necesidades.append(Necesidad(
                viaje.id, Motivo.ALOJAMIENTO, ("hotel",), ciudad, max(momento, actual.fin), siguiente.inicio,
                f"Dónde dormir en {ciudad}",
            ))
    return necesidades
