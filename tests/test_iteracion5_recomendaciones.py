"""ADD Iteración 5: Sistema de Recomendación con optimización human-in-the-loop."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from tests.conftest import drenar
from trotamundos.app import crear_app
from trotamundos.asincrono.bus_eventos import ContratoInvalido
from trotamundos.dominio import eventos
from trotamundos.recomendacion.estrategias import EstrategiaPuntuacion, Puntuacion
from trotamundos.recomendacion.modelo import CARACTERISTICAS


def _grupos(cliente, h) -> dict[str, dict]:
    return {g["motivo"] + ":" + g["descripcion"]: g for g in cliente.get("/api/v1/recomendaciones", headers=h).json()}


def _hoteles_sevilla(cliente, h) -> list[dict]:
    return _grupos(cliente, h)["alojamiento:Dónde dormir en Sevilla"]["sugerencias"]


@pytest.fixture
def ana(cliente, login, sistema):
    drenar(sistema)  # el recomendador precalcula a partir de los eventos de la carga inicial
    return login("ana")


class TestPrecalculoDeSugerencias:
    def test_detecta_alojamiento_y_ruta_faltantes(self, cliente, ana):
        grupos = _grupos(cliente, ana)
        assert set(grupos) == {"alojamiento:Dónde dormir en Sevilla", "transporte:Cómo ir de Sevilla a Madrid"}
        transporte = grupos["transporte:Cómo ir de Sevilla a Madrid"]["sugerencias"]
        assert {s["oferta"]["tipo"] for s in transporte} <= {"tren", "vuelo"} and len(transporte) == 3
        assert len({s["oferta"]["titulo"] for s in transporte}) == 3  # diversidad: productos distintos
        hotel = _hoteles_sevilla(cliente, ana)[0]
        assert hotel["explicacion"] and set(hotel["caracteristicas"]) == {
            "precio", "comodidad", "cercania", "popularidad", "afinidad"}

    def test_la_consulta_no_calcula(self, cliente, ana, sistema):
        llamadas = []
        original = sistema.recomendaciones.recalcular_usuario
        sistema.recomendaciones.recalcular_usuario = lambda *a: llamadas.append(a) or original(*a)
        cliente.get("/api/v1/recomendaciones", headers=ana)
        assert llamadas == []  # la lectura usa lo precalculado (QA-R2)

    def test_viaje_completo_no_genera_sugerencias(self, cliente, login, sistema):
        drenar(sistema)
        assert cliente.get("/api/v1/recomendaciones", headers=login("carla")).json() == []


class TestAceptar:
    def test_reserva_en_el_proveedor_y_la_agrega_al_viaje(self, cliente, ana, sistema):
        sugerencia = _hoteles_sevilla(cliente, ana)[0]
        r = cliente.post(f"/api/v1/recomendaciones/{sugerencia['id']}/aceptar", headers=ana)
        assert r.status_code == 201
        reserva = r.json()
        assert reserva["destino"]["ciudad"] == "Sevilla" and reserva["fuente"] == "proveedor"
        espana = next(v for v in cliente.get("/api/v1/viajes", headers=ana).json() if v["nombre"] == "España en familia")
        assert reserva["viaje_id"] == espana["id"]
        # El proveedor la conoce: el sondeo/reconciliación funciona sobre ella
        assert reserva["codigo_confirmacion"] in sistema.externos.proveedores["hoteles-plaza"].reservas
        drenar(sistema)
        assert "alojamiento:Dónde dormir en Sevilla" not in _grupos(cliente, ana)  # necesidad cubierta
        assert cliente.post(f"/api/v1/recomendaciones/{sugerencia['id']}/aceptar", headers=ana).status_code == 404

    def test_catalogo_caido_al_aceptar_responde_503(self, cliente, ana, sistema):
        sugerencia = _hoteles_sevilla(cliente, ana)[0]
        sistema.externos.proveedores["hoteles-plaza"].caido = True
        r = cliente.post(f"/api/v1/recomendaciones/{sugerencia['id']}/aceptar", headers=ana)
        assert r.status_code == 503


class TestHumanInTheLoop:
    def test_rechazo_por_precio_cambia_el_orden(self, cliente, ana, sistema):
        antes = _hoteles_sevilla(cliente, ana)
        assert [s["oferta"]["titulo"] for s in antes] == [
            "Hotel Plaza Sevilla", "Plaza Gran Sevilla", "Plaza Express Sevilla"]
        r = cliente.post(f"/api/v1/recomendaciones/{antes[0]['id']}/rechazar", json={"motivo": "precio"}, headers=ana)
        assert r.status_code == 204
        drenar(sistema)  # aprendizaje asíncrono
        pesos = cliente.get("/api/v1/recomendaciones/preferencias", headers=ana).json()["pesos"]
        assert pesos["precio"] > 1.0  # ahora le importa más el precio
        despues = [s["oferta"]["titulo"] for s in _hoteles_sevilla(cliente, ana)]
        assert despues[0] == "Plaza Express Sevilla"
        assert "Hotel Plaza Sevilla" not in despues  # lo rechazado no se vuelve a sugerir

    def test_aceptar_refuerza_las_caracteristicas_elegidas(self, cliente, ana, sistema):
        lujo = next(s for s in _hoteles_sevilla(cliente, ana) if s["oferta"]["titulo"] == "Plaza Gran Sevilla")
        cliente.post(f"/api/v1/recomendaciones/{lujo['id']}/aceptar", headers=ana)
        drenar(sistema)
        pesos = cliente.get("/api/v1/recomendaciones/preferencias", headers=ana).json()["pesos"]
        assert pesos["comodidad"] > 1.0 and pesos["precio"] < 1.0

    def test_ajuste_explicito_de_parametros(self, cliente, ana, sistema):
        r = cliente.put("/api/v1/recomendaciones/preferencias", headers=ana,
                        json={"categoria_minima": 5, "transporte_preferido": "tren"})
        assert r.status_code == 200 and r.json()["parametros"]["categoria_minima"] == 5
        drenar(sistema)
        assert [s["oferta"]["titulo"] for s in _hoteles_sevilla(cliente, ana)] == ["Plaza Gran Sevilla"]
        transporte = _grupos(cliente, ana)["transporte:Cómo ir de Sevilla a Madrid"]["sugerencias"]
        assert transporte[0]["oferta"]["tipo"] == "tren"

    def test_presupuesto_filtra_ofertas(self, cliente, ana, sistema):
        cliente.put("/api/v1/recomendaciones/preferencias", headers=ana, json={"presupuesto_max": 100})
        drenar(sistema)
        grupos = _grupos(cliente, ana)
        assert "alojamiento:Dónde dormir en Sevilla" not in grupos  # ningún hotel de 4 noches entra en USD 100
        assert all(s["oferta"]["precio_usd"] <= 100 for g in grupos.values() for s in g["sugerencias"])


class TestDisrupcion:
    def test_cancelacion_del_proveedor_propone_alternativas_y_avisa(self, cliente, ana, sistema):
        carga = dict(sistema.externos.proveedores["rentacar"].reservas["RC-99812"], status="CANCELLED")
        cliente.post("/api/v1/proveedores/rentacar/webhook", json=carga)
        drenar(sistema)
        disrupcion = [g for g in cliente.get("/api/v1/recomendaciones", headers=ana).json() if g["motivo"] == "disrupcion"]
        assert len(disrupcion) == 1 and disrupcion[0]["reserva_origen_id"]
        assert all(s["oferta"]["tipo"] == "auto" for s in disrupcion[0]["sugerencias"])
        notificaciones = cliente.get("/api/v1/notificaciones", headers=ana).json()
        assert any(n["tipo"] == "recomendacion.disrupcion" for n in notificaciones)
        # Al aceptar una alternativa la disrupción queda resuelta
        cliente.post(f"/api/v1/recomendaciones/{disrupcion[0]['sugerencias'][0]['id']}/aceptar", headers=ana)
        drenar(sistema)
        assert not any(g["motivo"] == "disrupcion" for g in cliente.get("/api/v1/recomendaciones", headers=ana).json())


class TestCalidad:
    def test_catalogo_caido_no_impide_sugerir_con_los_demas(self, cliente, ana, sistema):
        sistema.externos.proveedores["trenes-del-sur"].caido = True
        cliente.post("/api/v1/recomendaciones/actualizar", headers=ana)
        drenar(sistema)
        transporte = _grupos(cliente, ana)["transporte:Cómo ir de Sevilla a Madrid"]["sugerencias"]
        assert transporte and all(s["oferta"]["tipo"] == "vuelo" for s in transporte)
        assert sistema.bus.mensajes_muertos() == []

    def test_funcion_no_critica_bajo_sobrecarga(self, config):
        with TestClient(crear_app(replace(config, umbral_carga=0))) as c:
            token = c.post("/api/v1/auth/login", json={"email": "ana@trotamundos.demo", "clave": "demo1234"}).json()
            h = {"Authorization": f"Bearer {token['token']}"}
            assert c.get("/api/v1/recomendaciones", headers=h).status_code == 503
            assert c.get("/api/v1/viajes", headers=h).status_code == 200

    def test_feedback_anonimizado_en_olap(self, cliente, ana, sistema, login):
        s = _hoteles_sevilla(cliente, ana)[0]
        cliente.post(f"/api/v1/recomendaciones/{s['id']}/rechazar", json={}, headers=ana)
        drenar(sistema)
        ana_id = sistema.repo_usuarios.por_email("ana@trotamundos.demo")["id"]
        volcado = json.dumps([dict(f) for f in sistema.almacen.bd.consultar("SELECT * FROM hechos_recomendaciones")])
        assert "rechazada" in volcado and ana_id not in volcado
        efectividad = cliente.get("/api/v1/analitica/recomendaciones", headers=login("datos")).json()
        assert any(e["rechazadas"] >= 1 for e in efectividad)

    def test_contrato_del_feedback(self, sistema):
        with pytest.raises(ContratoInvalido):
            sistema.bus.publicar(eventos.RECOMENDACION_FEEDBACK,
                                 {"usuario_id": "u", "accion": "aceptada", "momento": "2026-01-01T00:00:00Z"})

    def test_solo_el_dueno_decide_sobre_sus_sugerencias(self, cliente, ana, login):
        s = _hoteles_sevilla(cliente, ana)[0]
        assert cliente.post(f"/api/v1/recomendaciones/{s['id']}/aceptar", headers=login("carla")).status_code == 404

    def test_estrategia_de_puntuacion_reemplazable(self, cliente, ana, sistema):
        """QA-M2: otro algoritmo se enchufa sin modificar el servicio ni la API (ADR 0020)."""

        class MasBarataPrimero(EstrategiaPuntuacion):
            nombre = "mas-barata-primero"

            def puntuar(self, ofertas, contexto):
                neutro = {c: 0.5 for c in CARACTERISTICAS}
                return [Puntuacion(o, neutro, -o.precio, []) for o in sorted(ofertas, key=lambda o: o.precio)]

        sistema.recomendaciones.estrategia = MasBarataPrimero()
        cliente.post("/api/v1/recomendaciones/actualizar", headers=ana)
        drenar(sistema)
        precios = [s["oferta"]["precio_usd"] for s in _hoteles_sevilla(cliente, ana)]
        assert len(precios) == 3 and precios == sorted(precios)
