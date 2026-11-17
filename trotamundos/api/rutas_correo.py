"""Vinculación de casilla, whitelist y escaneo de correo (US-01, US-02, QA-S2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import EntradaWhitelist, VinculoCorreo
from trotamundos.integracion.registro import ProveedorNoRegistrado
from trotamundos.seguridad.gestor_tokens import AlcanceNoPermitido

router = APIRouter(tags=["correo"])


@router.post("/correo/vincular", status_code=status.HTTP_201_CREATED,
             summary="Vincular casilla vía OAuth con alcance de solo lectura")
def vincular(datos: VinculoCorreo, identidad: IdentidadDep, sistema: SistemaDep) -> dict:
    try:
        return sistema.gestor_tokens.vincular(identidad.usuario_id, identidad.email, datos.proveedor, datos.direccion)
    except ProveedorNoRegistrado as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
    except AlcanceNoPermitido as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e)) from e


@router.get("/correo/cuenta", summary="Estado de la casilla vinculada (nunca expone el token)")
def cuenta(identidad: IdentidadDep, sistema: SistemaDep) -> dict:
    c = sistema.repo_cuentas.obtener(identidad.usuario_id)
    if not c:
        return {"vinculada": False}
    return {"vinculada": True, "proveedor": c["proveedor"], "direccion": c["direccion"],
            "alcances": c["alcances"].split(), "estado": c["estado"], "vinculada_en": c["vinculada_en"],
            "ultimo_sondeo": c["ultimo_sondeo"], "correos": sistema.repo_cuentas.estadisticas(identidad.usuario_id)}


@router.delete("/correo/cuenta", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular y revocar el acceso")
def desvincular(identidad: IdentidadDep, sistema: SistemaDep) -> None:
    sistema.gestor_tokens.revocar(identidad.usuario_id, "solicitado por el usuario")


@router.post("/correo/sondear", summary="Sondear la casilla ahora (encola los correos autorizados)")
def sondear(identidad: IdentidadDep, sistema: SistemaDep) -> dict:
    return sistema.escaneo.sondear(identidad.usuario_id)


@router.get("/correo/whitelist", summary="Remitentes autorizados")
def listar_whitelist(identidad: IdentidadDep, sistema: SistemaDep) -> list[str]:
    return sistema.repo_whitelist.listar(identidad.usuario_id)


@router.post("/correo/whitelist", status_code=status.HTTP_201_CREATED, summary="Agregar remitente o dominio")
def agregar_whitelist(entrada: EntradaWhitelist, identidad: IdentidadDep, sistema: SistemaDep) -> list[str]:
    sistema.repo_whitelist.agregar(identidad.usuario_id, entrada.remitente)
    return sistema.repo_whitelist.listar(identidad.usuario_id)


@router.delete("/correo/whitelist/{remitente}", summary="Quitar remitente o dominio")
def quitar_whitelist(remitente: str, identidad: IdentidadDep, sistema: SistemaDep) -> list[str]:
    sistema.repo_whitelist.quitar(identidad.usuario_id, remitente)
    return sistema.repo_whitelist.listar(identidad.usuario_id)
