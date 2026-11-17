"""Acceso a almacenamiento (Repositorio) — Capa 3: Datos.

ADD It.1 "Comunicación con almacenamiento" / It.2 "Acceso a almacenamiento".
Encapsula las consultas SQL y aísla a los servicios de negocio de los detalles
de persistencia (táctica Encapsular). Todas las fechas se guardan en UTC ISO-8601
(ADR-0016).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from typing import Any

from trotamundos.datos.base_datos import BaseDatos
from trotamundos.dominio.modelo import (
    EstadoReserva,
    EstadoSincronizacion,
    EstadoViaje,
    FuenteReserva,
    Reserva,
    Ubicacion,
    Viaje,
    a_utc,
    ahora_utc,
)


def _iso(valor: datetime) -> str:
    return a_utc(valor).isoformat()


def _ubicacion_a_json(u: Ubicacion | None) -> str | None:
    return json.dumps(asdict(u), ensure_ascii=False) if u else None


def _ubicacion_de_json(texto: str | None) -> Ubicacion | None:
    return Ubicacion(**json.loads(texto)) if texto else None


def _fila_a_reserva(f: sqlite3.Row) -> Reserva:
    return Reserva(
        id=f["id"],
        usuario_id=f["usuario_id"],
        viaje_id=f["viaje_id"],
        tipo=f["tipo"],
        proveedor=f["proveedor"],
        codigo_confirmacion=f["codigo_confirmacion"],
        titulo=f["titulo"],
        inicio=a_utc(f["inicio"]),
        fin=a_utc(f["fin"]),
        destino=_ubicacion_de_json(f["destino_json"]),  # type: ignore[arg-type]
        origen=_ubicacion_de_json(f["origen_json"]),
        estado=EstadoReserva(f["estado"]),
        detalles=json.loads(f["detalles_json"]),
        fuente=FuenteReserva(f["fuente"]),
        sincronizacion=EstadoSincronizacion(f["sincronizacion"]),
        ultima_actualizacion=a_utc(f["ultima_actualizacion"]),
    )


def _fila_a_viaje(f: sqlite3.Row) -> Viaje:
    return Viaje(
        id=f["id"],
        usuario_id=f["usuario_id"],
        nombre=f["nombre"],
        destino=f["destino"],
        inicio=a_utc(f["inicio"]),
        fin=a_utc(f["fin"]),
        estado=EstadoViaje(f["estado"]),
    )


class RepositorioReservas:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def guardar(self, r: Reserva) -> None:
        self.bd.ejecutar(
            """INSERT INTO reservas (id, usuario_id, viaje_id, tipo, proveedor, codigo_confirmacion,
                   titulo, inicio, fin, destino_json, origen_json, estado, detalles_json, fuente,
                   sincronizacion, ultima_actualizacion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET viaje_id=excluded.viaje_id, tipo=excluded.tipo,
                   proveedor=excluded.proveedor, codigo_confirmacion=excluded.codigo_confirmacion,
                   titulo=excluded.titulo, inicio=excluded.inicio, fin=excluded.fin,
                   destino_json=excluded.destino_json, origen_json=excluded.origen_json,
                   estado=excluded.estado, detalles_json=excluded.detalles_json,
                   fuente=excluded.fuente, sincronizacion=excluded.sincronizacion,
                   ultima_actualizacion=excluded.ultima_actualizacion""",
            (
                r.id, r.usuario_id, r.viaje_id, r.tipo, r.proveedor, r.codigo_confirmacion,
                r.titulo, _iso(r.inicio), _iso(r.fin), _ubicacion_a_json(r.destino),
                _ubicacion_a_json(r.origen), r.estado.value,
                json.dumps(r.detalles, ensure_ascii=False), r.fuente.value,
                r.sincronizacion.value, _iso(r.ultima_actualizacion),
            ),
        )

    def obtener(self, reserva_id: str) -> Reserva | None:
        f = self.bd.consultar_uno("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        return _fila_a_reserva(f) if f else None

    def buscar_por_codigo(self, usuario_id: str, proveedor: str, codigo: str) -> Reserva | None:
        f = self.bd.consultar_uno(
            "SELECT * FROM reservas WHERE usuario_id=? AND proveedor=? AND codigo_confirmacion=?",
            (usuario_id, proveedor, codigo),
        )
        return _fila_a_reserva(f) if f else None

    def buscar_por_proveedor(self, proveedor: str, codigo: str) -> list[Reserva]:
        filas = self.bd.consultar(
            "SELECT * FROM reservas WHERE proveedor=? AND codigo_confirmacion=?", (proveedor, codigo)
        )
        return [_fila_a_reserva(f) for f in filas]

    def de_viaje(self, viaje_id: str) -> list[Reserva]:
        filas = self.bd.consultar(
            "SELECT * FROM reservas WHERE viaje_id = ? ORDER BY inicio", (viaje_id,)
        )
        return [_fila_a_reserva(f) for f in filas]

    def de_usuario(self, usuario_id: str) -> list[Reserva]:
        filas = self.bd.consultar(
            "SELECT * FROM reservas WHERE usuario_id = ? ORDER BY inicio", (usuario_id,)
        )
        return [_fila_a_reserva(f) for f in filas]

    def activas_de_proveedor(self, proveedores: list[str]) -> list[Reserva]:
        if not proveedores:
            return []
        marcas = ",".join("?" for _ in proveedores)
        filas = self.bd.consultar(
            f"""SELECT r.* FROM reservas r JOIN viajes v ON v.id = r.viaje_id
                WHERE r.proveedor IN ({marcas}) AND v.estado != 'archivado'
                  AND r.estado != 'cancelada'""",
            tuple(proveedores),
        )
        return [_fila_a_reserva(f) for f in filas]

    def eliminar(self, reserva_id: str) -> None:
        self.bd.ejecutar("DELETE FROM reservas WHERE id = ?", (reserva_id,))


class RepositorioViajes:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def guardar(self, v: Viaje) -> None:
        self.bd.ejecutar(
            """INSERT INTO viajes (id, usuario_id, nombre, destino, inicio, fin, estado)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre, destino=excluded.destino,
                   inicio=excluded.inicio, fin=excluded.fin, estado=excluded.estado""",
            (v.id, v.usuario_id, v.nombre, v.destino, _iso(v.inicio), _iso(v.fin), v.estado.value),
        )

    def obtener(self, viaje_id: str) -> Viaje | None:
        f = self.bd.consultar_uno("SELECT * FROM viajes WHERE id = ?", (viaje_id,))
        return _fila_a_viaje(f) if f else None

    def de_usuario(self, usuario_id: str, incluir_archivados: bool = False) -> list[Viaje]:
        sql = "SELECT * FROM viajes WHERE usuario_id = ?"
        if not incluir_archivados:
            sql += " AND estado != 'archivado'"
        filas = self.bd.consultar(sql + " ORDER BY inicio", (usuario_id,))
        return [_fila_a_viaje(f) for f in filas]

    def no_archivados(self) -> list[Viaje]:
        filas = self.bd.consultar("SELECT * FROM viajes WHERE estado != 'archivado'")
        return [_fila_a_viaje(f) for f in filas]

    def eliminar(self, viaje_id: str) -> None:
        with self.bd.transaccion() as c:
            c.execute("DELETE FROM comparticiones WHERE viaje_id = ?", (viaje_id,))
            c.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))


class RepositorioUsuarios:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def crear(self, **datos: Any) -> None:
        columnas = ", ".join(datos)
        marcas = ", ".join("?" for _ in datos)
        self.bd.ejecutar(f"INSERT INTO usuarios ({columnas}) VALUES ({marcas})", tuple(datos.values()))

    def por_email(self, email: str) -> dict[str, Any] | None:
        f = self.bd.consultar_uno("SELECT * FROM usuarios WHERE email = ?", (email.lower(),))
        return dict(f) if f else None

    def por_id(self, usuario_id: str) -> dict[str, Any] | None:
        f = self.bd.consultar_uno("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        return dict(f) if f else None

    def actualizar(self, usuario_id: str, **datos: Any) -> None:
        asignaciones = ", ".join(f"{k} = ?" for k in datos)
        self.bd.ejecutar(
            f"UPDATE usuarios SET {asignaciones} WHERE id = ?", (*datos.values(), usuario_id)
        )


class RepositorioWhitelist:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def listar(self, usuario_id: str) -> list[str]:
        filas = self.bd.consultar(
            "SELECT remitente FROM whitelist WHERE usuario_id = ? ORDER BY remitente", (usuario_id,)
        )
        return [f["remitente"] for f in filas]

    def agregar(self, usuario_id: str, remitente: str) -> None:
        self.bd.ejecutar(
            "INSERT OR IGNORE INTO whitelist (usuario_id, remitente) VALUES (?, ?)",
            (usuario_id, remitente.lower().strip()),
        )

    def quitar(self, usuario_id: str, remitente: str) -> None:
        self.bd.ejecutar(
            "DELETE FROM whitelist WHERE usuario_id = ? AND remitente = ?",
            (usuario_id, remitente.lower().strip()),
        )


class RepositorioCuentasCorreo:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def guardar(self, usuario_id: str, proveedor: str, direccion: str, token_cifrado: bytes,
                alcances: list[str], estado: str = "activa") -> None:
        self.bd.ejecutar(
            """INSERT INTO cuentas_correo (usuario_id, proveedor, direccion, token_cifrado, alcances,
                   estado, vinculada_en) VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(usuario_id) DO UPDATE SET proveedor=excluded.proveedor,
                   direccion=excluded.direccion, token_cifrado=excluded.token_cifrado,
                   alcances=excluded.alcances, estado=excluded.estado,
                   vinculada_en=excluded.vinculada_en""",
            (usuario_id, proveedor, direccion, token_cifrado, " ".join(alcances), estado,
             ahora_utc().isoformat()),
        )

    def obtener(self, usuario_id: str) -> dict[str, Any] | None:
        f = self.bd.consultar_uno("SELECT * FROM cuentas_correo WHERE usuario_id = ?", (usuario_id,))
        return dict(f) if f else None

    def activas(self) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar("SELECT * FROM cuentas_correo WHERE estado = 'activa'")]

    def cambiar_estado(self, usuario_id: str, estado: str) -> None:
        self.bd.ejecutar("UPDATE cuentas_correo SET estado = ? WHERE usuario_id = ?", (estado, usuario_id))

    def marcar_sondeo(self, usuario_id: str) -> None:
        self.bd.ejecutar(
            "UPDATE cuentas_correo SET ultimo_sondeo = ? WHERE usuario_id = ?",
            (ahora_utc().isoformat(), usuario_id),
        )

    def ya_procesado(self, usuario_id: str, mensaje_id: str) -> bool:
        return self.bd.consultar_uno(
            "SELECT 1 FROM correos_procesados WHERE usuario_id = ? AND mensaje_id = ?",
            (usuario_id, mensaje_id),
        ) is not None

    def marcar_procesado(self, usuario_id: str, mensaje_id: str, resultado: str) -> None:
        self.bd.ejecutar(
            "INSERT OR IGNORE INTO correos_procesados (usuario_id, mensaje_id, resultado) VALUES (?,?,?)",
            (usuario_id, mensaje_id, resultado),
        )

    def estadisticas(self, usuario_id: str) -> dict[str, int]:
        filas = self.bd.consultar(
            "SELECT resultado, COUNT(*) AS n FROM correos_procesados WHERE usuario_id = ? GROUP BY resultado",
            (usuario_id,),
        )
        return {f["resultado"]: f["n"] for f in filas}


class RepositorioComparticiones:
    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def agregar(self, viaje_id: str, email: str, permiso: str = "lectura") -> None:
        self.bd.ejecutar(
            """INSERT OR REPLACE INTO comparticiones (viaje_id, email_invitado, permiso, creado_en)
               VALUES (?,?,?,?)""",
            (viaje_id, email.lower().strip(), permiso, ahora_utc().isoformat()),
        )

    def quitar(self, viaje_id: str, email: str) -> None:
        self.bd.ejecutar(
            "DELETE FROM comparticiones WHERE viaje_id = ? AND email_invitado = ?",
            (viaje_id, email.lower().strip()),
        )

    def de_viaje(self, viaje_id: str) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar(
            "SELECT * FROM comparticiones WHERE viaje_id = ? ORDER BY email_invitado", (viaje_id,)
        )]

    def permiso(self, viaje_id: str, email: str) -> str | None:
        f = self.bd.consultar_uno(
            "SELECT permiso FROM comparticiones WHERE viaje_id = ? AND email_invitado = ?",
            (viaje_id, email.lower()),
        )
        return f["permiso"] if f else None

    def viajes_compartidos_con(self, email: str) -> list[str]:
        return [f["viaje_id"] for f in self.bd.consultar(
            "SELECT viaje_id FROM comparticiones WHERE email_invitado = ?", (email.lower(),)
        )]


class RepositorioNotificaciones:
    """Notificaciones a operaciones y a usuarios (QA-D1, QA-D2, QA-S2)."""

    def __init__(self, bd: BaseDatos) -> None:
        self.bd = bd

    def notificar(self, destinatario: str, tipo: str, mensaje: str) -> None:
        self.bd.ejecutar(
            "INSERT INTO notificaciones (momento, destinatario, tipo, mensaje) VALUES (?,?,?,?)",
            (ahora_utc().isoformat(), destinatario, tipo, mensaje),
        )

    def de(self, destinatario: str, limite: int = 50) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar(
            "SELECT * FROM notificaciones WHERE destinatario = ? ORDER BY id DESC LIMIT ?",
            (destinatario, limite),
        )]
