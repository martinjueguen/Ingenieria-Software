"""Compartición segura de itinerarios (QA-S1, ADR-0015) y redes sociales (QA-I2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import Comparticion, Publicacion
from trotamundos.integracion.registro import ProveedorNoRegistrado
from trotamundos.seguridad.autorizacion import AccesoDenegado, Permiso

router = APIRouter(tags=["compartir"])


def _propio(viaje_id: str, identidad, sistema):  # type: ignore[no-untyped-def]
    try:
        return sistema.control_acceso.autorizar(identidad, viaje_id, Permiso.ESCRITURA)
    except AccesoDenegado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Viaje no encontrado") from None


@router.get("/viajes/{viaje_id}/comparticiones", summary="Personas designadas (ACL del itinerario)")
def listar(viaje_id: str, identidad: IdentidadDep, sistema: SistemaDep) -> list[dict]:
    _propio(viaje_id, identidad, sistema)
    return sistema.repo_comparticiones.de_viaje(viaje_id)


@router.post("/viajes/{viaje_id}/comparticiones", status_code=status.HTTP_201_CREATED,
             summary="Designar a una persona con permiso de solo lectura")
def agregar(viaje_id: str, datos: Comparticion, identidad: IdentidadDep, sistema: SistemaDep) -> list[dict]:
    _propio(viaje_id, identidad, sistema)
    sistema.repo_comparticiones.agregar(viaje_id, datos.email, Permiso.LECTURA)
    sistema.auditoria.registrar(identidad.email, "viaje.compartir", f"viaje:{viaje_id}", "concedido", datos.email)
    return sistema.repo_comparticiones.de_viaje(viaje_id)


@router.delete("/viajes/{viaje_id}/comparticiones/{email}", summary="Quitar a una persona designada")
def quitar(viaje_id: str, email: str, identidad: IdentidadDep, sistema: SistemaDep) -> list[dict]:
    _propio(viaje_id, identidad, sistema)
    sistema.repo_comparticiones.quitar(viaje_id, email)
    sistema.auditoria.registrar(identidad.email, "viaje.dejar_de_compartir", f"viaje:{viaje_id}", "concedido", email)
    return sistema.repo_comparticiones.de_viaje(viaje_id)


@router.post("/viajes/{viaje_id}/publicar", summary="Publicar en una red social un enlace protegido al itinerario")
def publicar(viaje_id: str, datos: Publicacion, request: Request, identidad: IdentidadDep,
             sistema: SistemaDep) -> dict:
    _propio(viaje_id, identidad, sistema)
    try:
        red = sistema.adaptadores.redes.obtener(datos.red)
    except ProveedorNoRegistrado as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
    enlace = str(request.base_url) + f"#/viaje/{viaje_id}"
    publicacion = red.publicar(identidad.usuario_id, datos.mensaje, enlace)
    return {"publicacion": publicacion, "enlace": enlace,
            "nota": "Solo las personas designadas podrán ver el itinerario al abrir el enlace."}
