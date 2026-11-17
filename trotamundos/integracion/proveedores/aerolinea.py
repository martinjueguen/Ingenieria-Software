"""Adaptador de aerolíneas (formato tipo intercambio IATA) → Modelo Canónico."""

from __future__ import annotations

from typing import Any

from trotamundos.dominio.modelo import EstadoReserva, Ubicacion, a_utc
from trotamundos.integracion.proveedores.base import AdaptadorProveedorBase
from trotamundos.integracion.puertos import ActualizacionCanonica

_ESTADOS = {"SCHEDULED": EstadoReserva.CONFIRMADA, "CHANGED": EstadoReserva.MODIFICADA,
            "DELAYED": EstadoReserva.MODIFICADA, "CANCELLED": EstadoReserva.CANCELADA}


def _aeropuerto(d: dict[str, Any]) -> Ubicacion:
    return Ubicacion(f"Aeropuerto {d['iata']}", d.get("city", ""), d.get("country", ""), d.get("lat"), d.get("lon"))


class AdaptadorAerolinea(AdaptadorProveedorBase):
    tipo_reserva = "vuelo"

    def _traducir(self, c: dict[str, Any]) -> ActualizacionCanonica:
        vuelo = c["flight"]
        detalles = {"numero_vuelo": vuelo["number"]}
        if c.get("gate"):
            detalles["puerta"] = c["gate"]
        return ActualizacionCanonica(
            proveedor=self.codigo,
            tipo=self.tipo_reserva,
            codigo_confirmacion=c["pnr"],
            estado=_ESTADOS[c["status"]],
            titulo=f"Vuelo {vuelo['number']} {vuelo['from']['iata']} → {vuelo['to']['iata']}",
            inicio=a_utc(vuelo["departure"]),
            fin=a_utc(vuelo["arrival"]),
            origen=_aeropuerto(vuelo["from"]),
            destino=_aeropuerto(vuelo["to"]),
            detalles=detalles,
            generado_en=a_utc(c["generated_at"]) if c.get("generated_at") else None,
        )
