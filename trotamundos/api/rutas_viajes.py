"""Panel de viajes (US-05, QA-R2) e itinerarios compartidos (QA-S1).

El API Controller deriva las lecturas al Gestor de caché (ADR-0004); solo en
un fallo de caché se consulta al Servicio de Itinerarios y a la base.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import CambioViaje, ViajeDTO
from trotamundos.seguridad.autorizacion import AccesoDenegado, Permiso

router = APIRouter(tags=["viajes"])


@router.get("/viajes", response_model=list[ViajeDTO], summary="Panel: viajes con sus reservas")
def panel(identidad: IdentidadDep, sistema: SistemaDep, response: Response,
          incluir_archivados: bool = False) -> list[dict]:
    vista = "panel-historial" if incluir_archivados else "panel"

    def calcular() -> list[dict]:
        return [ViajeDTO.de(it).model_dump(mode="json")
                for it in sistema.itinerarios.panel(identidad.usuario_id, incluir_archivados)]

    datos, acierto = sistema.cache.obtener_o_calcular(sistema.cache.clave(identidad.usuario_id, vista), calcular)
    response.headers["X-Cache"] = "HIT" if acierto else "MISS"
    return datos


@router.get("/viajes/compartidos", response_model=list[ViajeDTO], summary="Viajes que otros compartieron conmigo")
def compartidos(identidad: IdentidadDep, sistema: SistemaDep) -> list[ViajeDTO]:
    resultado = []
    for viaje_id in sistema.repo_comparticiones.viajes_compartidos_con(identidad.email):
        try:
            viaje = sistema.control_acceso.autorizar(identidad, viaje_id, Permiso.LECTURA)
        except AccesoDenegado:
            continue
        resultado.append(ViajeDTO.de(sistema.itinerarios.itinerario(viaje), es_propietario=False))
    return resultado


@router.get("/viajes/{viaje_id}", response_model=ViajeDTO, summary="Itinerario de un viaje (propio o compartido)",
            responses={404: {"description": "Inexistente o sin autorización (no se distingue)"}})
def obtener(viaje_id: str, identidad: IdentidadDep, sistema: SistemaDep) -> ViajeDTO:
    try:
        viaje = sistema.control_acceso.autorizar(identidad, viaje_id, Permiso.LECTURA)
    except AccesoDenegado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Viaje no encontrado") from None
    return ViajeDTO.de(sistema.itinerarios.itinerario(viaje), es_propietario=viaje.usuario_id == identidad.usuario_id)


@router.patch("/viajes/{viaje_id}", response_model=ViajeDTO, summary="Renombrar un viaje")
def renombrar(viaje_id: str, cambio: CambioViaje, identidad: IdentidadDep, sistema: SistemaDep) -> ViajeDTO:
    try:
        viaje = sistema.control_acceso.autorizar(identidad, viaje_id, Permiso.ESCRITURA)
    except AccesoDenegado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Viaje no encontrado") from None
    viaje = sistema.itinerarios.renombrar(viaje, cambio.nombre)
    sistema.cache.invalidar_usuario(identidad.usuario_id)
    return ViajeDTO.de(sistema.itinerarios.itinerario(viaje))
