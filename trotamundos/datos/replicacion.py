"""Replicación entre regiones — conector "Replicación entre regiones".

ADD It.4, Concepto 1 (ADR-0012), QA-D1: "0 reservas confirmadas perdidas".
Después de cada transacción confirmada en la región primaria, el estado de la
base OLTP se copia a la base de la región secundaria antes de responder al
cliente (replicación síncrona: RPO = 0).

En producción esto lo resuelve el motor del clúster de base de datos; en el
prototipo se usa la API de *backup* de SQLite (ADR-0017).
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

from trotamundos.dominio.modelo import ahora_utc

log = logging.getLogger(__name__)


class ReplicadorRegional:
    def __init__(self, ruta_replica: str) -> None:
        Path(ruta_replica).parent.mkdir(parents=True, exist_ok=True)
        self.ruta_replica = ruta_replica
        self._lock = threading.Lock()
        self.replicaciones = 0
        self.ultima_replicacion: str | None = None
        self.ultimo_error: str | None = None

    def __call__(self, origen: sqlite3.Connection) -> None:
        with self._lock:
            try:
                destino = sqlite3.connect(self.ruta_replica, timeout=5)
                try:
                    origen.backup(destino)
                finally:
                    destino.close()
                self.replicaciones += 1
                self.ultima_replicacion = ahora_utc().isoformat()
                self.ultimo_error = None
            except sqlite3.Error as e:  # la réplica no bloquea a la primaria
                self.ultimo_error = str(e)
                log.error("Fallo de replicación hacia %s: %s", self.ruta_replica, e)

    def estado(self) -> dict[str, object]:
        return {
            "replica": self.ruta_replica,
            "replicaciones": self.replicaciones,
            "ultima_replicacion": self.ultima_replicacion,
            "ultimo_error": self.ultimo_error,
        }
