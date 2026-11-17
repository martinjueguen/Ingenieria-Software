"""Grupo de trabajadores concurrentes con autoescalado — Procesamiento asíncrono.

ADD It.3, Concepto 2 (ADR-0008): *Introduce concurrency* (worker pool).
ADD It.4, Concepto 2 (ADR-0013): *Increase resources* — el tamaño del grupo se
ajusta según la longitud de las colas, entre un mínimo y un máximo.

En producción cada worker es una instancia de un grupo de autoescalado; en el
prototipo cada worker es un hilo (ADR-0017).
"""

from __future__ import annotations

import logging
import math
import threading

from trotamundos.asincrono.bus_eventos import BusEventos

log = logging.getLogger(__name__)


class _Worker(threading.Thread):
    def __init__(self, bus: BusEventos, numero: int) -> None:
        super().__init__(name=f"worker-{numero}", daemon=True)
        self.bus = bus
        self.detener = threading.Event()

    def run(self) -> None:
        while not self.detener.is_set():
            try:
                hubo = self.bus.procesar_siguiente()
            except Exception:  # noqa: BLE001
                log.exception("Error inesperado en %s", self.name)
                hubo = False
            if not hubo:
                self.detener.wait(0.2)


class GrupoWorkers:
    def __init__(self, bus: BusEventos, minimo: int, maximo: int, mensajes_por_worker: int) -> None:
        self.bus = bus
        self.minimo = minimo
        self.maximo = maximo
        self.mensajes_por_worker = mensajes_por_worker
        self._workers: list[_Worker] = []
        self._contador = 0
        self._detener = threading.Event()
        self._autoescalador = threading.Thread(target=self._bucle_autoescalado, name="autoescalador", daemon=True)
        self.eventos_escalado: list[str] = []

    def iniciar(self) -> None:
        self._ajustar(self.minimo)
        self._autoescalador.start()

    def detener(self) -> None:
        self._detener.set()
        for w in self._workers:
            w.detener.set()

    def deseados(self, pendientes: int) -> int:
        return max(self.minimo, min(self.maximo, math.ceil(pendientes / self.mensajes_por_worker)))

    def _ajustar(self, cantidad: int) -> None:
        actual = len(self._workers)
        if cantidad > actual:
            for _ in range(cantidad - actual):
                self._contador += 1
                w = _Worker(self.bus, self._contador)
                w.start()
                self._workers.append(w)
        elif cantidad < actual:
            for w in self._workers[cantidad:]:
                w.detener.set()
            self._workers = self._workers[:cantidad]
        if cantidad != actual:
            mensaje = f"workers {actual} -> {cantidad}"
            self.eventos_escalado.append(mensaje)
            self.eventos_escalado[:] = self.eventos_escalado[-20:]
            log.info("Autoescalado: %s", mensaje)

    def _bucle_autoescalado(self) -> None:
        while not self._detener.wait(2.0):
            self._ajustar(self.deseados(self.bus.pendientes()))

    def estado(self) -> dict[str, object]:
        return {
            "activos": len(self._workers),
            "minimo": self.minimo,
            "maximo": self.maximo,
            "ultimos_escalados": list(self.eventos_escalado),
        }
