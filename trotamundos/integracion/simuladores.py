"""Simuladores de los sistemas externos del diagrama de contexto.

NO forman parte de Trotamundos: reemplazan a Gmail, a las APIs de aerolíneas,
hoteles, arrendadoras y trenes, a la agencia de viajes y a la red social, para
que el prototipo pueda demostrarse sin credenciales reales. Cada uno habla su
propio formato "propietario", distinto del Modelo Canónico, para evidenciar el
trabajo de los adaptadores (ADR-0007). Permiten inyectar fallas (QA-D2) y
emitir cambios (QA-R1).
"""

from __future__ import annotations

import copy
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from trotamundos.dominio.modelo import ahora_utc


class SistemaCaido(ConnectionError):
    pass


@dataclass
class SimuladorProveedorViajes:
    """API de un proveedor de viajes (formato propietario por proveedor)."""

    codigo: str
    reservas: dict[str, dict[str, Any]] = field(default_factory=dict)
    caido: bool = False
    llamadas: int = 0
    # Webhook hacia Trotamundos: lo conecta la app al receptor de notificaciones.
    webhook: Callable[[str, dict[str, Any]], None] | None = None

    def ping(self) -> bool:
        return not self.caido

    def consultar(self, codigo_confirmacion: str) -> dict[str, Any]:
        self.llamadas += 1
        if self.caido:
            raise SistemaCaido(f"{self.codigo}: 503 Service Unavailable")
        if codigo_confirmacion not in self.reservas:
            raise KeyError(codigo_confirmacion)
        return copy.deepcopy(self.reservas[codigo_confirmacion])

    def emitir_cambio(self, codigo_confirmacion: str, cambios: dict[str, Any]) -> dict[str, Any]:
        """El proveedor modifica una reserva y notifica por webhook (si está disponible)."""
        registro = self.reservas[codigo_confirmacion]
        _fusionar(registro, cambios)
        registro["generated_at"] = ahora_utc().isoformat()
        if self.webhook and not self.caido:
            self.webhook(self.codigo, copy.deepcopy(registro))
        return copy.deepcopy(registro)


def _fusionar(destino: dict[str, Any], cambios: dict[str, Any]) -> None:
    for k, v in cambios.items():
        if isinstance(v, dict) and isinstance(destino.get(k), dict):
            _fusionar(destino[k], v)
        else:
            destino[k] = v


@dataclass
class _Mensaje:
    id: str
    remitente: str
    asunto: str
    cuerpo: str
    recibido_en: datetime


class SimuladorCorreo:
    """Servidor de correo con OAuth (estilo Gmail API)."""

    ALCANCES_VALIDOS = {"correo.lectura", "correo.escritura", "correo.borrado"}

    def __init__(self, codigo: str = "gmail") -> None:
        self.codigo = codigo
        self.casillas: dict[str, list[_Mensaje]] = {}
        self.tokens: dict[str, tuple[str, set[str]]] = {}
        self.caido = False
        self.lecturas_de_cuerpo: list[str] = []  # para verificar privacidad (US-02)
        # Señal de seguridad hacia Trotamundos: (direccion, origen)
        self.reportar_uso: Callable[[str, str], None] | None = None
        self.otorgar_alcances_extra = False  # simula un proveedor que otorga de más
        self._lock = threading.Lock()

    def entregar(self, direccion: str, remitente: str, asunto: str, cuerpo: str) -> str:
        mensaje = _Mensaje(secrets.token_hex(8), remitente.lower(), asunto, cuerpo, ahora_utc())
        with self._lock:
            self.casillas.setdefault(direccion.lower(), []).append(mensaje)
        return mensaje.id

    def autorizar(self, direccion: str, alcances: list[str]) -> tuple[str, list[str]]:
        otorgados = set(alcances) & self.ALCANCES_VALIDOS
        if self.otorgar_alcances_extra:
            otorgados |= {"correo.escritura"}
        token = secrets.token_urlsafe(24)
        self.tokens[token] = (direccion.lower(), otorgados)
        self.casillas.setdefault(direccion.lower(), [])
        return token, sorted(otorgados)

    def revocar(self, token: str) -> None:
        self.tokens.pop(token, None)

    def _verificar(self, token: str, direccion: str, alcance: str, origen: str) -> None:
        if self.caido:
            raise SistemaCaido(f"{self.codigo}: no disponible")
        datos = self.tokens.get(token)
        if not datos or datos[0] != direccion.lower() or alcance not in datos[1]:
            raise PermissionError("401 token inválido, revocado o sin alcance")
        if self.reportar_uso:
            self.reportar_uso(direccion.lower(), origen)
            if token not in self.tokens:  # revocado como consecuencia del reporte
                raise PermissionError("401 token revocado")

    def listar(self, token: str, direccion: str, origen: str) -> list[dict[str, Any]]:
        self._verificar(token, direccion, "correo.lectura", origen)
        return [{"id": m.id, "from": m.remitente, "date": m.recibido_en.isoformat()}
                for m in self.casillas.get(direccion.lower(), [])]

    def leer(self, token: str, direccion: str, mensaje_id: str, origen: str) -> dict[str, Any]:
        self._verificar(token, direccion, "correo.lectura", origen)
        for m in self.casillas.get(direccion.lower(), []):
            if m.id == mensaje_id:
                self.lecturas_de_cuerpo.append(m.id)
                return {"id": m.id, "from": m.remitente, "subject": m.asunto, "body": m.cuerpo,
                        "date": m.recibido_en.isoformat()}
        raise KeyError(mensaje_id)


class SimuladorAgencia:
    def __init__(self, codigo: str, nombre: str) -> None:
        self.codigo = codigo
        self.nombre = nombre
        self.casos: dict[str, dict[str, Any]] = {}
        self.caido = False

    def abrir_caso(self, documento: dict[str, Any]) -> str:
        if self.caido:
            raise SistemaCaido(f"{self.codigo}: no disponible")
        numero = f"{self.codigo.upper()}-{len(self.casos) + 1:05d}"
        self.casos[numero] = documento
        return numero


class SimuladorRedSocial:
    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        self.publicaciones: list[dict[str, str]] = []

    def publicar(self, token: str, texto: str, enlace: str) -> str:
        pid = f"{self.codigo}-{len(self.publicaciones) + 1}"
        self.publicaciones.append({"id": pid, "texto": texto, "enlace": enlace})
        return pid
