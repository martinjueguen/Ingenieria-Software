"""Entrada de notificaciones de proveedores (webhooks) — US-03, QA-R1.

El webhook no procesa en el acto: encola la carga y responde 202 (*Queue
requests*, ADR-0008). Un worker la traduce con el adaptador del proveedor.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.integracion.registro import ProveedorNoRegistrado

router = APIRouter(tags=["proveedores"])


@router.post("/proveedores/{proveedor}/webhook", status_code=status.HTTP_202_ACCEPTED,
             summary="Notificación de cambio de un proveedor (formato propietario)")
def webhook(proveedor: str, sistema: SistemaDep, carga: dict[str, Any] = Body(...)) -> dict:
    try:
        evento_id = sistema.sincronizador.recibir_webhook(proveedor, carga)
    except ProveedorNoRegistrado as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    return {"aceptado": True, "evento_id": evento_id}


@router.get("/proveedores", summary="Proveedores integrados y su disponibilidad")
def proveedores(_: IdentidadDep, sistema: SistemaDep) -> list[dict]:
    return [{"codigo": a.codigo, "tipo": a.tipo_reserva,
             "estado": "caido" if a.codigo in sistema.sincronizador.caidos else "disponible",
             "caido_desde": sistema.sincronizador.caidos.get(a.codigo)}
            for a in sistema.adaptadores.proveedores.todos()]
