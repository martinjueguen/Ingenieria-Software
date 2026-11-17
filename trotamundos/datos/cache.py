"""Gestor de caché de itinerarios activos — Capa 3: Datos.

ADD It.2, Concepto 2 (ADR-0004). Tácticas: *Maintain multiple copies of data*
y *Reduce computational overhead*. Las lecturas del panel y del resumen móvil
se resuelven desde memoria; el Servicio de Reservas invalida la entrada del
usuario inmediatamente después de cada modificación confirmada.

En producción sería un servicio dedicado (p. ej. Redis); en el prototipo es un
diccionario en proceso con TTL detrás de la misma interfaz (ADR-0017).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable


class GestorCache:
    def __init__(self, ttl_segundos: int = 300) -> None:
        self.ttl = ttl_segundos
        self._datos: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.aciertos = 0
        self.fallos = 0
        self.invalidaciones = 0

    def obtener_o_calcular(self, clave: str, calcular: Callable[[], Any]) -> tuple[Any, bool]:
        """Devuelve (valor, fue_acierto)."""
        ahora = time.monotonic()
        with self._lock:
            entrada = self._datos.get(clave)
            if entrada and entrada[0] > ahora:
                self.aciertos += 1
                return entrada[1], True
            self.fallos += 1
        valor = calcular()
        with self._lock:
            self._datos[clave] = (ahora + self.ttl, valor)
        return valor, False

    def invalidar_usuario(self, usuario_id: str) -> None:
        """Purga todas las vistas cacheadas de un usuario (política de invalidación)."""
        prefijo = f"u:{usuario_id}:"
        with self._lock:
            for clave in [c for c in self._datos if c.startswith(prefijo)]:
                del self._datos[clave]
            self.invalidaciones += 1

    def invalidar_todo(self) -> None:
        with self._lock:
            self._datos.clear()
            self.invalidaciones += 1

    @staticmethod
    def clave(usuario_id: str, vista: str) -> str:
        return f"u:{usuario_id}:{vista}"

    def metricas(self) -> dict[str, int]:
        with self._lock:
            return {
                "entradas": len(self._datos),
                "aciertos": self.aciertos,
                "fallos": self.fallos,
                "invalidaciones": self.invalidaciones,
            }
