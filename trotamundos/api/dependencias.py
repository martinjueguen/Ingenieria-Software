"""Dependencias comunes de la API: acceso al sistema y autenticación por token."""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from trotamundos.app import Sistema
from trotamundos.seguridad.autenticacion import ErrorAutenticacion, Identidad

_bearer = HTTPBearer(auto_error=False)


def obtener_sistema(request: Request) -> Sistema:
    return request.app.state.sistema


SistemaDep = Annotated[Sistema, Depends(obtener_sistema)]


def identidad_actual(
    sistema: SistemaDep,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Identidad:
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token de acceso",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        return sistema.emisor_tokens.verificar(credenciales.credentials)
    except ErrorAutenticacion as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e), headers={"WWW-Authenticate": "Bearer"}) from e


IdentidadDep = Annotated[Identidad, Depends(identidad_actual)]


def requiere_rol(*roles: str) -> Callable[[Identidad], Identidad]:
    def verificar(identidad: IdentidadDep) -> Identidad:
        if identidad.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requiere rol: {', '.join(roles)}")
        return identidad
    return verificar
