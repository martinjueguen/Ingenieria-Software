"""Planificador de tareas periódicas — Procesamiento asíncrono.

ADD It.2, Concepto 4 (ADR-0006): *Schedule resources* / *Defer binding*.
Ejecuta en segundo plano: archivado de viajes (Gestor de Ciclo de Vida),
sondeo de casillas de correo, heartbeat y sondeo de proveedores. Ninguna de
estas tareas corre dentro de una solicitud interactiva.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from trotamundos.dominio.modelo import ahora_utc

log = logging.getLogger(__name__)


@dataclass
class Tarea:
    nombre: str
    periodo: float
    funcion: Callable[[], Any]
    proxima: float = 0.0
    ultima_ejecucion: str | None = None
    ultimo_resultado: Any = None
    ultimo_error: str | None = None
    ejecuciones: int = field(default=0)


class Planificador:
    def __init__(self) -> None:
        self.tareas: dict[str, Tarea] = {}
        self._detener = threading.Event()
        self._hilo = threading.Thread(target=self._bucle, name="planificador", daemon=True)

    def agregar(self, nombre: str, periodo: float, funcion: Callable[[], Any], demora_inicial: float = 1.0) -> None:
        self.tareas[nombre] = Tarea(nombre, periodo, funcion, time.monotonic() + demora_inicial)

    def ejecutar_ahora(self, nombre: str) -> Any:
        tarea = self.tareas[nombre]
        try:
            tarea.ultimo_resultado = tarea.funcion()
            tarea.ultimo_error = None
        except Exception as e:  # noqa: BLE001
            tarea.ultimo_error = f"{type(e).__name__}: {e}"
            log.exception("Tarea %s falló", nombre)
        tarea.ultima_ejecucion = ahora_utc().isoformat()
        tarea.ejecuciones += 1
        tarea.proxima = time.monotonic() + tarea.periodo
        return tarea.ultimo_resultado

    def iniciar(self) -> None:
        self._hilo.start()

    def detener(self) -> None:
        self._detener.set()

    def _bucle(self) -> None:
        while not self._detener.wait(0.5):
            ahora = time.monotonic()
            for tarea in list(self.tareas.values()):
                if tarea.proxima <= ahora:
                    self.ejecutar_ahora(tarea.nombre)

    def estado(self) -> list[dict[str, Any]]:
        return [
            {"nombre": t.nombre, "periodo_s": t.periodo, "ejecuciones": t.ejecuciones,
             "ultima_ejecucion": t.ultima_ejecucion, "ultimo_resultado": t.ultimo_resultado,
             "ultimo_error": t.ultimo_error}
            for t in self.tareas.values()
        ]
