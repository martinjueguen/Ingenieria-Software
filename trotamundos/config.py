"""Configuración del prototipo (parametrizable por variables de entorno).

Todos los parámetros que cambian entre regiones o entornos viven acá para que
el núcleo no se modifique al desplegar una nueva región (QA-U2, ADR-0016).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _env(nombre: str, defecto: str) -> str:
    return os.environ.get(f"TROTAMUNDOS_{nombre}", defecto)


@dataclass
class Config:
    # Región de despliegue (ADR-0012)
    region: str = field(default_factory=lambda: _env("REGION", "primaria"))
    # Base de datos operacional OLTP (ADR-0001, ADR-0003)
    ruta_bd: str = field(default_factory=lambda: _env("BD", str(RAIZ / "var" / "oltp-primaria.db")))
    # Réplica en la región secundaria; vacío = sin replicación (ADR-0012)
    ruta_replica: str = field(default_factory=lambda: _env("REPLICA", ""))
    # Almacenamiento persistente del bus de eventos (ADR-0008)
    ruta_bus: str = field(default_factory=lambda: _env("BUS", str(RAIZ / "var" / "bus-primaria.db")))
    # Almacén analítico OLAP segregado (ADR-0014)
    ruta_olap: str = field(default_factory=lambda: _env("OLAP", str(RAIZ / "var" / "olap.db")))
    # Clave para firmar tokens de sesión (servicios sin estado, ADR-0013)
    secreto_sesion: str = field(default_factory=lambda: _env("SECRETO", "secreto-solo-para-desarrollo"))
    # Clave Fernet para cifrar tokens de correo en reposo (ADR-0009)
    clave_cifrado: str = field(default_factory=lambda: _env("CLAVE_CIFRADO", ""))
    # Caché de itinerarios (ADR-0004)
    ttl_cache_segundos: int = field(default_factory=lambda: int(_env("TTL_CACHE", "300")))
    # Workers (ADR-0008, ADR-0013)
    workers_min: int = field(default_factory=lambda: int(_env("WORKERS_MIN", "2")))
    workers_max: int = field(default_factory=lambda: int(_env("WORKERS_MAX", "8")))
    mensajes_por_worker: int = field(default_factory=lambda: int(_env("MENSAJES_POR_WORKER", "20")))
    # Reintentos (ADR-0010)
    max_intentos: int = field(default_factory=lambda: int(_env("MAX_INTENTOS", "6")))
    backoff_base_segundos: float = field(default_factory=lambda: float(_env("BACKOFF_BASE", "1.0")))
    # Planificador: períodos en segundos (ADR-0006, ADR-0008, ADR-0014)
    periodo_sondeo_correo: float = field(default_factory=lambda: float(_env("PERIODO_CORREO", "60")))
    periodo_sondeo_proveedores: float = field(default_factory=lambda: float(_env("PERIODO_PROVEEDORES", "120")))
    # Heartbeat a proveedores externos: detección de caída < 30 s (QA-D2)
    periodo_salud_proveedores: float = field(default_factory=lambda: float(_env("PERIODO_SALUD", "10")))
    periodo_archivado: float = field(default_factory=lambda: float(_env("PERIODO_ARCHIVADO", "3600")))
    # Recálculo proactivo de recomendaciones (ADD It.5)
    periodo_recomendaciones: float = field(default_factory=lambda: float(_env("PERIODO_RECOMENDACIONES", "21600")))
    # Protección de carga: solicitudes concurrentes antes de rechazar funciones no críticas (QA-E1)
    umbral_carga: int = field(default_factory=lambda: int(_env("UMBRAL_CARGA", "200")))
    # Arrancar hilos de fondo (los tests lo desactivan y ejecutan pasos a mano)
    procesos_fondo: bool = field(default_factory=lambda: _env("PROCESOS_FONDO", "1") == "1")
    # Cargar datos de demostración
    datos_demo: bool = field(default_factory=lambda: _env("DATOS_DEMO", "1") == "1")
    # Ruta a los contratos (spec-driven)
    ruta_specs: Path = RAIZ / "specs"
