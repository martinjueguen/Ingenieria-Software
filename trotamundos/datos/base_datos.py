"""Base de datos operacional (OLTP) — Capa 3: Datos.

ADD It.1 "Base de datos" / It.4 "Base de datos operacional (OLTP)".
En el prototipo es SQLite (ADR-0017); en producción sería un clúster relacional
replicado entre regiones (ADR-0012). Después de cada transacción confirmada
se invoca el gancho de replicación (`datos/replicacion.py`).
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

ESQUEMA_OLTP = """
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    hash_clave TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'viajero',
    idioma TEXT NOT NULL DEFAULT 'es',
    zona_horaria TEXT NOT NULL DEFAULT 'America/Argentina/Buenos_Aires',
    moneda TEXT NOT NULL DEFAULT 'ARS',
    agencia_preferida TEXT
);
CREATE TABLE IF NOT EXISTS viajes (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    nombre TEXT NOT NULL,
    destino TEXT NOT NULL,
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,
    estado TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_viajes_usuario ON viajes(usuario_id, estado);
CREATE TABLE IF NOT EXISTS reservas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    viaje_id TEXT REFERENCES viajes(id),
    tipo TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    codigo_confirmacion TEXT NOT NULL,
    titulo TEXT NOT NULL,
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,
    destino_json TEXT NOT NULL,
    origen_json TEXT,
    estado TEXT NOT NULL,
    detalles_json TEXT NOT NULL,
    fuente TEXT NOT NULL,
    sincronizacion TEXT NOT NULL,
    ultima_actualizacion TEXT NOT NULL,
    UNIQUE (usuario_id, proveedor, codigo_confirmacion)
);
CREATE INDEX IF NOT EXISTS ix_reservas_viaje ON reservas(viaje_id);
CREATE INDEX IF NOT EXISTS ix_reservas_proveedor ON reservas(proveedor, codigo_confirmacion);
CREATE TABLE IF NOT EXISTS whitelist (
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    remitente TEXT NOT NULL,
    PRIMARY KEY (usuario_id, remitente)
);
CREATE TABLE IF NOT EXISTS cuentas_correo (
    usuario_id TEXT PRIMARY KEY REFERENCES usuarios(id),
    proveedor TEXT NOT NULL,
    direccion TEXT NOT NULL,
    token_cifrado BLOB NOT NULL,
    alcances TEXT NOT NULL,
    estado TEXT NOT NULL,
    vinculada_en TEXT NOT NULL,
    ultimo_sondeo TEXT
);
CREATE TABLE IF NOT EXISTS correos_procesados (
    usuario_id TEXT NOT NULL,
    mensaje_id TEXT NOT NULL,
    resultado TEXT NOT NULL,
    PRIMARY KEY (usuario_id, mensaje_id)
);
CREATE TABLE IF NOT EXISTS comparticiones (
    viaje_id TEXT NOT NULL REFERENCES viajes(id),
    email_invitado TEXT NOT NULL,
    permiso TEXT NOT NULL DEFAULT 'lectura',
    creado_en TEXT NOT NULL,
    PRIMARY KEY (viaje_id, email_invitado)
);
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    momento TEXT NOT NULL,
    actor TEXT NOT NULL,
    accion TEXT NOT NULL,
    recurso TEXT NOT NULL,
    resultado TEXT NOT NULL,
    detalle TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS notificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    momento TEXT NOT NULL,
    destinatario TEXT NOT NULL,
    tipo TEXT NOT NULL,
    mensaje TEXT NOT NULL
);
"""


class BaseDatos:
    """Conexión SQLite compartida, segura entre hilos, con gancho post-commit."""

    def __init__(self, ruta: str, esquema: str = ESQUEMA_OLTP) -> None:
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self.ruta = ruta
        self._conexion = sqlite3.connect(ruta, check_same_thread=False, isolation_level=None)
        self._conexion.row_factory = sqlite3.Row
        self._conexion.execute("PRAGMA foreign_keys = ON")
        if ruta != ":memory:":
            self._conexion.execute("PRAGMA journal_mode = WAL")
        self._lock = threading.RLock()
        self._profundidad = 0
        self._ganchos_post_commit: list[Callable[[sqlite3.Connection], None]] = []
        self._conexion.executescript(esquema)

    def asegurar_esquema(self, esquema: str) -> None:
        """Permite que un módulo cree sus propias tablas sin modificar el esquema base."""
        with self._lock:
            self._conexion.executescript(esquema)

    def al_confirmar(self, gancho: Callable[[sqlite3.Connection], None]) -> None:
        self._ganchos_post_commit.append(gancho)

    @contextmanager
    def transaccion(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            externa = self._profundidad == 0
            if externa:
                self._conexion.execute("BEGIN IMMEDIATE")
            self._profundidad += 1
            try:
                yield self._conexion
            except BaseException:
                self._profundidad -= 1
                if externa:
                    self._conexion.execute("ROLLBACK")
                raise
            self._profundidad -= 1
            if externa:
                self._conexion.execute("COMMIT")
                for gancho in self._ganchos_post_commit:
                    gancho(self._conexion)

    def consultar(self, sql: str, parametros: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conexion.execute(sql, parametros).fetchall()

    def consultar_uno(self, sql: str, parametros: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._conexion.execute(sql, parametros).fetchone()

    def ejecutar(self, sql: str, parametros: tuple = ()) -> sqlite3.Cursor:
        with self.transaccion() as conexion:
            return conexion.execute(sql, parametros)

    def cerrar(self) -> None:
        with self._lock:
            self._conexion.close()
