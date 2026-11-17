"""Autenticación y perfil del usuario (Seguridad y control de acceso; preferencias i18n QA-U2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import CambioPerfil, Credenciales, Perfil, Sesion
from trotamundos.seguridad.autenticacion import Identidad, verificar_clave

router = APIRouter(tags=["autenticacion"])


def _perfil(fila: dict) -> Perfil:
    return Perfil(**{k: fila[k] for k in Perfil.model_fields})


@router.post("/auth/login", response_model=Sesion, summary="Iniciar sesión")
def login(datos: Credenciales, sistema: SistemaDep) -> Sesion:
    usuario = sistema.repo_usuarios.por_email(datos.email)
    if not usuario or not verificar_clave(datos.clave, usuario["hash_clave"]):
        sistema.auditoria.registrar(datos.email.lower(), "auth.login", "sesion", "denegado", "credenciales inválidas")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
    token = sistema.emisor_tokens.emitir(Identidad(usuario["id"], usuario["email"], usuario["rol"]))
    return Sesion(token=token, usuario=_perfil(usuario))


@router.get("/usuarios/yo", response_model=Perfil, summary="Perfil y preferencias regionales")
def perfil(identidad: IdentidadDep, sistema: SistemaDep) -> Perfil:
    return _perfil(sistema.repo_usuarios.por_id(identidad.usuario_id))  # type: ignore[arg-type]


@router.patch("/usuarios/yo", response_model=Perfil, summary="Cambiar idioma, zona horaria, moneda o agencia")
def cambiar_perfil(cambios: CambioPerfil, identidad: IdentidadDep, sistema: SistemaDep) -> Perfil:
    datos = cambios.model_dump(exclude_none=True)
    if "agencia_preferida" in datos and datos["agencia_preferida"] not in sistema.adaptadores.agencias.codigos():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Agencia desconocida")
    if datos:
        sistema.repo_usuarios.actualizar(identidad.usuario_id, **datos)
    return _perfil(sistema.repo_usuarios.por_id(identidad.usuario_id))  # type: ignore[arg-type]


@router.get("/notificaciones", summary="Notificaciones del usuario (p. ej. revocación de acceso al correo)")
def notificaciones(identidad: IdentidadDep, sistema: SistemaDep) -> list[dict]:
    return sistema.notificaciones.de(f"usuario:{identidad.usuario_id}")
