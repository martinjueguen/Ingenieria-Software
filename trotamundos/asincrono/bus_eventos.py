"""Bus de eventos con colas persistentes — Capa 2/3.

ADD It.1 "Bus de eventos" (ADR-0001) e It.3, Concepto 2 (ADR-0008):
- *Queue requests*: los productores publican y siguen; nadie espera el procesamiento.
- Persistencia de mensajes: sobreviven a la caída del proceso (entrega al menos una vez).
- Reintentos con retroceso exponencial y cola de mensajes muertos (ADR-0010).
- Cada tema puede tener varias colas suscriptas (fan-out por grupo de consumidores).
- Spec-driven (ADR-0018): toda carga publicada se valida contra su contrato
  `specs/eventos/<tema>.schema.json`; un mensaje que no cumple el contrato se rechaza.

En producción sería un broker (RabbitMQ/Kafka/SQS); en el prototipo es SQLite
detrás de esta misma interfaz (ADR-0017).
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator

from trotamundos.datos.base_datos import BaseDatos
from trotamundos.dominio.modelo import a_utc, ahora_utc, nuevo_id

log = logging.getLogger(__name__)

ESQUEMA_BUS = """
CREATE TABLE IF NOT EXISTS mensajes (
    id TEXT PRIMARY KEY,
    cola TEXT NOT NULL,
    tema TEXT NOT NULL,
    sobre_json TEXT NOT NULL,
    estado TEXT NOT NULL,
    intentos INTEGER NOT NULL DEFAULT 0,
    disponible_en TEXT NOT NULL,
    creado_en TEXT NOT NULL,
    procesado_en TEXT,
    ultimo_error TEXT
);
CREATE INDEX IF NOT EXISTS ix_mensajes_listos ON mensajes(estado, disponible_en);
"""

Manejador = Callable[[dict[str, Any]], None]


class ContratoInvalido(ValueError):
    pass


@dataclass
class Suscripcion:
    cola: str
    tema: str
    manejador: Manejador


class BusEventos:
    def __init__(self, ruta: str, ruta_contratos: Path, max_intentos: int = 6,
                 backoff_base_segundos: float = 1.0,
                 al_agotar_reintentos: Callable[[str, dict[str, Any], str], None] | None = None) -> None:
        self.bd = BaseDatos(ruta, ESQUEMA_BUS)
        self.max_intentos = max_intentos
        self.backoff_base = backoff_base_segundos
        self._al_agotar = al_agotar_reintentos
        self._suscripciones: dict[str, Suscripcion] = {}
        self._por_tema: dict[str, list[str]] = {}
        self._validadores = self._cargar_contratos(ruta_contratos)
        self._lock_toma = threading.Lock()
        # Mensajes que quedaron "en_proceso" por una caída se reencolan (al menos una vez).
        self.bd.ejecutar("UPDATE mensajes SET estado = 'pendiente' WHERE estado = 'en_proceso'")

    @staticmethod
    def _cargar_contratos(ruta: Path) -> dict[str, Draft202012Validator]:
        validadores = {}
        for archivo in sorted(ruta.glob("*.schema.json")):
            esquema = json.loads(archivo.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(esquema)
            validadores[archivo.name.removesuffix(".schema.json")] = Draft202012Validator(esquema)
        return validadores

    def temas_con_contrato(self) -> list[str]:
        return sorted(self._validadores)

    # ---- Suscripción y publicación --------------------------------------- #

    def suscribir(self, tema: str, cola: str, manejador: Manejador) -> None:
        if tema not in self._validadores:
            raise ContratoInvalido(f"No existe contrato para el tema '{tema}'")
        self._suscripciones[cola] = Suscripcion(cola, tema, manejador)
        self._por_tema.setdefault(tema, []).append(cola)

    def publicar(self, tema: str, carga: dict[str, Any], retraso_segundos: float = 0) -> str:
        validador = self._validadores.get(tema)
        if validador is None:
            raise ContratoInvalido(f"No existe contrato para el tema '{tema}'")
        errores = sorted(validador.iter_errors(carga), key=lambda e: e.path)
        if errores:
            detalle = "; ".join(f"{'/'.join(map(str, e.path)) or '(raíz)'}: {e.message}" for e in errores)
            raise ContratoInvalido(f"La carga de '{tema}' no cumple el contrato: {detalle}")
        evento_id = nuevo_id()
        ahora = ahora_utc()
        sobre = {"evento_id": evento_id, "tema": tema, "ocurrido_en": ahora.isoformat(), "carga": carga}
        disponible = (ahora + timedelta(seconds=retraso_segundos)).isoformat()
        with self.bd.transaccion() as c:
            for cola in self._por_tema.get(tema, []):
                c.execute(
                    """INSERT INTO mensajes (id, cola, tema, sobre_json, estado, disponible_en, creado_en)
                       VALUES (?,?,?,?, 'pendiente', ?, ?)""",
                    (nuevo_id(), cola, tema, json.dumps(sobre, ensure_ascii=False), disponible, ahora.isoformat()),
                )
        return evento_id

    # ---- Consumo ----------------------------------------------------------- #

    def _tomar(self) -> tuple[str, str, dict[str, Any], int] | None:
        with self._lock_toma, self.bd.transaccion() as c:
            fila = c.execute(
                """SELECT id, cola, sobre_json, intentos FROM mensajes
                   WHERE estado = 'pendiente' AND disponible_en <= ?
                   ORDER BY disponible_en LIMIT 1""",
                (ahora_utc().isoformat(),),
            ).fetchone()
            if not fila:
                return None
            c.execute("UPDATE mensajes SET estado = 'en_proceso' WHERE id = ?", (fila["id"],))
            return fila["id"], fila["cola"], json.loads(fila["sobre_json"]), fila["intentos"]

    def procesar_siguiente(self) -> bool:
        """Procesa un mensaje listo. Devuelve False si no había ninguno."""
        tomado = self._tomar()
        if tomado is None:
            return False
        mensaje_id, cola, sobre, intentos = tomado
        suscripcion = self._suscripciones.get(cola)
        try:
            if suscripcion is None:
                raise RuntimeError(f"Sin consumidor para la cola {cola}")
            suscripcion.manejador(sobre)
        except Exception as error:  # noqa: BLE001 — cualquier falla del consumidor se reintenta
            self._registrar_falla(mensaje_id, cola, sobre, intentos + 1, error)
        else:
            self.bd.ejecutar(
                "UPDATE mensajes SET estado = 'hecho', procesado_en = ?, intentos = ? WHERE id = ?",
                (ahora_utc().isoformat(), intentos + 1, mensaje_id),
            )
        return True

    def _registrar_falla(self, mensaje_id: str, cola: str, sobre: dict[str, Any], intentos: int,
                         error: Exception) -> None:
        texto = f"{type(error).__name__}: {error}"
        if intentos >= self.max_intentos:
            self.bd.ejecutar(
                "UPDATE mensajes SET estado = 'muerto', intentos = ?, ultimo_error = ? WHERE id = ?",
                (intentos, texto, mensaje_id),
            )
            log.error("Mensaje %s de %s agotó reintentos: %s", mensaje_id, cola, texto)
            if self._al_agotar:
                self._al_agotar(cola, sobre, texto)
            return
        espera = self.backoff_base * (2 ** (intentos - 1))  # retroceso exponencial
        disponible = (ahora_utc() + timedelta(seconds=espera)).isoformat()
        self.bd.ejecutar(
            """UPDATE mensajes SET estado = 'pendiente', intentos = ?, disponible_en = ?, ultimo_error = ?
               WHERE id = ?""",
            (intentos, disponible, texto, mensaje_id),
        )
        log.warning("Mensaje %s de %s falló (intento %s), reintento en %.1fs: %s",
                    mensaje_id, cola, intentos, espera, texto)

    def procesar_pendientes(self, maximo: int = 10_000) -> int:
        """Drena los mensajes listos en el hilo actual (usado por tests y demo)."""
        n = 0
        while n < maximo and self.procesar_siguiente():
            n += 1
        return n

    # ---- Observabilidad ---------------------------------------------------- #

    def pendientes(self) -> int:
        fila = self.bd.consultar_uno("SELECT COUNT(*) AS n FROM mensajes WHERE estado IN ('pendiente','en_proceso')")
        return int(fila["n"]) if fila else 0

    def metricas(self) -> dict[str, Any]:
        por_estado = {
            f"{f['cola']}.{f['estado']}": f["n"]
            for f in self.bd.consultar("SELECT cola, estado, COUNT(*) AS n FROM mensajes GROUP BY cola, estado")
        }
        fila = self.bd.consultar_uno(
            """SELECT MAX(julianday(procesado_en) - julianday(creado_en)) * 86400 AS max_s,
                      AVG(julianday(procesado_en) - julianday(creado_en)) * 86400 AS prom_s
               FROM mensajes WHERE estado = 'hecho'"""
        )
        mas_viejo = self.bd.consultar_uno(
            "SELECT MIN(creado_en) AS m FROM mensajes WHERE estado IN ('pendiente','en_proceso')"
        )
        antiguedad = None
        if mas_viejo and mas_viejo["m"]:
            antiguedad = (ahora_utc() - a_utc(mas_viejo["m"])).total_seconds()
        return {
            "pendientes": self.pendientes(),
            "por_cola_y_estado": por_estado,
            "latencia_cola_max_s": round(fila["max_s"] or 0, 3) if fila else 0,
            "latencia_cola_promedio_s": round(fila["prom_s"] or 0, 3) if fila else 0,
            "antiguedad_pendiente_mas_viejo_s": antiguedad,
        }

    def mensajes_muertos(self) -> list[dict[str, Any]]:
        return [dict(f) for f in self.bd.consultar(
            "SELECT id, cola, tema, intentos, ultimo_error, creado_en FROM mensajes WHERE estado = 'muerto'"
        )]
