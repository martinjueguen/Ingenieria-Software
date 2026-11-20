"""Analítica de datos para el equipo de monetización (US-07, ADR-0014).

Consultas pesadas contra el almacén OLAP segregado, nunca contra la base
operacional. Funciones no críticas: se suspenden bajo sobrecarga (QA-E1).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from trotamundos.api.dependencias import SistemaDep, requiere_rol
from trotamundos.seguridad.autenticacion import Identidad

router = APIRouter(tags=["analitica"])
Analista = Annotated[Identidad, Depends(requiere_rol("analista"))]


@router.get("/analitica/destinos", summary="Tendencias de destinos")
def destinos(_: Analista, sistema: SistemaDep, limite: int = 10) -> list[dict]:
    return sistema.almacen.tendencias_destinos(limite)


@router.get("/analitica/cancelaciones", summary="Tasa de cancelación por proveedor")
def cancelaciones(_: Analista, sistema: SistemaDep) -> list[dict]:
    return sistema.almacen.cancelaciones_por_proveedor()


@router.get("/analitica/estacionalidad", summary="Reservas por mes y tipo")
def estacionalidad(_: Analista, sistema: SistemaDep) -> list[dict]:
    return sistema.almacen.estacionalidad()


@router.get("/analitica/recomendaciones", summary="Efectividad del sistema de recomendación (tasa de aceptación)")
def recomendaciones(_: Analista, sistema: SistemaDep) -> list[dict]:
    return sistema.almacen.efectividad_recomendaciones()
