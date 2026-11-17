"""Modelo de dominio y Modelo Canónico de Reserva.

Implementa:
- Modelo Canónico de Reserva (ADD It.3, Concepto 1 / ADR-0007): todos los
  adaptadores traducen a `Reserva`; el núcleo no conoce formatos externos.
- Registro de tipos de transporte (ADD It.2 Concepto 1 / QA-M1): agregar un
  medio de transporte nuevo es registrar un `TipoReserva`, sin modificar los
  tipos existentes.
- Viaje y sus estados de ciclo de vida (US-05 / ADR-0006).

Todas las fechas son `datetime` con zona UTC (ADR-0016).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def a_utc(valor: datetime | str) -> datetime:
    """Normaliza cualquier fecha a UTC (ADR-0016). Fechas sin zona se asumen UTC."""
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def nuevo_id() -> str:
    return uuid.uuid4().hex


class ErrorDominio(ValueError):
    """Violación de una regla de negocio."""


# --------------------------------------------------------------------------- #
# Tipos de reserva (extensibles)                                              #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TipoReserva:
    codigo: str
    nombre: str
    campos_requeridos: tuple[str, ...] = ()
    es_transporte: bool = True

    def validar_detalles(self, detalles: dict[str, Any]) -> None:
        faltantes = [c for c in self.campos_requeridos if not detalles.get(c)]
        if faltantes:
            raise ErrorDominio(
                f"La reserva de tipo '{self.codigo}' requiere los campos: {', '.join(faltantes)}"
            )


class RegistroTiposReserva:
    """Registro de medios de transporte/servicios soportados (QA-M1)."""

    def __init__(self) -> None:
        self._tipos: dict[str, TipoReserva] = {}

    def registrar(self, tipo: TipoReserva) -> None:
        if tipo.codigo in self._tipos:
            raise ErrorDominio(f"El tipo '{tipo.codigo}' ya está registrado")
        self._tipos[tipo.codigo] = tipo

    def obtener(self, codigo: str) -> TipoReserva:
        try:
            return self._tipos[codigo]
        except KeyError:
            raise ErrorDominio(f"Tipo de reserva desconocido: '{codigo}'") from None

    def codigos(self) -> list[str]:
        return list(self._tipos)


TIPOS_RESERVA = RegistroTiposReserva()
TIPOS_RESERVA.registrar(TipoReserva("vuelo", "Vuelo", ("numero_vuelo",)))
TIPOS_RESERVA.registrar(TipoReserva("hotel", "Hotel", (), es_transporte=False))
TIPOS_RESERVA.registrar(TipoReserva("auto", "Alquiler de auto", ()))
# Trenes y autobuses se incorporaron sin tocar los tipos anteriores (QA-M1).
TIPOS_RESERVA.registrar(TipoReserva("tren", "Tren", ("numero_tren",)))
TIPOS_RESERVA.registrar(TipoReserva("autobus", "Autobús", ()))


# --------------------------------------------------------------------------- #
# Modelo canónico                                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Ubicacion:
    nombre: str
    ciudad: str = ""
    pais: str = ""
    lat: float | None = None
    lon: float | None = None


class EstadoReserva(StrEnum):
    CONFIRMADA = "confirmada"
    MODIFICADA = "modificada"
    CANCELADA = "cancelada"


class FuenteReserva(StrEnum):
    MANUAL = "manual"
    CORREO = "correo"
    PROVEEDOR = "proveedor"


class EstadoSincronizacion(StrEnum):
    AL_DIA = "al_dia"
    # El proveedor no respondió: se muestra la última información conocida (QA-D2)
    DESACTUALIZADA = "desactualizada"


@dataclass(frozen=True)
class Reserva:
    """Modelo Canónico de Reserva (ADR-0007)."""

    id: str
    usuario_id: str
    tipo: str
    proveedor: str
    codigo_confirmacion: str
    titulo: str
    inicio: datetime
    fin: datetime
    destino: Ubicacion
    origen: Ubicacion | None = None
    estado: EstadoReserva = EstadoReserva.CONFIRMADA
    detalles: dict[str, Any] = field(default_factory=dict)
    fuente: FuenteReserva = FuenteReserva.MANUAL
    viaje_id: str | None = None
    sincronizacion: EstadoSincronizacion = EstadoSincronizacion.AL_DIA
    ultima_actualizacion: datetime = field(default_factory=ahora_utc)

    def validar(self, tipos: RegistroTiposReserva = TIPOS_RESERVA) -> None:
        tipos.obtener(self.tipo).validar_detalles(self.detalles)
        if self.fin < self.inicio:
            raise ErrorDominio("La fecha de fin no puede ser anterior a la de inicio")
        if not self.codigo_confirmacion.strip():
            raise ErrorDominio("El código de confirmación es obligatorio")

    def con(self, **cambios: Any) -> "Reserva":
        return replace(self, **cambios)


class EstadoViaje(StrEnum):
    PLANIFICADO = "planificado"
    EN_CURSO = "en_curso"
    FINALIZADO = "finalizado"
    ARCHIVADO = "archivado"


@dataclass(frozen=True)
class Viaje:
    id: str
    usuario_id: str
    nombre: str
    destino: str
    inicio: datetime
    fin: datetime
    estado: EstadoViaje = EstadoViaje.PLANIFICADO

    def con(self, **cambios: Any) -> "Viaje":
        return replace(self, **cambios)


def estado_por_fechas(inicio: datetime, fin: datetime, momento: datetime | None = None) -> EstadoViaje:
    momento = momento or ahora_utc()
    if momento < inicio:
        return EstadoViaje.PLANIFICADO
    if momento <= fin:
        return EstadoViaje.EN_CURSO
    return EstadoViaje.FINALIZADO
