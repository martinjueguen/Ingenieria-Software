"""ADD Iteración 4: US-07, QA-D1, QA-E1, QA-S1, QA-U2, CON-3 (ADR-0012 a ADR-0016)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

from fastapi.testclient import TestClient

from tests.conftest import drenar
from trotamundos.app import crear_app
from trotamundos.asincrono.workers import GrupoWorkers
from trotamundos.config import RAIZ
from trotamundos.infraestructura.gestor_trafico import GestorTrafico, Region


class TestQAS1ItinerariosCompartidos:
    def _viaje_de_ana(self, cliente, login) -> str:
        viajes = cliente.get("/api/v1/viajes", headers=login("ana")).json()
        return next(v["id"] for v in viajes if v["nombre"] == "España en familia")

    def test_persona_designada_puede_ver(self, cliente, login):
        viaje_id = self._viaje_de_ana(cliente, login)
        h = login("bruno")
        r = cliente.get(f"/api/v1/viajes/{viaje_id}", headers=h)
        assert r.status_code == 200 and r.json()["es_propietario"] is False
        assert [v["id"] for v in cliente.get("/api/v1/viajes/compartidos", headers=h).json()] == [viaje_id]

    def test_no_designado_bloqueado_y_auditado(self, cliente, login):
        viaje_id = self._viaje_de_ana(cliente, login)
        assert cliente.get(f"/api/v1/viajes/{viaje_id}", headers=login("carla")).status_code == 404
        assert cliente.get(f"/api/v1/viajes/{viaje_id}").status_code == 401  # sin autenticar
        auditoria = cliente.get(f"/api/v1/operaciones/auditoria?recurso=viaje:{viaje_id}&resultado=denegado",
                                headers=login("ops")).json()
        assert any(a["actor"] == "carla@trotamundos.demo" for a in auditoria)

    def test_designado_no_puede_modificar_ni_recompartir(self, cliente, login):
        viaje_id = self._viaje_de_ana(cliente, login)
        h = login("bruno")
        assert cliente.patch(f"/api/v1/viajes/{viaje_id}", json={"nombre": "x"}, headers=h).status_code == 404
        assert cliente.post(f"/api/v1/viajes/{viaje_id}/comparticiones", json={"email": "otro@x.com"},
                            headers=h).status_code == 404

    def test_revocar_designacion(self, cliente, login):
        viaje_id = self._viaje_de_ana(cliente, login)
        cliente.delete(f"/api/v1/viajes/{viaje_id}/comparticiones/bruno@trotamundos.demo", headers=login("ana"))
        assert cliente.get(f"/api/v1/viajes/{viaje_id}", headers=login("bruno")).status_code == 404

    def test_red_social_solo_recibe_un_enlace(self, cliente, sistema, login):
        viaje_id = self._viaje_de_ana(cliente, login)
        r = cliente.post(f"/api/v1/viajes/{viaje_id}/publicar", json={}, headers=login("ana"))
        assert r.status_code == 200
        publicado = sistema.externos.red_social.publicaciones[-1]
        assert viaje_id in publicado["enlace"] and "AS7K2P" not in json.dumps(publicado)


class TestUS07Analitica:
    def test_hechos_anonimizados_en_almacen_separado(self, cliente, sistema, login):
        drenar(sistema)  # exportador analítico asíncrono
        assert sistema.almacen.total_hechos() > 0
        assert sistema.almacen.bd.ruta != sistema.bd.ruta
        ana = sistema.repo_usuarios.por_email("ana@trotamundos.demo")["id"]
        volcado = json.dumps([dict(f) for f in sistema.almacen.bd.consultar("SELECT * FROM hechos_reservas")])
        assert ana not in volcado and "AS7K2P" not in volcado

    def test_consultas_para_el_equipo_de_datos(self, cliente, sistema, login):
        drenar(sistema)
        h = login("datos")
        destinos = cliente.get("/api/v1/analitica/destinos", headers=h).json()
        assert {d["ciudad_destino"] for d in destinos} >= {"Roma", "Cusco", "Madrid"}
        cancel = {c["proveedor"]: c for c in cliente.get("/api/v1/analitica/cancelaciones", headers=h).json()}
        assert cancel["hoteles-plaza"]["cancelaciones"] >= 1
        assert cliente.get("/api/v1/analitica/estacionalidad", headers=h).status_code == 200

    def test_viajero_no_accede_a_analitica(self, cliente, login):
        assert cliente.get("/api/v1/analitica/destinos", headers=login("ana")).status_code == 403


class TestQAE1PicoDeCarga:
    def test_bajo_sobrecarga_se_suspenden_solo_funciones_no_criticas(self, config):
        app = crear_app(replace(config, umbral_carga=0))
        with TestClient(app) as c:
            token = c.post("/api/v1/auth/login",
                           json={"email": "datos@trotamundos.demo", "clave": "demo1234"}).json()["token"]
            h = {"Authorization": f"Bearer {token}"}
            r = c.get("/api/v1/analitica/destinos", headers=h)
            assert r.status_code == 503 and r.headers["Retry-After"]
            assert c.get("/api/v1/viajes", headers=h).status_code == 200  # crítico: sigue atendiendo

    def test_autoescalado_de_workers_segun_longitud_de_cola(self, sistema):
        grupo = GrupoWorkers(sistema.bus, minimo=2, maximo=8, mensajes_por_worker=20)
        assert grupo.deseados(0) == 2
        assert grupo.deseados(100) == 5
        assert grupo.deseados(10_000) == 8


class TestQAD1Multirregion:
    def test_replicacion_sincronica_hacia_la_region_secundaria(self, config, tmp_path):
        replica = tmp_path / "oltp-secundaria.db"
        app = crear_app(replace(config, ruta_replica=str(replica)))
        sistema = app.state.sistema
        assert sistema.replicador.replicaciones > 0
        total_primaria = sistema.bd.consultar_uno("SELECT COUNT(*) AS n FROM reservas")["n"]
        con = sqlite3.connect(replica)
        assert con.execute("SELECT COUNT(*) FROM reservas").fetchone()[0] == total_primaria  # RPO = 0
        con.close()

    def test_geodns_conmuta_tras_heartbeats_fallidos(self, monkeypatch):
        gestor = GestorTrafico([Region("primaria", "http://p"), Region("secundaria", "http://s")], "clave")
        promovidas = []

        class Resp:
            status_code = 200

        def get(url):
            if url.startswith("http://p"):
                raise __import__("httpx").ConnectError("caída")
            return Resp()

        monkeypatch.setattr(gestor._cliente, "get", get)
        monkeypatch.setattr(gestor._cliente, "post", lambda url, headers: promovidas.append(url))
        gestor.heartbeat()
        gestor.heartbeat()
        assert gestor.region_activa.nombre == "primaria"  # todavía no supera el umbral
        gestor.heartbeat()
        assert gestor.region_activa.nombre == "secundaria"
        assert promovidas == ["http://s/api/v1/region/promover"]
        assert gestor.incidentes[0]["region_caida"] == "primaria"

    def test_promover_requiere_clave_de_infraestructura(self, cliente):
        assert cliente.post("/api/v1/region/promover").status_code == 403
        r = cliente.post("/api/v1/region/promover", headers={"X-Clave-Infra": "secreto-solo-para-desarrollo"})
        assert r.status_code == 200 and r.json()["estado"] == "activa"


class TestQAU2Internacionalizacion:
    def test_paquetes_de_idioma_completos(self):
        carpeta = RAIZ / "trotamundos" / "web" / "i18n"
        paquetes = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in carpeta.glob("*.json")}
        assert {"es", "en", "pt"} <= set(paquetes)
        claves = set(paquetes["es"])
        assert all(set(p) == claves for p in paquetes.values())

    def test_preferencias_regionales_por_usuario(self, cliente, login):
        h = login("carla")
        r = cliente.patch("/api/v1/usuarios/yo", json={"idioma": "en", "moneda": "EUR", "zona_horaria": "Asia/Tokyo"},
                          headers=h)
        assert r.json()["idioma"] == "en" and r.json()["moneda"] == "EUR"

    def test_region_identificada_en_cada_respuesta(self, cliente):
        assert cliente.get("/api/v1/salud").headers["X-Region"] == "test"
