"""Adaptador de arrendadoras de autos → Modelo Canónico."""

from __future__ import annotations

from typing import Any

from trotamundos.dominio.modelo import EstadoReserva, Ubicacion, a_utc
from trotamundos.integracion.proveedores.base import AdaptadorProveedorBase
from trotamundos.integracion.puertos import ActualizacionCanonica

_ESTADOS = {"CONFIRMED": EstadoReserva.CONFIRMADA, "UPDATED": EstadoReserva.MODIFICADA,
            "CANCELLED": EstadoReserva.CANCELADA}


def _lugar(d: dict[str, Any]) -> Ubicacion:
    return Ubicacion(d["location"], d.get("city", ""), d.get("country", ""), d.get("lat"), d.get("lon"))


class AdaptadorArrendadora(AdaptadorProveedorBase):
    tipo_reserva = "auto"

    def _traducir(self, c: dict[str, Any]) -> ActualizacionCanonica:
        return ActualizacionCanonica(
            proveedor=self.codigo,
            tipo=self.tipo_reserva,
            codigo_confirmacion=c["reservationNumber"],
            estado=_ESTADOS[c["status"]],
            titulo=f"Auto {c.get('vehicle', '')}".strip(),
            inicio=a_utc(c["pickup"]["datetime"]),
            fin=a_utc(c["dropoff"]["datetime"]),
            origen=_lugar(c["pickup"]),
            destino=_lugar(c["pickup"]),
            detalles={"vehiculo": c.get("vehicle", ""), "devolucion": c["dropoff"]["location"]},
            generado_en=a_utc(c["generated_at"]) if c.get("generated_at") else None,
        )
