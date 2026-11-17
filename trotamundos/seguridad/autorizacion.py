"""Controlador de autorización de itinerarios — Capa 2.

ADD It.4, Concepto 4 (ADR-0015), QA-S1. Tácticas *Authorize actors* y
*Limit access*: antes de entregar un viaje se verifica que el actor
autenticado sea el propietario o figure en la Lista de Control de Acceso del
itinerario. Todo acceso (concedido o denegado) queda en la auditoría.
Para evitar enumeración de identificadores, un acceso denegado se informa
igual que un recurso inexistente.
"""

from __future__ import annotations

from enum import StrEnum

from trotamundos.datos.repositorios import RepositorioComparticiones, RepositorioViajes
from trotamundos.dominio.modelo import Viaje
from trotamundos.seguridad.auditoria import RegistroAuditoria
from trotamundos.seguridad.autenticacion import Identidad


class Permiso(StrEnum):
    LECTURA = "lectura"
    ESCRITURA = "escritura"  # solo el propietario


class AccesoDenegado(Exception):
    pass


class ControlAccesoItinerarios:
    def __init__(self, viajes: RepositorioViajes, comparticiones: RepositorioComparticiones,
                 auditoria: RegistroAuditoria) -> None:
        self.viajes = viajes
        self.comparticiones = comparticiones
        self.auditoria = auditoria

    def autorizar(self, actor: Identidad, viaje_id: str, permiso: Permiso) -> Viaje:
        viaje = self.viajes.obtener(viaje_id)
        recurso = f"viaje:{viaje_id}"
        if viaje is None:
            self.auditoria.registrar(actor.email, f"viaje.{permiso}", recurso, "denegado", "inexistente")
            raise AccesoDenegado(viaje_id)
        if viaje.usuario_id == actor.usuario_id:
            return viaje  # el propietario no genera ruido en la auditoría
        concedido = self.comparticiones.permiso(viaje_id, actor.email)
        if permiso == Permiso.LECTURA and concedido == Permiso.LECTURA:
            self.auditoria.registrar(actor.email, "viaje.lectura", recurso, "concedido", "persona designada")
            return viaje
        self.auditoria.registrar(
            actor.email, f"viaje.{permiso}", recurso, "denegado",
            "no figura en la lista de personas designadas",
        )
        raise AccesoDenegado(viaje_id)
