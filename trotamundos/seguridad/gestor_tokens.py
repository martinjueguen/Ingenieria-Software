"""Gestor de tokens y seguridad de ingesta — Capa 2.

ADD It.3, Concepto 3 (ADR-0009), QA-S2:
- *Limit access*: solo se solicitan y aceptan tokens con alcance de solo lectura.
- *Encrypt data*: los tokens se guardan cifrados (Fernet) en el almacén.
- Detección de uso anómalo → revocación inmediata, notificación al usuario y
  registro en auditoría (detección < 5 min, revocación < 1 min).

El único consumidor legítimo de los tokens es el Servicio de Escaneo. El
proveedor de correo reporta cada uso del token (señal de seguridad); si el uso
proviene de otro origen, o supera la tasa esperada, se considera comprometido.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from trotamundos.datos.repositorios import RepositorioCuentasCorreo, RepositorioNotificaciones
from trotamundos.integracion.puertos import AdaptadorCorreo
from trotamundos.integracion.registro import RegistroAdaptadores
from trotamundos.seguridad.auditoria import RegistroAuditoria
from trotamundos.seguridad.cifrado import CifradorTokens

ORIGEN_LEGITIMO = "trotamundos-servicio-escaneo"
MAX_USOS_POR_MINUTO = 30


class AlcanceNoPermitido(Exception):
    pass


class CuentaNoDisponible(Exception):
    pass


class GestorTokens:
    def __init__(self, cuentas: RepositorioCuentasCorreo, cifrador: CifradorTokens,
                 adaptadores: RegistroAdaptadores, auditoria: RegistroAuditoria,
                 notificaciones: RepositorioNotificaciones) -> None:
        self.cuentas = cuentas
        self.cifrador = cifrador
        self.adaptadores = adaptadores
        self.auditoria = auditoria
        self.notificaciones = notificaciones
        self._usos: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def vincular(self, usuario_id: str, email_usuario: str, proveedor: str, direccion: str) -> dict:
        adaptador: AdaptadorCorreo = self.adaptadores.correo.obtener(proveedor)
        token, otorgados = adaptador.autorizar(direccion, [AdaptadorCorreo.ALCANCE_SOLO_LECTURA])
        if set(otorgados) != {AdaptadorCorreo.ALCANCE_SOLO_LECTURA}:
            adaptador.revocar(token)
            self.auditoria.registrar(email_usuario, "correo.vincular", f"correo:{direccion}",
                                     "denegado", f"alcances excesivos: {otorgados}")
            raise AlcanceNoPermitido("El proveedor otorgó alcances distintos de solo lectura")
        self.cuentas.guardar(usuario_id, proveedor, direccion, self.cifrador.cifrar(token), otorgados)
        self.auditoria.registrar(email_usuario, "correo.vincular", f"correo:{direccion}", "concedido",
                                 "alcance solo lectura")
        return {"proveedor": proveedor, "direccion": direccion, "alcances": otorgados, "estado": "activa"}

    def token_para_escaneo(self, usuario_id: str) -> tuple[AdaptadorCorreo, str, str]:
        """Devuelve (adaptador, token en claro, dirección) solo para el Servicio de Escaneo."""
        cuenta = self.cuentas.obtener(usuario_id)
        if not cuenta or cuenta["estado"] != "activa":
            raise CuentaNoDisponible(usuario_id)
        token = self.cifrador.descifrar(cuenta["token_cifrado"])
        return self.adaptadores.correo.obtener(cuenta["proveedor"]), token, cuenta["direccion"]

    def reportar_uso(self, usuario_id: str, origen: str) -> bool:
        """Señal de seguridad del proveedor de correo. Devuelve False si se revocó."""
        ahora = time.monotonic()
        with self._lock:
            usos = self._usos[usuario_id]
            usos.append(ahora)
            while usos and usos[0] < ahora - 60:
                usos.popleft()
            excesivo = len(usos) > MAX_USOS_POR_MINUTO
        if origen != ORIGEN_LEGITIMO:
            self.revocar(usuario_id, f"uso del token desde origen no reconocido: {origen}", anomalo=True)
            return False
        if excesivo:
            self.revocar(usuario_id, "tasa de uso anómala del token", anomalo=True)
            return False
        return True

    def revocar(self, usuario_id: str, motivo: str, anomalo: bool = False) -> None:
        cuenta = self.cuentas.obtener(usuario_id)
        if not cuenta or cuenta["estado"] == "revocada":
            return
        try:
            token = self.cifrador.descifrar(cuenta["token_cifrado"])
            self.adaptadores.correo.obtener(cuenta["proveedor"]).revocar(token)
        finally:
            self.cuentas.cambiar_estado(usuario_id, "revocada")
        self.auditoria.registrar(
            "sistema" if anomalo else usuario_id, "correo.revocar", f"correo:{cuenta['direccion']}",
            "anomalia" if anomalo else "solicitado", motivo,
        )
        if anomalo:
            self.notificaciones.notificar(
                f"usuario:{usuario_id}", "seguridad",
                f"Detectamos un uso sospechoso del acceso a {cuenta['direccion']} y lo revocamos. "
                "Volvé a vincular tu casilla cuando quieras.",
            )
            self.notificaciones.notificar("operaciones", "seguridad.correo", f"{motivo} (usuario {usuario_id})")
