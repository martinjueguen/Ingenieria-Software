"""Cifrado en reposo de tokens de acceso al correo.

ADD It.3, Concepto 3 (ADR-0009), QA-S2. Táctica *Encrypt data*: los tokens
OAuth de las casillas vinculadas nunca se guardan en claro. Se usa Fernet
(AES-128-CBC + HMAC-SHA256) de la librería `cryptography`.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet


class CifradorTokens:
    def __init__(self, clave: str, secreto_respaldo: str) -> None:
        if not clave:
            # Solo para desarrollo: derivar una clave estable del secreto de la app.
            # En producción la clave proviene de un gestor de secretos (KMS).
            clave = base64.urlsafe_b64encode(
                hashlib.sha256(f"cifrado:{secreto_respaldo}".encode()).digest()
            ).decode()
        self._fernet = Fernet(clave.encode() if isinstance(clave, str) else clave)

    def cifrar(self, texto: str) -> bytes:
        return self._fernet.encrypt(texto.encode())

    def descifrar(self, cifrado: bytes) -> str:
        return self._fernet.decrypt(cifrado).decode()
