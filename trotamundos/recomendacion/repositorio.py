"""Persistencia del Sistema de Recomendación (Capa 3).

El módulo crea sus propias tablas en la base operacional: las recomendaciones
precalculadas y las preferencias de cada viajero (parámetros explícitos y
pesos aprendidos).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from typing import Any

from trotamundos.datos.base_datos import BaseDatos
from trotamundos.dominio.modelo import Ubicacion, a_utc, ahora_utc
from trotamundos.integracion.puertos import Oferta
from trotamundos.recomendacion.modelo import (
    PESOS_INICIALES,
    EstadoRecomendacion,
    Motivo,
    Parametros,
    Recomendacion,
)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS preferencias_recomendacion (
    usuario_id TEXT PRIMARY KEY,
    parametros_json TEXT NOT NULL,
    pesos_json TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recomendaciones (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL,
    viaje_id TEXT NOT NULL,
    grupo TEXT NOT NULL,
    motivo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    reserva_origen_id TEXT,
    oferta_json TEXT NOT NULL,
    puntaje REAL NOT NULL,
    caracteristicas_json TEXT NOT NULL,
    explicacion_json TEXT NOT NULL,
    estado TEXT NOT NULL,
    creada_en TEXT NOT NULL,
    resuelta_en TEXT
);
CREATE INDEX IF NOT EXISTS ix_recomendaciones_usuario ON recomendaciones(usuario_id, estado);
"""


def _oferta_a_json(o: Oferta) -> str:
    d = asdict(o)
    d["inicio"], d["fin"] = o.inicio.isoformat(), o.fin.isoformat()
    return json.dumps(d, ensure_ascii=False)


def _oferta_de_json(texto: str) -> Oferta:
    d = json.loads(texto)
    return Oferta(
        id=d["id"], proveedor=d["proveedor"], tipo=d["tipo"], titulo=d["titulo"],
        inicio=a_utc(d["inicio"]), fin=a_utc(d["fin"]), destino=Ubicacion(**d["destino"]),
        origen=Ubicacion(**d["origen"]) if d["origen"] else None, precio=d["precio"], atributos=d["atributos"],
    )


def _fila(f: sqlite3.Row) -> Recomendacion:
    return Recomendacion(
        id=f["id"], usuario_id=f["usuario_id"], viaje_id=f["viaje_id"], grupo=f["grupo"],
        motivo=Motivo(f["motivo"]), descripcion=f["descripcion"], oferta=_oferta_de_json(f["oferta_json"]),
        puntaje=f["puntaje"], caracteristicas=json.loads(f["caracteristicas_json"]),
        estado=EstadoRecomendacion(f["estado"]), reserva_origen_id=f["reserva_origen_id"],
        creada_en=a_utc(f["creada_en"]), explicacion=json.loads(f["explicacion_json"]),
    )


class RepositorioRecomendaciones:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd
        bd.asegurar_esquema(ESQUEMA)

    # ---- Preferencias ------------------------------------------------------ #

    def preferencias(self, usuario_id: str) -> tuple[Parametros, dict[str, float]]:
        f = self.bd.consultar_uno("SELECT * FROM preferencias_recomendacion WHERE usuario_id = ?", (usuario_id,))
        if not f:
            return Parametros(), dict(PESOS_INICIALES)
        return Parametros(**json.loads(f["parametros_json"])), {**PESOS_INICIALES, **json.loads(f["pesos_json"])}

    def guardar_preferencias(self, usuario_id: str, parametros: Parametros, pesos: dict[str, float]) -> None:
        self.bd.ejecutar(
            """INSERT INTO preferencias_recomendacion VALUES (?,?,?,?)
               ON CONFLICT(usuario_id) DO UPDATE SET parametros_json = excluded.parametros_json,
                   pesos_json = excluded.pesos_json, actualizado_en = excluded.actualizado_en""",
            (usuario_id, json.dumps(asdict(parametros)), json.dumps(pesos), ahora_utc().isoformat()),
        )

    # ---- Recomendaciones --------------------------------------------------- #

    def reemplazar_pendientes(self, usuario_id: str, viaje_id: str, nuevas: list[Recomendacion]) -> list[str]:
        """Sincroniza las pendientes del viaje con el nuevo cálculo. Devuelve los grupos nuevos."""
        ahora = ahora_utc().isoformat()
        with self.bd.transaccion() as c:
            previas = {f["id"]: f["grupo"] for f in c.execute(
                "SELECT id, grupo FROM recomendaciones WHERE usuario_id = ? AND viaje_id = ? AND estado = 'pendiente'",
                (usuario_id, viaje_id))}
            resueltas = {f["id"] for f in c.execute(
                "SELECT id FROM recomendaciones WHERE usuario_id = ? AND estado != 'pendiente'", (usuario_id,))}
            ids_nuevas = {r.id for r in nuevas}
            for rid in set(previas) - ids_nuevas:
                c.execute("DELETE FROM recomendaciones WHERE id = ?", (rid,))
            for r in nuevas:
                if r.id in resueltas:
                    continue
                c.execute(
                    """INSERT INTO recomendaciones (id, usuario_id, viaje_id, grupo, motivo, descripcion,
                           reserva_origen_id, oferta_json, puntaje, caracteristicas_json, explicacion_json,
                           estado, creada_en)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?, 'pendiente', ?)
                       ON CONFLICT(id) DO UPDATE SET puntaje = excluded.puntaje,
                           caracteristicas_json = excluded.caracteristicas_json,
                           explicacion_json = excluded.explicacion_json, oferta_json = excluded.oferta_json""",
                    (r.id, usuario_id, viaje_id, r.grupo, r.motivo.value, r.descripcion, r.reserva_origen_id,
                     _oferta_a_json(r.oferta), r.puntaje, json.dumps(r.caracteristicas),
                     json.dumps(r.explicacion), ahora),
                )
        grupos_previos = set(previas.values())
        return sorted({r.grupo for r in nuevas if r.id not in resueltas} - grupos_previos)

    def pendientes(self, usuario_id: str, viaje_id: str | None = None) -> list[Recomendacion]:
        sql = "SELECT * FROM recomendaciones WHERE usuario_id = ? AND estado = 'pendiente'"
        parametros: tuple[Any, ...] = (usuario_id,)
        if viaje_id:
            sql += " AND viaje_id = ?"
            parametros += (viaje_id,)
        return [_fila(f) for f in self.bd.consultar(sql + " ORDER BY grupo, puntaje DESC", parametros)]

    def obtener(self, rec_id: str) -> Recomendacion | None:
        f = self.bd.consultar_uno("SELECT * FROM recomendaciones WHERE id = ?", (rec_id,))
        return _fila(f) if f else None

    def del_grupo(self, usuario_id: str, grupo: str) -> list[Recomendacion]:
        return [_fila(f) for f in self.bd.consultar(
            "SELECT * FROM recomendaciones WHERE usuario_id = ? AND grupo = ?", (usuario_id, grupo))]

    def ofertas_rechazadas(self, usuario_id: str) -> set[str]:
        return {json.loads(f["oferta_json"])["id"] for f in self.bd.consultar(
            "SELECT oferta_json FROM recomendaciones WHERE usuario_id = ? AND estado = 'rechazada'", (usuario_id,))}

    def resolver(self, rec_id: str, estado: EstadoRecomendacion) -> None:
        self.bd.ejecutar("UPDATE recomendaciones SET estado = ?, resuelta_en = ? WHERE id = ?",
                         (estado.value, ahora_utc().isoformat(), rec_id))

    def descartar_resto_del_grupo(self, usuario_id: str, grupo: str, excepto: str) -> None:
        self.bd.ejecutar(
            """UPDATE recomendaciones SET estado = 'descartada', resuelta_en = ?
               WHERE usuario_id = ? AND grupo = ? AND id != ? AND estado = 'pendiente'""",
            (ahora_utc().isoformat(), usuario_id, grupo, excepto),
        )

    def eliminar_pendientes_de_viajes_inactivos(self, usuario_id: str, viajes_activos: set[str]) -> None:
        for f in self.bd.consultar(
                "SELECT DISTINCT viaje_id FROM recomendaciones WHERE usuario_id = ? AND estado = 'pendiente'",
                (usuario_id,)):
            if f["viaje_id"] not in viajes_activos:
                self.bd.ejecutar("DELETE FROM recomendaciones WHERE viaje_id = ? AND estado = 'pendiente'",
                                 (f["viaje_id"],))
