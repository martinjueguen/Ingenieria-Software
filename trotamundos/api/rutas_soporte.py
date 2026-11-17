"""Resolución de problemas con la agencia preferida (US-06, ADR-0011)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import SolicitudSoporte
from trotamundos.integracion.agencia import contexto_de_contingencia
from trotamundos.integracion.puertos import ErrorProveedor
from trotamundos.seguridad.autorizacion import AccesoDenegado, Permiso

router = APIRouter(tags=["soporte"])


@router.get("/agencias", summary="Agencias de viaje integradas")
def agencias(_: IdentidadDep, sistema: SistemaDep) -> list[dict]:
    return [{"codigo": a.codigo, "nombre": a.nombre} for a in sistema.adaptadores.agencias.todos()]


@router.post("/viajes/{viaje_id}/soporte", status_code=status.HTTP_201_CREATED,
             summary="Enviar el contexto del viaje al soporte de la agencia preferida")
def solicitar_soporte(viaje_id: str, solicitud: SolicitudSoporte, identidad: IdentidadDep,
                      sistema: SistemaDep) -> dict:
    try:
        viaje = sistema.control_acceso.autorizar(identidad, viaje_id, Permiso.ESCRITURA)
    except AccesoDenegado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Viaje no encontrado") from None
    usuario = sistema.repo_usuarios.por_id(identidad.usuario_id)
    if not usuario or not usuario["agencia_preferida"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Primero elegí tu agencia de viajes preferida en tu perfil")
    adaptador = sistema.adaptadores.agencias.obtener(usuario["agencia_preferida"])
    contexto = contexto_de_contingencia(usuario, sistema.itinerarios.itinerario(viaje),
                                        solicitud.reservas_afectadas, solicitud.motivo, solicitud.descripcion)
    try:
        caso = adaptador.enviar_solicitud(contexto)
    except ErrorProveedor as e:
        sistema.notificaciones.notificar("operaciones", "agencia.caida", f"{adaptador.codigo}: {e}")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "La agencia no responde; intentá en unos minutos",
                            headers={"Retry-After": "60"}) from e
    return {"agencia": adaptador.nombre, "caso": caso, "reservas_enviadas": len(contexto["reservas"])}
