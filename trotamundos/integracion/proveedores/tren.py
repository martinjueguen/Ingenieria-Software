"""Adaptador de operadores ferroviarios → Modelo Canónico.

Demuestra QA-M1 / QA-I1: el medio "tren" se incorporó registrando un tipo en
`dominio/modelo.py` y agregando este adaptador, sin modificar vuelos, hoteles
ni autos.
"""

from __future__ import annotations

from typing import Any

from trotamundos.dominio.modelo import EstadoReserva, Ubicacion, a_utc
from trotamundos.integracion.proveedores.base import AdaptadorProveedorBase
from trotamundos.integracion.puertos import ActualizacionCanonica

_ESTADOS = {"confirmado": EstadoReserva.CONFIRMADA, "modificado": EstadoReserva.MODIFICADA,
            "anulado": EstadoReserva.CANCELADA}


def _estacion(d: dict[str, Any]) -> Ubicacion:
    return Ubicacion(f"Estación {d['estacion']}", d.get("ciudad", ""), d.get("pais", ""), d.get("lat"), d.get("lon"))


class AdaptadorTren(AdaptadorProveedorBase):
    tipo_reserva = "tren"

    def _traducir(self, c: dict[str, Any]) -> ActualizacionCanonica:
        return ActualizacionCanonica(
            proveedor=self.codigo,
            tipo=self.tipo_reserva,
            codigo_confirmacion=c["localizador"],
            estado=_ESTADOS[c["estado"]],
            titulo=f"Tren {c['tren']} {c['salida']['estacion']} → {c['llegada']['estacion']}",
            inicio=a_utc(c["salida"]["hora"]),
            fin=a_utc(c["llegada"]["hora"]),
            origen=_estacion(c["salida"]),
            destino=_estacion(c["llegada"]),
            detalles={"numero_tren": c["tren"], "coche": c.get("coche", ""), "asiento": c.get("asiento", "")},
            generado_en=a_utc(c["generado_en"]) if c.get("generado_en") else None,
        )
