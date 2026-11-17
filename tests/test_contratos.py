"""Spec-driven (ADR-0018): la implementación respeta los contratos de `specs/`.

- El OpenAPI generado por la API debe coincidir con `specs/openapi.json`.
  Si cambia la API sin actualizar el contrato (o viceversa), este test falla.
  Para actualizar el contrato a propósito: `python -m scripts.exportar_contrato`.
- El bus rechaza cargas que no cumplen el JSON Schema del evento.
"""

from __future__ import annotations

import json

import pytest

from trotamundos.asincrono.bus_eventos import ContratoInvalido
from trotamundos.config import RAIZ
from trotamundos.dominio import eventos


def test_api_coincide_con_el_contrato_openapi(app):
    contrato = json.loads((RAIZ / "specs" / "openapi.json").read_text(encoding="utf-8"))
    generado = json.loads(json.dumps(app.openapi()))
    assert generado["paths"].keys() == contrato["paths"].keys(), "rutas distintas al contrato"
    assert generado == contrato


def test_todo_evento_tiene_contrato(sistema):
    assert set(eventos.TODOS) == set(sistema.bus.temas_con_contrato())


def test_bus_rechaza_carga_que_viola_el_contrato(sistema):
    with pytest.raises(ContratoInvalido, match="codigo_confirmacion"):
        sistema.bus.publicar(eventos.PROVEEDOR_CONSULTA, {"proveedor": "x"})
    with pytest.raises(ContratoInvalido):
        sistema.bus.publicar(eventos.RESERVA_CAMBIADA, {"operacion": "inventada"})


def test_mensaje_que_agota_reintentos_va_a_cola_de_muertos(sistema):
    sistema.bus.procesar_pendientes()
    sistema.bus.max_intentos = 2
    sistema.externos.proveedores["rentacar"].caido = True
    sistema.sincronizador.encolar_consultas("rentacar")
    sistema.bus.procesar_pendientes()
    muertos = sistema.bus.mensajes_muertos()
    assert len(muertos) == 1 and muertos[0]["cola"] == "consultas-proveedores"
    assert any(n["tipo"] == "mensaje.muerto" for n in sistema.notificaciones.de("operaciones"))
