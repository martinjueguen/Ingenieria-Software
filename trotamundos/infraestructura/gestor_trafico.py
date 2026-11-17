"""Global Traffic Manager / GeoDNS (simulado) — Vista de despliegue, ADD It.4.

ADR-0012, QA-D1. Tácticas: *Heartbeat / Ping-Echo* (chequeo de salud de cada
región), *Removal from service* y *Active redundancy* (región secundaria caliente).
Es el punto de entrada global: reenvía cada solicitud a la región activa. Si la
región activa no responde N heartbeats seguidos, conmuta a la siguiente región
sana, la promueve a activa y registra el incidente.

En producción es un servicio de DNS/anycast administrado; en el prototipo es un
proxy HTTP en Python (ADR-0017).

Uso:  python -m trotamundos.infraestructura.gestor_trafico \
          --region primaria=http://127.0.0.1:8001 --region secundaria=http://127.0.0.1:8002
"""

from __future__ import annotations

import argparse
import logging
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

log = logging.getLogger("gestor_trafico")
CABECERAS_EXCLUIDAS = {"host", "content-length", "connection", "transfer-encoding", "content-encoding"}


@dataclass
class Region:
    nombre: str
    url: str
    sana: bool = True
    fallos_seguidos: int = 0
    ultimo_heartbeat: str | None = None


@dataclass
class GestorTrafico:
    regiones: list[Region]
    clave_infra: str
    umbral_fallos: int = 3
    periodo_heartbeat: float = 1.0
    activa: int = 0
    incidentes: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._detener = threading.Event()
        self._cliente = httpx.Client(timeout=0.8)

    @property
    def region_activa(self) -> Region:
        return self.regiones[self.activa]

    def heartbeat(self) -> None:
        for region in self.regiones:
            try:
                ok = self._cliente.get(f"{region.url}/api/v1/salud").status_code == 200
            except httpx.HTTPError:
                ok = False
            region.ultimo_heartbeat = datetime.now(timezone.utc).isoformat()
            region.fallos_seguidos = 0 if ok else region.fallos_seguidos + 1
            region.sana = ok or region.fallos_seguidos < self.umbral_fallos
        if not self.region_activa.sana:
            self._conmutar()

    def _conmutar(self) -> None:
        caida = self.region_activa
        for i, region in enumerate(self.regiones):
            if i != self.activa and region.sana and region.fallos_seguidos == 0:
                inicio = time.perf_counter()
                self.activa = i
                try:
                    self._cliente.post(f"{region.url}/api/v1/region/promover",
                                       headers={"X-Clave-Infra": self.clave_infra})
                except httpx.HTTPError as e:
                    log.error("No se pudo promover %s: %s", region.nombre, e)
                incidente = {
                    "momento": datetime.now(timezone.utc).isoformat(),
                    "region_caida": caida.nombre,
                    "nueva_activa": region.nombre,
                    "detectado_tras_heartbeats": self.umbral_fallos,
                    "conmutacion_ms": round((time.perf_counter() - inicio) * 1000, 1),
                }
                self.incidentes.append(incidente)
                log.warning("CONMUTACIÓN: %s", incidente)  # notificación a operaciones
                return
        log.error("Ninguna región sana disponible")

    def bucle(self) -> None:
        while not self._detener.wait(self.periodo_heartbeat):
            self.heartbeat()

    def detener(self) -> None:
        self._detener.set()


def crear_proxy(gestor: GestorTrafico) -> FastAPI:
    @asynccontextmanager
    async def ciclo(_: FastAPI) -> AsyncIterator[None]:
        hilo = threading.Thread(target=gestor.bucle, daemon=True, name="heartbeat")
        hilo.start()
        yield
        gestor.detener()

    app = FastAPI(title="Global Traffic Manager (simulado)", lifespan=ciclo)
    cliente = httpx.AsyncClient(timeout=10)

    @app.get("/gtm/estado")
    def estado() -> dict:
        return {"activa": gestor.region_activa.nombre,
                "regiones": [r.__dict__ for r in gestor.regiones], "incidentes": gestor.incidentes}

    @app.api_route("/{ruta:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def reenviar(ruta: str, request: Request) -> Response:
        destino = f"{gestor.region_activa.url}/{ruta}"
        cabeceras = {k: v for k, v in request.headers.items() if k.lower() not in CABECERAS_EXCLUIDAS}
        try:
            r = await cliente.request(request.method, destino, params=request.query_params,
                                      content=await request.body(), headers=cabeceras)
        except httpx.HTTPError:
            return Response('{"detail":"Región no disponible, reintentá en unos segundos"}', status_code=503,
                            media_type="application/json", headers={"Retry-After": "2"})
        salida = {k: v for k, v in r.headers.items() if k.lower() not in CABECERAS_EXCLUIDAS}
        return Response(r.content, status_code=r.status_code, headers=salida)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Global Traffic Manager simulado")
    parser.add_argument("--region", action="append", required=True, help="nombre=url (en orden de prioridad)")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--clave-infra", default="secreto-solo-para-desarrollo")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    regiones = [Region(*r.split("=", 1)) for r in args.region]
    uvicorn.run(crear_proxy(GestorTrafico(regiones, args.clave_infra)), host="127.0.0.1", port=args.puerto)


if __name__ == "__main__":
    main()
