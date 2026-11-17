"""Fixtures: cada test levanta una región aislada (bases en un directorio temporal,
sin hilos de fondo: las colas y tareas se ejecutan explícitamente)."""

from __future__ import annotations

import warnings
from dataclasses import replace
from typing import Callable

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi.testclient import TestClient  # noqa: E402

from trotamundos.app import Sistema, crear_app  # noqa: E402
from trotamundos.config import Config  # noqa: E402


@pytest.fixture
def config(tmp_path) -> Config:
    return replace(
        Config(),
        ruta_bd=str(tmp_path / "oltp.db"),
        ruta_bus=str(tmp_path / "bus.db"),
        ruta_olap=str(tmp_path / "olap.db"),
        ruta_replica="",
        procesos_fondo=False,
        datos_demo=True,
        backoff_base_segundos=0.0,
        region="test",
    )


@pytest.fixture
def app(config):
    return crear_app(config)


@pytest.fixture
def sistema(app) -> Sistema:
    return app.state.sistema


@pytest.fixture
def cliente(app) -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def login(cliente) -> Callable[[str], dict[str, str]]:
    def _login(usuario: str) -> dict[str, str]:
        r = cliente.post("/api/v1/auth/login", json={"email": f"{usuario}@trotamundos.demo", "clave": "demo1234"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['token']}"}
    return _login


def drenar(sistema: Sistema) -> int:
    """Simula a los workers: procesa todos los mensajes listos de las colas."""
    return sistema.bus.procesar_pendientes()
