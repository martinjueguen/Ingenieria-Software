"""Adaptador de cadenas hoteleras → Modelo Canónico."""

from __future__ import annotations

from typing import Any

from trotamundos.dominio.modelo import EstadoReserva, Ubicacion, a_utc
from trotamundos.integracion.proveedores.base import AdaptadorProveedorBase
from trotamundos.integracion.puertos import ActualizacionCanonica

_ESTADOS = {"BOOKED": EstadoReserva.CONFIRMADA, "MODIFIED": EstadoReserva.MODIFICADA,
            "CANCELED": EstadoReserva.CANCELADA}


class AdaptadorHotel(AdaptadorProveedorBase):
    tipo_reserva = "hotel"

    def _traducir(self, c: dict[str, Any]) -> ActualizacionCanonica:
        h = c["hotel"]
        detalles = {k: c[k] for k in ("room",) if c.get(k)}
        return ActualizacionCanonica(
            proveedor=self.codigo,
            tipo=self.tipo_reserva,
            codigo_confirmacion=c["confirmation_no"],
            estado=_ESTADOS[c["state"]],
            titulo=h["name"],
            inicio=a_utc(c["check_in"]),
            fin=a_utc(c["check_out"]),
            destino=Ubicacion(h["name"], h.get("city", ""), h.get("country", ""), h.get("lat"), h.get("lon")),
            detalles={"habitacion": detalles["room"]} if detalles else {},
            generado_en=a_utc(c["generated_at"]) if c.get("generated_at") else None,
        )
