"""Modelo del Sistema de Recomendación (ADD It.5)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from trotamundos.integracion.puertos import Oferta

# Características con las que se puntúa cada oferta (todas normalizadas a 0..1).
CARACTERISTICAS = ("precio", "comodidad", "cercania", "popularidad", "afinidad")
PESOS_INICIALES = {"precio": 1.0, "comodidad": 1.0, "cercania": 1.0, "popularidad": 0.5, "afinidad": 0.5}
SUGERENCIAS_POR_GRUPO = 3


class Motivo(StrEnum):
    ALOJAMIENTO = "alojamiento"   # falta alojamiento en una ciudad del viaje
    TRANSPORTE = "transporte"     # falta un tramo entre dos ciudades (ruta)
    DISRUPCION = "disrupcion"     # una reserva fue cancelada y no tiene reemplazo


class EstadoRecomendacion(StrEnum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    DESCARTADA = "descartada"     # el usuario eligió otra del mismo grupo


@dataclass(frozen=True)
class Parametros:
    """Parámetros que el viajero ajusta explícitamente (human-in-the-loop)."""

    presupuesto_max: float | None = None       # USD por reserva
    distancia_max_km: float | None = None      # alojamiento: distancia máxima al centro
    categoria_minima: int | None = None        # alojamiento: estrellas mínimas
    transporte_preferido: str | None = None    # tren | vuelo | autobus

    def admite(self, oferta: Oferta) -> bool:
        if self.presupuesto_max is not None and oferta.precio > self.presupuesto_max:
            return False
        dist = oferta.atributos.get("distancia_centro_km")
        if self.distancia_max_km is not None and dist is not None and dist > self.distancia_max_km:
            return False
        estrellas = oferta.atributos.get("estrellas")
        if self.categoria_minima is not None and estrellas is not None and estrellas < self.categoria_minima:
            return False
        return True


@dataclass(frozen=True)
class Necesidad:
    """Algo que le falta (o se le cayó) al viaje y para lo cual se buscan alternativas."""

    viaje_id: str
    motivo: Motivo
    tipos: tuple[str, ...]
    ciudad_destino: str
    desde: datetime
    hasta: datetime
    descripcion: str
    ciudad_origen: str | None = None
    reserva_origen_id: str | None = None

    @property
    def grupo(self) -> str:
        return f"{self.viaje_id}:{self.motivo}:{self.ciudad_origen or ''}>{self.ciudad_destino}:{self.desde.date()}"


@dataclass(frozen=True)
class Recomendacion:
    id: str
    usuario_id: str
    viaje_id: str
    grupo: str
    motivo: Motivo
    descripcion: str
    oferta: Oferta
    puntaje: float
    caracteristicas: dict[str, float]
    estado: EstadoRecomendacion = EstadoRecomendacion.PENDIENTE
    reserva_origen_id: str | None = None
    creada_en: datetime | None = None
    explicacion: list[str] = field(default_factory=list)


def id_recomendacion(usuario_id: str, grupo: str, oferta_id: str) -> str:
    """Estable entre recálculos: la misma oferta para la misma necesidad conserva su id."""
    return hashlib.sha1(f"{usuario_id}|{grupo}|{oferta_id}".encode()).hexdigest()[:20]


def promedio(vectores: list[dict[str, float]]) -> dict[str, float]:
    if not vectores:
        return {c: 0.5 for c in CARACTERISTICAS}
    return {c: sum(v.get(c, 0.5) for v in vectores) / len(vectores) for c in CARACTERISTICAS}

