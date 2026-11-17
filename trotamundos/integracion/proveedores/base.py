"""Base común de adaptadores de proveedores de viajes (ADR-0007, ADR-0010).

Centraliza la *Exception detection*: cualquier falla de comunicación del
sistema externo se traduce a `ErrorProveedor`, que dispara reintentos con
backoff en el procesamiento asíncrono.
"""

from __future__ import annotations

from typing import Any

from trotamundos.integracion.puertos import (
    ActualizacionCanonica,
    AdaptadorProveedorViajes,
    ErrorProveedor,
)
from trotamundos.integracion.simuladores import SimuladorProveedorViajes, SistemaCaido


class AdaptadorProveedorBase(AdaptadorProveedorViajes):
    def __init__(self, codigo: str, api: SimuladorProveedorViajes) -> None:
        self.codigo = codigo
        self.api = api

    def consultar_reserva(self, codigo_confirmacion: str) -> ActualizacionCanonica:
        try:
            registro = self.api.consultar(codigo_confirmacion)
        except (SistemaCaido, TimeoutError, ConnectionError) as e:
            raise ErrorProveedor(str(e)) from e
        except KeyError as e:
            raise ErrorProveedor(f"{self.codigo}: reserva {codigo_confirmacion} inexistente") from e
        return self.traducir_notificacion(registro)

    def disponible(self) -> bool:
        return self.api.ping()

    def traducir_notificacion(self, carga: dict[str, Any]) -> ActualizacionCanonica:
        try:
            return self._traducir(carga)
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Formato inválido de {self.codigo}: {e}") from e

    def _traducir(self, carga: dict[str, Any]) -> ActualizacionCanonica:  # pragma: no cover
        raise NotImplementedError
