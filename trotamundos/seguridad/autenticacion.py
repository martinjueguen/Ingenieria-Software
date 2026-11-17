"""Autenticación — módulo "Seguridad y control de acceso" (Capa 2).

ADD It.1 (ADR-0001): verificar la identidad del usuario antes de acceder a las
funcionalidades protegidas. Los tokens de sesión son autocontenidos y firmados
con HMAC, de modo que cualquier instancia de la API puede validarlos sin estado
compartido (servicios *stateless* para autoescalado, ADR-0013).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

ITERACIONES = 120_000
DURACION_TOKEN_SEGUNDOS = 8 * 3600


class ErrorAutenticacion(Exception):
    pass


def hashear_clave(clave: str) -> str:
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), ITERACIONES)
    return f"pbkdf2${sal}${digest.hex()}"


def verificar_clave(clave: str, almacenado: str) -> bool:
    try:
        _, sal, esperado = almacenado.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), ITERACIONES)
    return hmac.compare_digest(digest.hex(), esperado)


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _de_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


@dataclass(frozen=True)
class Identidad:
    usuario_id: str
    email: str
    rol: str


class EmisorTokens:
    def __init__(self, secreto: str) -> None:
        self._secreto = secreto.encode()

    def emitir(self, identidad: Identidad, duracion: int = DURACION_TOKEN_SEGUNDOS) -> str:
        carga = {
            "sub": identidad.usuario_id,
            "email": identidad.email,
            "rol": identidad.rol,
            "exp": int(time.time()) + duracion,
        }
        cuerpo = _b64(json.dumps(carga, separators=(",", ":")).encode())
        firma = _b64(hmac.new(self._secreto, cuerpo.encode(), hashlib.sha256).digest())
        return f"{cuerpo}.{firma}"

    def verificar(self, token: str) -> Identidad:
        try:
            cuerpo, firma = token.split(".")
        except ValueError:
            raise ErrorAutenticacion("Token mal formado") from None
        esperada = _b64(hmac.new(self._secreto, cuerpo.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(firma, esperada):
            raise ErrorAutenticacion("Firma inválida")
        carga = json.loads(_de_b64(cuerpo))
        if carga["exp"] < time.time():
            raise ErrorAutenticacion("Token vencido")
        return Identidad(carga["sub"], carga["email"], carga["rol"])
