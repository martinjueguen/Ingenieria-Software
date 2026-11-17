"""Servicio de escaneo y filtrado de correo — Capa 2.

ADD It.3, Conceptos 2 y 3 (ADR-0008, ADR-0009), US-01, US-02, QA-S2.
Pasos del diagrama de secuencia de la iteración 3:
 1-4  obtiene el token cifrado (Gestor de tokens) con alcance de solo lectura;
 5-7  lista SOLO encabezados y compara el remitente contra la whitelist del
      usuario (*Authorize actors*): lo que no coincide se descarta sin leer
      asunto ni cuerpo;
 8-9  publica los correos autorizados en la cola `correo.recibido` (*Queue requests*).
"""

from __future__ import annotations

import logging

from trotamundos.asincrono.bus_eventos import BusEventos
from trotamundos.datos.repositorios import (
    RepositorioCuentasCorreo,
    RepositorioNotificaciones,
    RepositorioWhitelist,
)
from trotamundos.dominio import eventos
from trotamundos.integracion.puertos import ErrorProveedor
from trotamundos.seguridad.gestor_tokens import CuentaNoDisponible, GestorTokens

log = logging.getLogger(__name__)


def remitente_autorizado(remitente: str, whitelist: list[str]) -> bool:
    """Una entrada puede ser una dirección exacta o un dominio (`dominio.com` / `@dominio.com`)."""
    remitente = remitente.lower().strip()
    dominio = remitente.rsplit("@", 1)[-1]
    for entrada in whitelist:
        entrada = entrada.lower().strip()
        if "@" in entrada and not entrada.startswith("@"):
            if remitente == entrada:
                return True
        elif dominio == entrada.lstrip("@") or dominio.endswith("." + entrada.lstrip("@")):
            return True
    return False


class ServicioEscaneoCorreo:
    def __init__(self, tokens: GestorTokens, cuentas: RepositorioCuentasCorreo,
                 whitelist: RepositorioWhitelist, bus: BusEventos,
                 notificaciones: RepositorioNotificaciones) -> None:
        self.tokens = tokens
        self.cuentas = cuentas
        self.whitelist = whitelist
        self.bus = bus
        self.notificaciones = notificaciones

    def sondear(self, usuario_id: str) -> dict[str, int]:
        resultado = {"encolados": 0, "descartados": 0}
        try:
            adaptador, token, direccion = self.tokens.token_para_escaneo(usuario_id)
        except CuentaNoDisponible:
            return resultado
        lista_blanca = self.whitelist.listar(usuario_id)
        try:
            encabezados = adaptador.listar_encabezados(token, direccion)
            for enc in encabezados:
                if self.cuentas.ya_procesado(usuario_id, enc.id):
                    continue
                if not remitente_autorizado(enc.remitente, lista_blanca):
                    # Descarte temprano: nunca se pide el asunto ni el cuerpo (privacidad).
                    self.cuentas.marcar_procesado(usuario_id, enc.id, "descartado")
                    resultado["descartados"] += 1
                    continue
                correo = adaptador.obtener_correo(token, direccion, enc.id)
                self.bus.publicar(eventos.CORREO_RECIBIDO, {
                    "usuario_id": usuario_id,
                    "mensaje_id": correo.id,
                    "remitente": correo.remitente,
                    "asunto": correo.asunto,
                    "cuerpo": correo.cuerpo,
                    "recibido_en": correo.recibido_en.isoformat(),
                })
                self.cuentas.marcar_procesado(usuario_id, enc.id, "encolado")
                resultado["encolados"] += 1
        except ErrorProveedor as e:
            # Se reintenta en el próximo ciclo de sondeo; se avisa a operaciones (QA-D2).
            self.notificaciones.notificar("operaciones", "proveedor.correo", f"Sondeo fallido: {e}")
            log.warning("Sondeo de correo fallido para %s: %s", usuario_id, e)
        except PermissionError:
            log.warning("Token de correo de %s revocado o inválido", usuario_id)
        self.cuentas.marcar_sondeo(usuario_id)
        return resultado

    def sondear_todos(self) -> dict[str, int]:
        total = {"encolados": 0, "descartados": 0}
        for cuenta in self.cuentas.activas():
            parcial = self.sondear(cuenta["usuario_id"])
            for k in total:
                total[k] += parcial[k]
        return total
