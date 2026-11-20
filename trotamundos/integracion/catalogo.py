"""Adaptador del catálogo de ofertas de un proveedor → formato canónico `Oferta`.

ADD It.5 (Sistema de Recomendación). Mismo patrón Adaptador que los
proveedores de reservas: el motor de recomendación solo conoce `Oferta`; un
proveedor nuevo con catálogo se incorpora registrando su adaptador.
"""

from __future__ import annotations

from typing import Any

from trotamundos.dominio.modelo import Ubicacion, a_utc
from trotamundos.integracion.puertos import AdaptadorCatalogo, BusquedaOfertas, ErrorProveedor, Oferta
from trotamundos.integracion.simuladores import SistemaCaido
from trotamundos.integracion.simuladores_catalogo import SimuladorCatalogo


def _ubicacion(d: dict[str, Any] | None) -> Ubicacion | None:
    if not d:
        return None
    return Ubicacion(d["name"], d.get("city", ""), d.get("country", ""), d.get("lat"), d.get("lon"))


class AdaptadorCatalogoEstandar(AdaptadorCatalogo):
    def __init__(self, api: SimuladorCatalogo) -> None:
        self.api = api
        self.codigo = api.codigo
        self.tipo_reserva = api.tipo

    def buscar(self, b: BusquedaOfertas) -> list[Oferta]:
        try:
            crudas = self.api.buscar(b.tipo, b.ciudad_destino, b.desde.isoformat(), b.hasta.isoformat(), b.ciudad_origen)
        except SistemaCaido as e:
            raise ErrorProveedor(str(e)) from e
        return [self._traducir(o) for o in crudas]

    def reservar(self, oferta_id: str, titular: str) -> str:
        try:
            return self.api.reservar(oferta_id, titular)
        except SistemaCaido as e:
            raise ErrorProveedor(str(e)) from e
        except KeyError as e:
            raise ErrorProveedor(f"{self.codigo}: la oferta ya no está disponible") from e

    def _traducir(self, o: dict[str, Any]) -> Oferta:
        atributos: dict[str, Any] = {}
        if "stars" in o:
            atributos["estrellas"] = o["stars"]
            atributos["comodidad"] = o["stars"] / 5
        if "comfort" in o:
            atributos["comodidad"] = o["comfort"]
        if "distanceKm" in o:
            atributos["distancia_centro_km"] = o["distanceKm"]
        if "durationMin" in o:
            atributos["duracion_min"] = o["durationMin"]
        if "number" in o:
            atributos["numero"] = o["number"]
        return Oferta(
            id=o["offerId"], proveedor=self.codigo, tipo=o["kind"], titulo=o["name"],
            inicio=a_utc(o["start"]), fin=a_utc(o["end"]), destino=_ubicacion(o["to"]),  # type: ignore[arg-type]
            origen=_ubicacion(o.get("from")), precio=float(o["priceUsd"]), atributos=atributos,
        )
