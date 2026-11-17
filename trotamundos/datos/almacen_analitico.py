"""Almacén de datos analítico (OLAP) segregado — Capa 3: Datos.

ADD It.4, Concepto 3 (ADR-0014), US-07. Las consultas pesadas del equipo de
datos se ejecutan exclusivamente contra este almacén, nunca contra la base
operacional. Lo alimenta el *Exportador analítico asíncrono*
(`asincrono/consumidores.py`) a partir de los eventos `reserva.cambiada`.

Los datos se guardan anonimizados: el usuario se reemplaza por un hash con sal
y no se guardan códigos de confirmación ni datos personales.
"""

from __future__ import annotations

import hashlib
from typing import Any

from trotamundos.datos.base_datos import BaseDatos

ESQUEMA_OLAP = """
CREATE TABLE IF NOT EXISTS hechos_reservas (
    evento_id TEXT PRIMARY KEY,
    momento TEXT NOT NULL,
    operacion TEXT NOT NULL,
    usuario_anonimo TEXT NOT NULL,
    tipo_reserva TEXT NOT NULL,
    proveedor TEXT NOT NULL,
    ciudad_destino TEXT NOT NULL,
    pais_destino TEXT NOT NULL,
    mes_viaje TEXT NOT NULL,
    anticipacion_dias INTEGER NOT NULL,
    estado TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_hechos_destino ON hechos_reservas(ciudad_destino);
CREATE INDEX IF NOT EXISTS ix_hechos_proveedor ON hechos_reservas(proveedor, estado);
"""


class AlmacenAnalitico:
    def __init__(self, ruta: str, sal: str) -> None:
        self.bd = BaseDatos(ruta, ESQUEMA_OLAP)
        self._sal = sal

    def anonimizar(self, usuario_id: str) -> str:
        return hashlib.sha256(f"{self._sal}:{usuario_id}".encode()).hexdigest()[:16]

    def registrar_hecho(self, evento_id: str, carga: dict[str, Any]) -> None:
        """Idempotente por `evento_id` (el bus entrega al menos una vez)."""
        self.bd.ejecutar(
            """INSERT OR IGNORE INTO hechos_reservas VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                evento_id,
                carga["momento"],
                carga["operacion"],
                self.anonimizar(carga["usuario_id"]),
                carga["tipo"],
                carga["proveedor"],
                carga.get("ciudad_destino") or "desconocida",
                carga.get("pais_destino") or "desconocido",
                carga["inicio"][:7],
                int(carga.get("anticipacion_dias", 0)),
                carga["estado"],
            ),
        )

    # ---- Consultas analíticas (US-07) ------------------------------------ #

    def tendencias_destinos(self, limite: int = 10) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar(
            """SELECT ciudad_destino, pais_destino, COUNT(*) AS reservas,
                      COUNT(DISTINCT usuario_anonimo) AS viajeros
               FROM hechos_reservas WHERE operacion = 'creada'
               GROUP BY ciudad_destino, pais_destino ORDER BY reservas DESC LIMIT ?""",
            (limite,),
        )]

    def cancelaciones_por_proveedor(self) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar(
            """SELECT proveedor,
                      SUM(CASE WHEN operacion = 'creada' THEN 1 ELSE 0 END) AS reservas,
                      SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END) AS cancelaciones,
                      ROUND(1.0 * SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END)
                            / MAX(SUM(CASE WHEN operacion = 'creada' THEN 1 ELSE 0 END), 1), 3)
                        AS tasa_cancelacion
               FROM hechos_reservas GROUP BY proveedor ORDER BY tasa_cancelacion DESC"""
        )]

    def estacionalidad(self) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar(
            """SELECT mes_viaje, tipo_reserva, COUNT(*) AS reservas,
                      ROUND(AVG(anticipacion_dias), 1) AS anticipacion_promedio_dias
               FROM hechos_reservas WHERE operacion = 'creada'
               GROUP BY mes_viaje, tipo_reserva ORDER BY mes_viaje, tipo_reserva"""
        )]

    def total_hechos(self) -> int:
        fila = self.bd.consultar_uno("SELECT COUNT(*) AS n FROM hechos_reservas")
        return int(fila["n"]) if fila else 0
