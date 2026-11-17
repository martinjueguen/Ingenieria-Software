"""Protección de carga y medición de latencia (middleware HTTP).

QA-E1 (R4): ante un pico, el sistema "prioriza consulta de viajes y
actualizaciones sobre funciones no críticas". Si las solicitudes en curso
superan el umbral, las funciones no críticas (analítica, publicación en redes)
responden 503 con `Retry-After`, preservando capacidad para el panel, el
resumen móvil y la ingesta de proveedores.

Además agrega `Server-Timing` y `X-Region` a cada respuesta para observar
QA-R2 (≤ 800 ms) y saber qué región atendió (ADR-0012).
"""

from __future__ import annotations

import threading
import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

RUTAS_NO_CRITICAS = ("/api/v1/analitica",)
SUFIJOS_NO_CRITICOS = ("/publicar",)


def es_no_critica(ruta: str) -> bool:
    return ruta.startswith(RUTAS_NO_CRITICAS) or ruta.endswith(SUFIJOS_NO_CRITICOS)


class EstadoCarga:
    """Contadores compartidos entre el middleware y el endpoint de operaciones."""

    def __init__(self, umbral: int, region: str) -> None:
        self.umbral = umbral
        self.region = region
        self.en_curso = 0
        self.rechazadas = 0
        self.latencias_ms: deque[float] = deque(maxlen=2000)
        self.lock = threading.Lock()

    def metricas(self) -> dict[str, object]:
        with self.lock:
            datos = sorted(self.latencias_ms)
            en_curso, rechazadas = self.en_curso, self.rechazadas
        p95 = datos[min(len(datos) - 1, int(len(datos) * 0.95))] if datos else 0
        return {"en_curso": en_curso, "umbral": self.umbral, "rechazadas_no_criticas": rechazadas,
                "muestras": len(datos), "p95_ms": round(p95, 1), "max_ms": round(datos[-1], 1) if datos else 0,
                "objetivo_ms": 800}


class ProteccionCarga(BaseHTTPMiddleware):
    def __init__(self, app, estado: EstadoCarga) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.estado = estado

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        e = self.estado
        ruta = request.url.path
        with e.lock:
            if e.en_curso >= e.umbral and es_no_critica(ruta):
                e.rechazadas += 1
                return JSONResponse({"detail": "Sistema bajo carga: función no crítica temporalmente suspendida"},
                                    status_code=503, headers={"Retry-After": "30", "X-Region": e.region})
            e.en_curso += 1
        inicio = time.perf_counter()
        try:
            respuesta = await call_next(request)
        finally:
            with e.lock:
                e.en_curso -= 1
        ms = (time.perf_counter() - inicio) * 1000
        if ruta.startswith("/api/"):
            with e.lock:
                e.latencias_ms.append(ms)
        respuesta.headers["Server-Timing"] = f"app;dur={ms:.1f}"
        respuesta.headers["X-Region"] = e.region
        return respuesta
