"""Controles de simulación de los sistemas externos (solo para la demo).

NO es parte de la API del producto: permite, desde la interfaz de demo,
provocar los estímulos de los escenarios de calidad (un proveedor emite un
cambio, un proveedor se cae, llega un correo, un atacante usa un token robado,
ejecutar ya una tarea programada). Se excluye del contrato `specs/openapi.json`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel

from trotamundos.api.dependencias import SistemaDep

router = APIRouter(prefix="/simulacion", tags=["simulacion"], include_in_schema=False)


class CambioProveedor(BaseModel):
    codigo_confirmacion: str
    cambios: dict[str, Any]


class Correo(BaseModel):
    direccion: str
    remitente: str
    asunto: str
    cuerpo: str


class UsoToken(BaseModel):
    direccion: str
    origen: str = "203.0.113.66 (desconocido)"


@router.post("/proveedores/{codigo}/cambio")
def cambio_proveedor(codigo: str, datos: CambioProveedor, sistema: SistemaDep) -> dict:
    sim = sistema.externos.proveedores.get(codigo)
    if not sim or datos.codigo_confirmacion not in sim.reservas:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor o reserva inexistente")
    return sim.emitir_cambio(datos.codigo_confirmacion, datos.cambios)


@router.post("/proveedores/{codigo}/caida")
def caida_proveedor(codigo: str, sistema: SistemaDep, caido: bool = Body(..., embed=True)) -> dict:
    sim = sistema.externos.proveedores.get(codigo)
    if not sim:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor inexistente")
    sim.caido = caido
    return {"proveedor": codigo, "caido": caido}


@router.get("/proveedores")
def reservas_en_proveedores(sistema: SistemaDep) -> dict:
    return {c: {"caido": s.caido, "reservas": list(s.reservas)} for c, s in sistema.externos.proveedores.items()}


@router.post("/correo/entregar")
def entregar_correo(datos: Correo, sistema: SistemaDep) -> dict:
    return {"mensaje_id": sistema.externos.correo.entregar(datos.direccion, datos.remitente, datos.asunto, datos.cuerpo)}


@router.post("/correo/uso-token")
def uso_token_robado(datos: UsoToken, sistema: SistemaDep) -> dict:
    """Un atacante usa el token robado de la casilla desde otro origen (QA-S2)."""
    correo = sistema.externos.correo
    token = next((t for t, (d, _) in correo.tokens.items() if d == datos.direccion.lower()), None)
    if token is None:
        return {"resultado": "sin token vigente para esa casilla"}
    try:
        correo.listar(token, datos.direccion, datos.origen)
        return {"resultado": "acceso concedido (no detectado)"}
    except PermissionError as e:
        return {"resultado": f"acceso bloqueado: {e}"}


@router.get("/agencias/{codigo}/casos")
def casos_agencia(codigo: str, sistema: SistemaDep) -> dict:
    sim = sistema.externos.agencias.get(codigo)
    if not sim:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agencia inexistente")
    return sim.casos


@router.get("/red-social")
def publicaciones(sistema: SistemaDep) -> list[dict]:
    return sistema.externos.red_social.publicaciones


@router.post("/tareas/{nombre}")
def ejecutar_tarea(nombre: str, sistema: SistemaDep) -> dict:
    if nombre not in sistema.planificador.tareas:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea inexistente")
    return {"tarea": nombre, "resultado": sistema.planificador.ejecutar_ahora(nombre)}


@router.post("/procesar-colas")
def procesar_colas(sistema: SistemaDep) -> dict:
    return {"procesados": sistema.bus.procesar_pendientes(maximo=1000)}
