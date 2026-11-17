"""Adaptador de correo estilo Gmail API (OAuth estándar) — ADR-0007, ADR-0009.

Agregar Outlook u otro proveedor = otro adaptador que implemente `AdaptadorCorreo`;
el motor de extracción no cambia (QA-I2).
"""

from __future__ import annotations

from trotamundos.dominio.modelo import a_utc
from trotamundos.integracion.puertos import (
    AdaptadorCorreo,
    CorreoCompleto,
    EncabezadoCorreo,
    ErrorProveedor,
)
from trotamundos.integracion.simuladores import SimuladorCorreo, SistemaCaido
from trotamundos.seguridad.gestor_tokens import ORIGEN_LEGITIMO


class AdaptadorGmail(AdaptadorCorreo):
    def __init__(self, api: SimuladorCorreo) -> None:
        self.codigo = api.codigo
        self.api = api

    def autorizar(self, direccion: str, alcances: list[str]) -> tuple[str, list[str]]:
        return self.api.autorizar(direccion, alcances)

    def revocar(self, token: str) -> None:
        self.api.revocar(token)

    def listar_encabezados(self, token: str, direccion: str) -> list[EncabezadoCorreo]:
        try:
            datos = self.api.listar(token, direccion, ORIGEN_LEGITIMO)
        except SistemaCaido as e:
            raise ErrorProveedor(str(e)) from e
        return [EncabezadoCorreo(d["id"], d["from"], a_utc(d["date"])) for d in datos]

    def obtener_correo(self, token: str, direccion: str, mensaje_id: str) -> CorreoCompleto:
        try:
            d = self.api.leer(token, direccion, mensaje_id, ORIGEN_LEGITIMO)
        except SistemaCaido as e:
            raise ErrorProveedor(str(e)) from e
        return CorreoCompleto(d["id"], d["from"], d["subject"], d["body"], a_utc(d["date"]))
