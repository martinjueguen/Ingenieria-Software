"""Sistema de Recomendación: sugerencias y ciclo human-in-the-loop (ADD It.5).

Las lecturas devuelven sugerencias ya precalculadas (no se calcula en la
solicitud). Aceptar, rechazar o ajustar alimenta el aprendizaje de preferencias.
Función no crítica: se suspende bajo sobrecarga (`proteccion_carga.py`).
"""

from __future__ import annotations

from dataclasses import asdict
from itertools import groupby

from fastapi import APIRouter, HTTPException, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import (
    GrupoRecomendaciones,
    ParametrosRecomendacion,
    PreferenciasRecomendacion,
    Rechazo,
    RecomendacionDTO,
    ReservaDTO,
)
from trotamundos.integracion.puertos import ErrorProveedor
from trotamundos.recomendacion.modelo import Parametros
from trotamundos.recomendacion.servicio import RecomendacionNoDisponible

router = APIRouter(tags=["recomendaciones"])
_NO_DISPONIBLE = "La sugerencia ya no está disponible"


@router.get("/recomendaciones", response_model=list[GrupoRecomendaciones],
            summary="Sugerencias pendientes agrupadas por necesidad del viaje")
def listar(identidad: IdentidadDep, sistema: SistemaDep, viaje_id: str | None = None) -> list[GrupoRecomendaciones]:
    recs = sistema.recomendaciones.listar(identidad.usuario_id, viaje_id)
    grupos = []
    for grupo, items in groupby(recs, key=lambda r: r.grupo):
        items = sorted(items, key=lambda r: r.puntaje, reverse=True)
        r0 = items[0]
        grupos.append(GrupoRecomendaciones(
            grupo=grupo, viaje_id=r0.viaje_id, motivo=r0.motivo.value, descripcion=r0.descripcion,
            reserva_origen_id=r0.reserva_origen_id, sugerencias=[RecomendacionDTO.de(r) for r in items]))
    orden = {"disrupcion": 0, "transporte": 1, "alojamiento": 2}
    return sorted(grupos, key=lambda g: orden[g.motivo])


@router.post("/recomendaciones/{rec_id}/aceptar", response_model=ReservaDTO, status_code=status.HTTP_201_CREATED,
             summary="Aceptar una sugerencia: se reserva en el proveedor y se agrega al viaje")
def aceptar(rec_id: str, identidad: IdentidadDep, sistema: SistemaDep) -> ReservaDTO:
    try:
        reserva = sistema.recomendaciones.aceptar(identidad.usuario_id, identidad.email, rec_id)
    except RecomendacionNoDisponible:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NO_DISPONIBLE) from None
    except ErrorProveedor as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"El proveedor no responde: {e}",
                            headers={"Retry-After": "60"}) from e
    return ReservaDTO.de(reserva)


@router.post("/recomendaciones/{rec_id}/rechazar", status_code=status.HTTP_204_NO_CONTENT,
             summary="Rechazar una sugerencia (opcionalmente indicando el motivo)")
def rechazar(rec_id: str, datos: Rechazo, identidad: IdentidadDep, sistema: SistemaDep) -> None:
    try:
        sistema.recomendaciones.rechazar(identidad.usuario_id, rec_id, datos.motivo)
    except RecomendacionNoDisponible:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NO_DISPONIBLE) from None


@router.get("/recomendaciones/preferencias", response_model=PreferenciasRecomendacion,
            summary="Parámetros ajustados por el viajero y pesos aprendidos")
def preferencias(identidad: IdentidadDep, sistema: SistemaDep) -> PreferenciasRecomendacion:
    parametros, pesos = sistema.recomendaciones.preferencias(identidad.usuario_id)
    return PreferenciasRecomendacion(parametros=ParametrosRecomendacion(**asdict(parametros)), pesos=pesos)


@router.put("/recomendaciones/preferencias", response_model=PreferenciasRecomendacion,
            summary="Ajustar parámetros (las sugerencias se recalculan en segundo plano)")
def ajustar(datos: ParametrosRecomendacion, identidad: IdentidadDep, sistema: SistemaDep) -> PreferenciasRecomendacion:
    sistema.recomendaciones.ajustar(identidad.usuario_id, Parametros(**datos.model_dump()))
    return preferencias(identidad, sistema)


@router.post("/recomendaciones/actualizar", status_code=status.HTTP_202_ACCEPTED,
             summary="Pedir que se recalculen mis sugerencias")
def actualizar(identidad: IdentidadDep, sistema: SistemaDep) -> dict:
    return {"evento_id": sistema.recomendaciones.solicitar(identidad.usuario_id, "usuario")}
