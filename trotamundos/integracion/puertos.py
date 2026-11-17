"""Puertos (interfaces) de la capa de integración con servicios externos.

ADD It.3, Concepto 1 (ADR-0007). Tácticas *Use an intermediary* y
*Encapsulate*: el núcleo solo conoce estas interfaces y el Modelo Canónico.
Agregar un proveedor = implementar un adaptador y registrarlo
(`integracion/registro.py`), sin modificar los demás módulos (QA-I1, QA-I2).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from trotamundos.dominio.modelo import EstadoReserva, Ubicacion


class ErrorProveedor(Exception):
    """Falla de comunicación con un sistema externo (QA-D2: *Exception detection*)."""


@dataclass(frozen=True)
class ActualizacionCanonica:
    """Estado de una reserva externa traducido al modelo canónico."""

    proveedor: str
    tipo: str
    codigo_confirmacion: str
    estado: EstadoReserva
    titulo: str
    inicio: datetime
    fin: datetime
    destino: Ubicacion
    origen: Ubicacion | None = None
    detalles: dict[str, Any] = field(default_factory=dict)
    # Momento en que la fuente generó el cambio: permite medir QA-R1 (≤ 5 min)
    generado_en: datetime | None = None


class AdaptadorProveedorViajes(ABC):
    """Aerolíneas, hoteles, arrendadoras, trenes, autobuses (CON-1, US-03)."""

    codigo: str
    tipo_reserva: str

    @abstractmethod
    def consultar_reserva(self, codigo_confirmacion: str) -> ActualizacionCanonica:
        """Consulta la API del proveedor. Lanza ErrorProveedor si no responde."""

    @abstractmethod
    def traducir_notificacion(self, carga: dict[str, Any]) -> ActualizacionCanonica:
        """Traduce una notificación (webhook) en formato propietario al modelo canónico."""

    @abstractmethod
    def disponible(self) -> bool:
        """Chequeo de salud (ping/echo) de la API del proveedor."""


@dataclass(frozen=True)
class EncabezadoCorreo:
    """Solo lo necesario para decidir por whitelist: no incluye asunto ni cuerpo."""

    id: str
    remitente: str
    recibido_en: datetime


@dataclass(frozen=True)
class CorreoCompleto:
    id: str
    remitente: str
    asunto: str
    cuerpo: str
    recibido_en: datetime


class AdaptadorCorreo(ABC):
    """Proveedores de correo (Gmail, Outlook, ...) con OAuth estándar (QA-I2, QA-S2)."""

    codigo: str
    ALCANCE_SOLO_LECTURA = "correo.lectura"

    @abstractmethod
    def autorizar(self, direccion: str, alcances: list[str]) -> tuple[str, list[str]]:
        """Flujo OAuth: devuelve (token_acceso, alcances_otorgados)."""

    @abstractmethod
    def revocar(self, token: str) -> None: ...

    @abstractmethod
    def listar_encabezados(self, token: str, direccion: str) -> list[EncabezadoCorreo]: ...

    @abstractmethod
    def obtener_correo(self, token: str, direccion: str, mensaje_id: str) -> CorreoCompleto: ...


class AdaptadorAgencia(ABC):
    """Adaptador de salida hacia agencias de viaje preferidas (US-06, ADR-0011)."""

    codigo: str
    nombre: str

    @abstractmethod
    def enviar_solicitud(self, contexto: dict[str, Any]) -> str:
        """Transmite el contexto estructurado del viaje; devuelve el número de caso."""


class AdaptadorRedSocial(ABC):
    """Redes sociales para compartir itinerarios (QA-I2)."""

    codigo: str

    @abstractmethod
    def publicar(self, token_usuario: str, mensaje: str, enlace: str) -> str: ...
