"""Conector de agencia preferida — adaptador de salida.

ADD It.3, Concepto 1 y decisión 5 (ADR-0011), US-06: recibe la solicitud de
asistencia del viajero, empaqueta el itinerario, las reservas afectadas y sus
códigos de confirmación en el formato estándar de contingencia y lo transmite
al canal de soporte de la agencia elegida por el usuario.
"""

from __future__ import annotations

from typing import Any

from trotamundos.gestion_viajes.servicio_itinerarios import ItinerarioConsolidado
from trotamundos.integracion.puertos import AdaptadorAgencia, ErrorProveedor
from trotamundos.integracion.simuladores import SimuladorAgencia, SistemaCaido


class AdaptadorAgenciaEstandar(AdaptadorAgencia):
    def __init__(self, api: SimuladorAgencia) -> None:
        self.codigo = api.codigo
        self.nombre = api.nombre
        self.api = api

    def enviar_solicitud(self, contexto: dict[str, Any]) -> str:
        try:
            return self.api.abrir_caso(contexto)
        except SistemaCaido as e:
            raise ErrorProveedor(str(e)) from e


def contexto_de_contingencia(viajero: dict[str, Any], itinerario: ItinerarioConsolidado,
                             reservas_afectadas: list[str], motivo: str, descripcion: str) -> dict[str, Any]:
    """Formato estándar de contingencia (independiente de cada agencia)."""
    v = itinerario.viaje
    return {
        "version": "1.0",
        "viajero": {"nombre": viajero["nombre"], "email": viajero["email"], "idioma": viajero["idioma"]},
        "motivo": motivo,
        "descripcion": descripcion,
        "viaje": {"nombre": v.nombre, "destino": v.destino, "inicio": v.inicio.isoformat(),
                  "fin": v.fin.isoformat()},
        "reservas": [
            {
                "afectada": r.id in reservas_afectadas,
                "tipo": r.tipo,
                "proveedor": r.proveedor,
                "codigo_confirmacion": r.codigo_confirmacion,
                "titulo": r.titulo,
                "inicio": r.inicio.isoformat(),
                "fin": r.fin.isoformat(),
                "estado": r.estado.value,
            }
            for r in itinerario.reservas
        ],
    }
