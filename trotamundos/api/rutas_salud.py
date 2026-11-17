"""Salud de la región (heartbeat del GeoDNS, ADR-0012) y observabilidad para operaciones."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from trotamundos.api.dependencias import SistemaDep, requiere_rol
from trotamundos.seguridad.autenticacion import Identidad

router = APIRouter(tags=["operaciones"])
Operador = Annotated[Identidad, Depends(requiere_rol("operaciones"))]


@router.get("/salud", summary="Heartbeat de la región (lo consulta el Global Traffic Manager)")
def salud(sistema: SistemaDep) -> dict:
    sistema.bd.consultar_uno("SELECT 1")
    return {"estado": "ok", "region": sistema.config.region}


@router.post("/region/promover", include_in_schema=False)
def promover(sistema: SistemaDep, x_clave_infra: Annotated[str | None, Header()] = None) -> dict:
    """Llamado por el Global Traffic Manager al conmutar: la región pasiva pasa a activa."""
    if not x_clave_infra or not hmac.compare_digest(x_clave_infra, sistema.config.secreto_sesion):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo la infraestructura puede promover una región")
    sistema.cache.invalidar_todo()
    if not sistema.workers.estado()["activos"]:
        sistema.iniciar_procesos_fondo()
    sistema.notificaciones.notificar("operaciones", "region.promovida",
                                     f"La región {sistema.config.region} pasó a ser la región activa")
    return {"region": sistema.config.region, "estado": "activa"}


@router.get("/operaciones/estado", summary="Métricas de los atributos de calidad")
def estado(_: Operador, sistema: SistemaDep, request: Request) -> dict:
    return {
        "region": sistema.config.region,
        "latencia_web": request.app.state.carga.metricas(),
        "propagacion_actualizaciones": sistema.reservas.metricas_propagacion(),
        "cache": sistema.cache.metricas(),
        "bus": sistema.bus.metricas(),
        "workers": sistema.workers.estado(),
        "planificador": sistema.planificador.estado(),
        "proveedores_caidos": sistema.sincronizador.caidos,
        "replicacion": sistema.replicador.estado() if sistema.replicador else None,
        "hechos_analiticos": sistema.almacen.total_hechos(),
    }


@router.get("/operaciones/notificaciones", summary="Notificaciones a operaciones")
def notificaciones(_: Operador, sistema: SistemaDep) -> list[dict]:
    return sistema.notificaciones.de("operaciones")


@router.get("/operaciones/auditoria", summary="Registro de auditoría de accesos")
def auditoria(_: Operador, sistema: SistemaDep, recurso: str = "", resultado: str | None = None) -> list[dict]:
    return sistema.auditoria.consultar(recurso, resultado)


@router.get("/operaciones/mensajes-muertos", summary="Mensajes que agotaron reintentos")
def muertos(_: Operador, sistema: SistemaDep) -> list[dict]:
    return sistema.bus.mensajes_muertos()
