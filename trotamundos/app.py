"""Raíz de composición: instancia y conecta los elementos del diseño.

Cada componente creado acá corresponde a un elemento de las vistas del ADD
(ver docs/arquitectura.md). Es el único lugar que conoce las implementaciones
concretas; el resto del código depende de interfaces.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from fastapi import FastAPI

from trotamundos.asincrono.bus_eventos import BusEventos
from trotamundos.asincrono.consumidores import Consumidores
from trotamundos.asincrono.planificador import Planificador
from trotamundos.asincrono.workers import GrupoWorkers
from trotamundos.config import Config
from trotamundos.datos.almacen_analitico import AlmacenAnalitico
from trotamundos.datos.base_datos import BaseDatos
from trotamundos.datos.cache import GestorCache
from trotamundos.datos.replicacion import ReplicadorRegional
from trotamundos.datos.repositorios import (
    RepositorioComparticiones,
    RepositorioCuentasCorreo,
    RepositorioNotificaciones,
    RepositorioReservas,
    RepositorioUsuarios,
    RepositorioViajes,
    RepositorioWhitelist,
)
from trotamundos.dominio import eventos
from trotamundos.gestion_viajes.gestor_ciclo_vida import GestorCicloVida
from trotamundos.gestion_viajes.servicio_itinerarios import ServicioItinerarios
from trotamundos.gestion_viajes.servicio_reservas import ServicioReservas
from trotamundos.integracion.agencia import AdaptadorAgenciaEstandar
from trotamundos.integracion.catalogo import AdaptadorCatalogoEstandar
from trotamundos.integracion.correo.gmail import AdaptadorGmail
from trotamundos.integracion.correo.servicio_escaneo import ServicioEscaneoCorreo
from trotamundos.integracion.proveedores.aerolinea import AdaptadorAerolinea
from trotamundos.integracion.proveedores.arrendadora import AdaptadorArrendadora
from trotamundos.integracion.proveedores.hotel import AdaptadorHotel
from trotamundos.integracion.proveedores.tren import AdaptadorTren
from trotamundos.integracion.redes_sociales import AdaptadorRedSocialEstandar
from trotamundos.integracion.registro import RegistroAdaptadores
from trotamundos.integracion.simuladores import (
    SimuladorAgencia,
    SimuladorCorreo,
    SimuladorProveedorViajes,
    SimuladorRedSocial,
)
from trotamundos.integracion.simuladores_catalogo import SimuladorCatalogo
from trotamundos.integracion.sincronizador_proveedores import SincronizadorProveedores
from trotamundos.recomendacion.estrategias import EstrategiaHibrida
from trotamundos.recomendacion.repositorio import RepositorioRecomendaciones
from trotamundos.recomendacion.servicio import ServicioRecomendaciones
from trotamundos.seguridad.auditoria import RegistroAuditoria
from trotamundos.seguridad.autenticacion import EmisorTokens
from trotamundos.seguridad.autorizacion import ControlAccesoItinerarios
from trotamundos.seguridad.cifrado import CifradorTokens
from trotamundos.seguridad.gestor_tokens import GestorTokens

log = logging.getLogger(__name__)


@dataclass
class SistemasExternos:
    """Simuladores de los sistemas externos del diagrama de contexto."""

    proveedores: dict[str, SimuladorProveedorViajes] = field(default_factory=dict)
    correo: SimuladorCorreo = field(default_factory=lambda: SimuladorCorreo("gmail"))
    agencias: dict[str, SimuladorAgencia] = field(default_factory=dict)
    red_social: SimuladorRedSocial = field(default_factory=lambda: SimuladorRedSocial("redsocial"))
    catalogos: dict[str, SimuladorCatalogo] = field(default_factory=dict)


class Sistema:
    """Contenedor de todos los componentes de una región de Trotamundos."""

    def __init__(self, config: Config) -> None:
        self.config = config
        # ---- Capa 3: Datos ------------------------------------------------- #
        self.bd = BaseDatos(config.ruta_bd)
        self.replicador = ReplicadorRegional(config.ruta_replica) if config.ruta_replica else None
        if self.replicador:
            self.bd.al_confirmar(self.replicador)
        self.cache = GestorCache(config.ttl_cache_segundos)
        self.almacen = AlmacenAnalitico(config.ruta_olap, sal=config.secreto_sesion)
        self.repo_reservas = RepositorioReservas(self.bd)
        self.repo_viajes = RepositorioViajes(self.bd)
        self.repo_usuarios = RepositorioUsuarios(self.bd)
        self.repo_whitelist = RepositorioWhitelist(self.bd)
        self.repo_cuentas = RepositorioCuentasCorreo(self.bd)
        self.repo_comparticiones = RepositorioComparticiones(self.bd)
        self.notificaciones = RepositorioNotificaciones(self.bd)
        self.auditoria = RegistroAuditoria(self.bd)

        # ---- Bus de eventos --------------------------------------------------- #
        self.bus = BusEventos(
            config.ruta_bus, config.ruta_specs / "eventos", config.max_intentos,
            config.backoff_base_segundos, al_agotar_reintentos=self._mensaje_muerto,
        )

        # ---- Sistemas externos (simulados) y adaptadores ----------------------- #
        self.externos = SistemasExternos()
        self.adaptadores = RegistroAdaptadores()
        self._registrar_adaptadores()

        # ---- Seguridad -------------------------------------------------------- #
        self.emisor_tokens = EmisorTokens(config.secreto_sesion)
        self.cifrador = CifradorTokens(config.clave_cifrado, config.secreto_sesion)
        self.control_acceso = ControlAccesoItinerarios(self.repo_viajes, self.repo_comparticiones, self.auditoria)
        self.gestor_tokens = GestorTokens(self.repo_cuentas, self.cifrador, self.adaptadores,
                                          self.auditoria, self.notificaciones)
        self.externos.correo.reportar_uso = self._senal_seguridad_correo

        # ---- Gestión de viajes y reservas ------------------------------------- #
        self.itinerarios = ServicioItinerarios(self.repo_viajes, self.repo_reservas)
        self.reservas = ServicioReservas(self.repo_reservas, self.itinerarios, self.cache, self.bus)
        self.ciclo_vida = GestorCicloVida(self.repo_viajes, self.cache)

        # ---- Integración / procesamiento asíncrono ---------------------------- #
        self.escaneo = ServicioEscaneoCorreo(self.gestor_tokens, self.repo_cuentas, self.repo_whitelist,
                                             self.bus, self.notificaciones)
        self.sincronizador = SincronizadorProveedores(self.adaptadores, self.repo_reservas, self.bus,
                                                      self.notificaciones)
        for sim in self.externos.proveedores.values():
            sim.webhook = self.sincronizador.recibir_webhook
        self.consumidores = Consumidores(self.reservas, self.repo_reservas, self.adaptadores,
                                         self.repo_cuentas, self.almacen)
        self.bus.suscribir(eventos.CORREO_RECIBIDO, "extraccion-correo", self.consumidores.correo_recibido)
        self.bus.suscribir(eventos.PROVEEDOR_ACTUALIZACION, "ingesta-proveedores",
                           self.consumidores.actualizacion_proveedor)
        self.bus.suscribir(eventos.PROVEEDOR_CONSULTA, "consultas-proveedores", self.consumidores.consulta_proveedor)
        self.bus.suscribir(eventos.RESERVA_CAMBIADA, "exportador-analitico", self.consumidores.exportar_analitica)

        # ---- Sistema de Recomendación (ADD It.5) ------------------------------- #
        self.recomendaciones = ServicioRecomendaciones(
            RepositorioRecomendaciones(self.bd), self.repo_viajes, self.repo_reservas, self.reservas,
            self.adaptadores, self.almacen, self.bus, self.notificaciones, EstrategiaHibrida(),
        )
        self.bus.suscribir(eventos.RESERVA_CAMBIADA, "recomendador", self.recomendaciones.al_cambiar_reserva)
        self.bus.suscribir(eventos.RECOMENDACION_SOLICITADA, "recomendador-solicitudes",
                           self.recomendaciones.al_solicitar)
        self.bus.suscribir(eventos.RECOMENDACION_FEEDBACK, "aprendizaje-recomendaciones",
                           self.recomendaciones.al_recibir_feedback)

        self.workers = GrupoWorkers(self.bus, config.workers_min, config.workers_max, config.mensajes_por_worker)
        self.planificador = Planificador()
        self.planificador.agregar("archivado-viajes", config.periodo_archivado, self.ciclo_vida.ejecutar)
        self.planificador.agregar("sondeo-correo", config.periodo_sondeo_correo, self.escaneo.sondear_todos)
        self.planificador.agregar("salud-proveedores", config.periodo_salud_proveedores,
                                  self.sincronizador.verificar_salud)
        self.planificador.agregar("sondeo-proveedores", config.periodo_sondeo_proveedores, self.sincronizador.sondear)
        self.planificador.agregar("recomendaciones-proactivas", config.periodo_recomendaciones,
                                  self.recomendaciones.solicitar_para_todos)

    def _registrar_adaptadores(self) -> None:
        """Alta de proveedores. Un proveedor nuevo = una línea acá + su adaptador (QA-I1)."""
        catalogo = [
            ("aerolineas-sur", AdaptadorAerolinea),
            ("hoteles-plaza", AdaptadorHotel),
            ("rentacar", AdaptadorArrendadora),
            ("trenes-del-sur", AdaptadorTren),
        ]
        for codigo, clase in catalogo:
            sim = SimuladorProveedorViajes(codigo)
            self.externos.proveedores[codigo] = sim
            self.adaptadores.proveedores.registrar(clase(codigo, sim))
        # Catálogos de ofertas (ADD It.5): un proveedor con catálogo = una línea más.
        for codigo, tipo in (("hoteles-plaza", "hotel"), ("rentacar", "auto"),
                             ("trenes-del-sur", "tren"), ("aerolineas-sur", "vuelo")):
            sim_catalogo = SimuladorCatalogo(tipo, self.externos.proveedores[codigo])
            self.externos.catalogos[codigo] = sim_catalogo
            self.adaptadores.catalogos.registrar(AdaptadorCatalogoEstandar(sim_catalogo))
        self.adaptadores.correo.registrar(AdaptadorGmail(self.externos.correo))
        for codigo, nombre in (("viajes-pampa", "Viajes Pampa"), ("global-travel", "Global Travel")):
            sim_agencia = SimuladorAgencia(codigo, nombre)
            self.externos.agencias[codigo] = sim_agencia
            self.adaptadores.agencias.registrar(AdaptadorAgenciaEstandar(sim_agencia))
        self.adaptadores.redes.registrar(AdaptadorRedSocialEstandar(self.externos.red_social))

    def _senal_seguridad_correo(self, direccion: str, origen: str) -> None:
        fila = self.bd.consultar_uno("SELECT usuario_id FROM cuentas_correo WHERE direccion = ?", (direccion,))
        if fila:
            self.gestor_tokens.reportar_uso(fila["usuario_id"], origen)

    def _mensaje_muerto(self, cola: str, sobre: dict, error: str) -> None:
        self.notificaciones.notificar("operaciones", "mensaje.muerto",
                                      f"{cola}: {sobre.get('tema')} agotó reintentos ({error})")

    def iniciar_procesos_fondo(self) -> None:
        self.workers.iniciar()
        self.planificador.iniciar()

    def detener(self) -> None:
        self.workers.detener()
        self.planificador.detener()


def crear_app(config: Config | None = None) -> FastAPI:
    from trotamundos.api.aplicacion import construir_api
    from trotamundos.datos_demo import cargar_datos_demo, sembrar_simuladores

    config = config or Config()
    sistema = Sistema(config)
    sembrar_simuladores(sistema)
    if config.datos_demo:
        cargar_datos_demo(sistema)
    return construir_api(sistema)
