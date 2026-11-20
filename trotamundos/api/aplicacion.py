"""Construcción de la aplicación HTTP — módulo "API / Acceso al sistema" (ADR-0002).

Punto de entrada único para los clientes web y móvil: API REST versionada
(`/api/v1`) cuyo contrato es `specs/openapi.json` (ADR-0018). También sirve los
recursos estáticos del cliente web (Capa 1).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from trotamundos import __version__
from trotamundos.api import (
    rutas_analitica,
    rutas_auth,
    rutas_compartir,
    rutas_correo,
    rutas_movil,
    rutas_proveedores,
    rutas_recomendaciones,
    rutas_reservas,
    rutas_salud,
    rutas_simulacion,
    rutas_soporte,
    rutas_viajes,
)
from trotamundos.api.proteccion_carga import EstadoCarga, ProteccionCarga
from trotamundos.app import Sistema
from trotamundos.config import RAIZ

DIR_WEB = RAIZ / "trotamundos" / "web"


def construir_api(sistema: Sistema) -> FastAPI:
    @asynccontextmanager
    async def ciclo(_: FastAPI) -> AsyncIterator[None]:
        if sistema.config.procesos_fondo:
            sistema.iniciar_procesos_fondo()
        yield
        sistema.detener()

    app = FastAPI(
        title="Trotamundos API",
        version=__version__,
        description="Contrato REST del panel de gestión de viajes Trotamundos. "
                    "Todas las fechas en UTC ISO-8601 (ADR-0016).",
        lifespan=ciclo,
    )
    app.state.sistema = sistema
    app.state.carga = EstadoCarga(sistema.config.umbral_carga, sistema.config.region)
    app.add_middleware(ProteccionCarga, estado=app.state.carga)

    v1 = APIRouter(prefix="/api/v1")
    for modulo in (rutas_auth, rutas_viajes, rutas_reservas, rutas_movil, rutas_correo, rutas_proveedores,
                   rutas_soporte, rutas_compartir, rutas_recomendaciones, rutas_analitica, rutas_salud,
                   rutas_simulacion):
        v1.include_router(modulo.router)
    app.include_router(v1)

    app.mount("/static", StaticFiles(directory=DIR_WEB), name="static")

    @app.get("/", include_in_schema=False)
    def inicio() -> FileResponse:
        return FileResponse(DIR_WEB / "index.html")

    @app.get("/movil", include_in_schema=False)
    def movil() -> FileResponse:
        return FileResponse(DIR_WEB / "movil.html")

    return app
