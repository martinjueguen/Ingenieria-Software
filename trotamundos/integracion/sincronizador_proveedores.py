"""Sincronización con proveedores turísticos — Integración con servicios externos.

ADD It.3, Conceptos 2 y 4 (ADR-0008, ADR-0010), US-03, QA-R1, QA-D2:
- Webhooks: la notificación del proveedor se encola tal cual (*Queue requests*);
  un worker la traduce con el adaptador y la aplica.
- Sondeo periódico: se encolan consultas a la API de cada reserva activa
  (cubre proveedores sin webhooks y la reconciliación).
- Heartbeat (*Ping/Echo*): detecta la caída de un proveedor en < 30 s, marca sus
  reservas como "última actualización" (se sigue mostrando la última info
  conocida), notifica a operaciones y, al recuperarse, encola la reconciliación
  completa (< 5 min).
"""

from __future__ import annotations

import logging
from typing import Any

from trotamundos.asincrono.bus_eventos import BusEventos
from trotamundos.datos.repositorios import RepositorioNotificaciones, RepositorioReservas
from trotamundos.dominio import eventos
from trotamundos.dominio.modelo import ahora_utc
from trotamundos.integracion.registro import RegistroAdaptadores

log = logging.getLogger(__name__)


class SincronizadorProveedores:
    def __init__(self, adaptadores: RegistroAdaptadores, reservas: RepositorioReservas,
                 bus: BusEventos, notificaciones: RepositorioNotificaciones) -> None:
        self.adaptadores = adaptadores
        self.reservas = reservas
        self.bus = bus
        self.notificaciones = notificaciones
        self.caidos: dict[str, str] = {}  # proveedor -> momento de detección

    def recibir_webhook(self, proveedor: str, carga: dict[str, Any]) -> str:
        self.adaptadores.proveedores.obtener(proveedor)  # valida que esté registrado
        return self.bus.publicar(eventos.PROVEEDOR_ACTUALIZACION, {
            "proveedor": proveedor, "origen": "webhook", "recibido_en": ahora_utc().isoformat(),
            "carga": carga,
        })

    def encolar_consultas(self, proveedor: str | None = None) -> int:
        codigos = [proveedor] if proveedor else self.adaptadores.proveedores.codigos()
        vistos: set[tuple[str, str]] = set()
        for r in self.reservas.activas_de_proveedor(codigos):
            clave = (r.proveedor, r.codigo_confirmacion)
            if clave in vistos:
                continue
            vistos.add(clave)
            self.bus.publicar(eventos.PROVEEDOR_CONSULTA, {
                "proveedor": r.proveedor, "codigo_confirmacion": r.codigo_confirmacion,
            })
        return len(vistos)

    def sondear(self) -> dict[str, int]:
        disponibles = [c for c in self.adaptadores.proveedores.codigos() if c not in self.caidos]
        return {"consultas_encoladas": sum(self.encolar_consultas(c) for c in disponibles)}

    def verificar_salud(self) -> dict[str, str]:
        estado: dict[str, str] = {}
        for adaptador in self.adaptadores.proveedores.todos():
            try:
                vivo = adaptador.disponible()
            except Exception:  # noqa: BLE001
                vivo = False
            codigo = adaptador.codigo
            if not vivo and codigo not in self.caidos:
                self.caidos[codigo] = ahora_utc().isoformat()
                self.notificaciones.notificar("operaciones", "proveedor.caido",
                                              f"El proveedor {codigo} no responde; se muestra la última información conocida")
                # Encolar consultas: fallarán, marcarán "desactualizada" y quedarán reintentando con backoff.
                self.encolar_consultas(codigo)
                log.warning("Proveedor %s caído", codigo)
            elif vivo and codigo in self.caidos:
                del self.caidos[codigo]
                n = self.encolar_consultas(codigo)
                self.notificaciones.notificar("operaciones", "proveedor.recuperado",
                                              f"El proveedor {codigo} se recuperó; reconciliando {n} reservas")
            estado[codigo] = "caido" if codigo in self.caidos else "disponible"
        return estado
