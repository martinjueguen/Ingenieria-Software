"""Registro de auditoría de accesos — Capa 3: Datos.

ADD It.4 (ADR-0015): "Almacén seguro donde se asientan todos los accesos e
intentos denegados a itinerarios compartidos". También registra eventos de
seguridad del correo (QA-S2): uso anómalo de tokens y revocaciones.
El registro es de solo inserción (no se exponen operaciones de borrado).
"""

from __future__ import annotations

from typing import Any

from trotamundos.datos.base_datos import BaseDatos
from trotamundos.dominio.modelo import ahora_utc


class RegistroAuditoria:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def registrar(self, actor: str, accion: str, recurso: str, resultado: str, detalle: str = "") -> None:
        self.bd.ejecutar(
            "INSERT INTO auditoria (momento, actor, accion, recurso, resultado, detalle) VALUES (?,?,?,?,?,?)",
            (ahora_utc().isoformat(), actor, accion, recurso, resultado, detalle),
        )

    def consultar(self, recurso_prefijo: str = "", resultado: str | None = None,
                  limite: int = 100) -> list[dict[str, Any]]:
        sql = "SELECT * FROM auditoria WHERE recurso LIKE ?"
        parametros: list[Any] = [f"{recurso_prefijo}%"]
        if resultado:
            sql += " AND resultado = ?"
            parametros.append(resultado)
        sql += " ORDER BY id DESC LIMIT ?"
        parametros.append(limite)
        return [dict(f) for f in self.bd.consultar(sql, tuple(parametros))]
