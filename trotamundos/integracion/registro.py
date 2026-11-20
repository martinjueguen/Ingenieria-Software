"""Registro de adaptadores de integración (ADR-0007).

Punto único donde se dan de alta los adaptadores. Incorporar un proveedor nuevo
consiste en escribir su adaptador y registrarlo en `app.py`; ningún otro módulo
se modifica (QA-I1 / QA-I2: "0 módulos existentes modificados").
"""

from __future__ import annotations

from typing import Generic, TypeVar

from trotamundos.integracion.puertos import (
    AdaptadorAgencia,
    AdaptadorCatalogo,
    AdaptadorCorreo,
    AdaptadorProveedorViajes,
    AdaptadorRedSocial,
)

T = TypeVar("T")


class ProveedorNoRegistrado(KeyError):
    pass


class _Catalogo(Generic[T]):
    def __init__(self, tipo: str) -> None:
        self._tipo = tipo
        self._items: dict[str, T] = {}

    def registrar(self, adaptador: T) -> None:
        self._items[adaptador.codigo] = adaptador  # type: ignore[attr-defined]

    def obtener(self, codigo: str) -> T:
        try:
            return self._items[codigo]
        except KeyError:
            raise ProveedorNoRegistrado(f"{self._tipo} no registrado: {codigo}") from None

    def codigos(self) -> list[str]:
        return list(self._items)

    def todos(self) -> list[T]:
        return list(self._items.values())


class RegistroAdaptadores:
    def __init__(self) -> None:
        self.proveedores: _Catalogo[AdaptadorProveedorViajes] = _Catalogo("Proveedor de viajes")
        self.correo: _Catalogo[AdaptadorCorreo] = _Catalogo("Proveedor de correo")
        self.agencias: _Catalogo[AdaptadorAgencia] = _Catalogo("Agencia")
        self.redes: _Catalogo[AdaptadorRedSocial] = _Catalogo("Red social")
        # Catálogos de ofertas para el Sistema de Recomendación (ADD It.5)
        self.catalogos: _Catalogo[AdaptadorCatalogo] = _Catalogo("Catálogo de ofertas")
