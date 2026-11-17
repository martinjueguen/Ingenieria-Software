"""Consumidores de las colas (procesamiento en segundo plano).

ADD It.1 "Procesamiento en segundo plano", It.3 "Motor de extracción" y
"Adaptadores", It.4 "Exportador analítico asíncrono". Cada manejador recibe el
sobre `{evento_id, tema, ocurrido_en, carga}`. Si lanza una excepción, el bus
reintenta con backoff exponencial (ADR-0010). Los manejadores son idempotentes
porque la entrega es "al menos una vez".
"""

from __future__ import annotations

import logging
from typing import Any

from trotamundos.datos.almacen_analitico import AlmacenAnalitico
from trotamundos.dominio.modelo import FuenteReserva
from trotamundos.gestion_viajes.servicio_reservas import ServicioReservas
from trotamundos.integracion.correo.motor_extraccion import CorreoSinReserva, extraer
from trotamundos.integracion.puertos import ErrorProveedor
from trotamundos.integracion.registro import RegistroAdaptadores
from trotamundos.datos.repositorios import RepositorioCuentasCorreo, RepositorioReservas

log = logging.getLogger(__name__)
Sobre = dict[str, Any]


class Consumidores:
    def __init__(self, reservas: ServicioReservas, repo_reservas: RepositorioReservas,
                 adaptadores: RegistroAdaptadores, cuentas: RepositorioCuentasCorreo,
                 almacen: AlmacenAnalitico) -> None:
        self.reservas = reservas
        self.repo_reservas = repo_reservas
        self.adaptadores = adaptadores
        self.cuentas = cuentas
        self.almacen = almacen

    # correo.recibido → Motor de extracción → Servicio de Reservas (US-01)
    def correo_recibido(self, sobre: Sobre) -> None:
        c = sobre["carga"]
        try:
            act = extraer(c["remitente"], c["asunto"], c["cuerpo"])
        except CorreoSinReserva:
            self.cuentas.marcar_procesado(c["usuario_id"], c["mensaje_id"] + ":extraccion", "sin_reserva")
            return
        self.reservas.aplicar_actualizacion_externa(c["usuario_id"], act, FuenteReserva.CORREO)

    # proveedor.actualizacion (webhook) → adaptador → Servicio de Reservas (US-03, QA-R1)
    def actualizacion_proveedor(self, sobre: Sobre) -> None:
        c = sobre["carga"]
        act = self.adaptadores.proveedores.obtener(c["proveedor"]).traducir_notificacion(c["carga"])
        for r in self.repo_reservas.buscar_por_proveedor(act.proveedor, act.codigo_confirmacion):
            self.reservas.aplicar_actualizacion_externa(r.usuario_id, act, FuenteReserva.PROVEEDOR)

    # proveedor.consulta → API del proveedor; si falla: última info conocida + reintento (QA-D2)
    def consulta_proveedor(self, sobre: Sobre) -> None:
        c = sobre["carga"]
        adaptador = self.adaptadores.proveedores.obtener(c["proveedor"])
        try:
            act = adaptador.consultar_reserva(c["codigo_confirmacion"])
        except ErrorProveedor:
            self.reservas.marcar_desactualizada(c["proveedor"], c["codigo_confirmacion"])
            raise  # el bus reprograma con retroceso exponencial
        for r in self.repo_reservas.buscar_por_proveedor(act.proveedor, act.codigo_confirmacion):
            self.reservas.aplicar_actualizacion_externa(r.usuario_id, act, FuenteReserva.PROVEEDOR)

    # reserva.cambiada → Exportador analítico asíncrono → OLAP (US-07)
    def exportar_analitica(self, sobre: Sobre) -> None:
        self.almacen.registrar_hecho(sobre["evento_id"], sobre["carga"])
