"""Endpoint de resumen ligero para móvil — Trip Summary (ADR-0005, QA-R3, QA-U1).

Devuelve solo el próximo tramo (con coordenadas para el GPS) y la cantidad de
viajes activos: *Bound response sizes* / *Reduce computational overhead*.
Los detalles se piden bajo demanda a `/viajes/{id}`.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import ResumenMovil, TramoResumido

router = APIRouter(tags=["movil"])


@router.get("/movil/resumen", response_model=ResumenMovil, summary="Resumen del próximo tramo (primer despliegue)")
def resumen(identidad: IdentidadDep, sistema: SistemaDep, response: Response) -> dict:
    def calcular() -> dict:
        par = sistema.itinerarios.proximo_tramo(identidad.usuario_id)
        activos = len(sistema.repo_viajes.de_usuario(identidad.usuario_id))
        if par is None:
            return ResumenMovil(proximo=None, viajes_activos=activos).model_dump(mode="json")
        viaje, r = par
        d = r.detalles
        detalle = d.get("puerta") and f"Puerta {d['puerta']}" or d.get("asiento") and f"Asiento {d['asiento']}" \
            or d.get("habitacion") and f"Habitación {d['habitacion']}" or None
        punto = r.origen if r.tipo in ("vuelo", "tren", "autobus") and r.origen else r.destino
        tramo = TramoResumido(
            viaje_id=viaje.id, viaje=viaje.nombre, reserva_id=r.id, tipo=r.tipo, titulo=r.titulo,
            codigo=r.codigo_confirmacion, inicio=r.inicio, estado=r.estado.value,
            sincronizacion=r.sincronizacion.value, destino=punto.nombre, lat=punto.lat, lon=punto.lon,
            detalle=detalle,
        )
        return ResumenMovil(proximo=tramo, viajes_activos=activos).model_dump(mode="json")

    datos, acierto = sistema.cache.obtener_o_calcular(sistema.cache.clave(identidad.usuario_id, "resumen"), calcular)
    response.headers["X-Cache"] = "HIT" if acierto else "MISS"
    return datos
