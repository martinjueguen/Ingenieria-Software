"""Adaptador de redes sociales para compartir itinerarios (QA-I2).

Lo que se publica es solo un enlace al itinerario: para verlo, el destinatario
debe autenticarse y figurar en la lista de personas designadas (QA-S1,
ADR-0015). La red social nunca recibe datos del viaje.
"""

from __future__ import annotations

from trotamundos.integracion.puertos import AdaptadorRedSocial
from trotamundos.integracion.simuladores import SimuladorRedSocial


class AdaptadorRedSocialEstandar(AdaptadorRedSocial):
    def __init__(self, api: SimuladorRedSocial) -> None:
        self.codigo = api.codigo
        self.api = api

    def publicar(self, token_usuario: str, mensaje: str, enlace: str) -> str:
        return self.api.publicar(token_usuario, mensaje, enlace)
