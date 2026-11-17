"""ADD Iteración 2: US-04, US-05, QA-R2, QA-R3 (ADR-0003 a ADR-0006)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone



def _manual(dias: int, **extra) -> dict:
    inicio = datetime.now(timezone.utc) + timedelta(days=dias)
    base = {
        "tipo": "hotel", "proveedor": "posada-local", "codigo_confirmacion": f"MAN-{dias}",
        "titulo": "Posada", "inicio": inicio.isoformat(), "fin": (inicio + timedelta(days=2)).isoformat(),
        "destino": {"nombre": "Posada del Sol", "ciudad": "Salta", "pais": "AR"},
    }
    base.update(extra)
    return base


class TestUS04GestionManual:
    def test_crear_actualizar_eliminar(self, cliente, login):
        h = login("carla")
        r = cliente.post("/api/v1/reservas", json=_manual(60), headers=h)
        assert r.status_code == 201
        reserva = r.json()
        assert reserva["fuente"] == "manual" and reserva["viaje_id"]

        r = cliente.patch(f"/api/v1/reservas/{reserva['id']}", json={"titulo": "Posada renovada"}, headers=h)
        assert r.status_code == 200
        assert r.json()["titulo"] == "Posada renovada" and r.json()["estado"] == "modificada"

        assert cliente.delete(f"/api/v1/reservas/{reserva['id']}", headers=h).status_code == 204
        assert cliente.get(f"/api/v1/reservas/{reserva['id']}", headers=h).status_code == 404
        # El viaje que quedó sin tramos se elimina
        assert cliente.get("/api/v1/viajes", headers=h).json() == []

    def test_valida_campos_requeridos_por_tipo(self, cliente, login):
        h = login("carla")
        r = cliente.post("/api/v1/reservas", json=_manual(10, tipo="vuelo"), headers=h)
        assert r.status_code == 422 and "numero_vuelo" in r.text

    def test_no_puede_tocar_reservas_ajenas(self, cliente, login, sistema):
        ajena = sistema.repo_reservas.de_usuario(sistema.repo_usuarios.por_email("ana@trotamundos.demo")["id"])[0]
        h = login("carla")
        assert cliente.patch(f"/api/v1/reservas/{ajena.id}", json={"titulo": "x"}, headers=h).status_code == 404
        assert cliente.delete(f"/api/v1/reservas/{ajena.id}", headers=h).status_code == 404


class TestUS05CicloDeVida:
    def test_agrupa_reservas_por_viaje_incluido_el_regreso(self, cliente, login):
        viajes = cliente.get("/api/v1/viajes", headers=login("ana")).json()
        espana = next(v for v in viajes if v["nombre"] == "España en familia")
        codigos = {r["codigo_confirmacion"] for r in espana["reservas"]}
        assert {"AS7K2P", "HP-55821", "RC-99812", "TS-4471", "AS9Q1R"} <= codigos

    def test_proceso_programado_archiva_viajes_finalizados(self, cliente, login, sistema):
        h = login("ana")
        assert any(v["destino"] == "Bariloche" for v in cliente.get("/api/v1/viajes", headers=h).json())
        resultado = sistema.planificador.ejecutar_ahora("archivado-viajes")
        assert resultado["archivados"] == 1
        panel = cliente.get("/api/v1/viajes", headers=h).json()
        assert all(v["destino"] != "Bariloche" for v in panel)
        historial = cliente.get("/api/v1/viajes?incluir_archivados=true", headers=h).json()
        assert any(v["destino"] == "Bariloche" and v["estado"] == "archivado" for v in historial)


class TestQAR2LatenciaWeb:
    def test_panel_servido_desde_cache_e_invalidado_al_modificar(self, cliente, login):
        h = login("ana")
        assert cliente.get("/api/v1/viajes", headers=h).headers["X-Cache"] == "MISS"
        assert cliente.get("/api/v1/viajes", headers=h).headers["X-Cache"] == "HIT"
        reserva = cliente.get("/api/v1/viajes", headers=h).json()[0]["reservas"][0]
        cliente.patch(f"/api/v1/reservas/{reserva['id']}", json={"titulo": "Cambiado"}, headers=h)
        r = cliente.get("/api/v1/viajes", headers=h)
        assert r.headers["X-Cache"] == "MISS"
        assert any(x["titulo"] == "Cambiado" for v in r.json() for x in v["reservas"])

    def test_tiempo_de_respuesta_bajo_800ms(self, cliente, login):
        h = login("ana")
        cliente.get("/api/v1/viajes", headers=h)
        inicio = time.perf_counter()
        for _ in range(20):
            assert cliente.get("/api/v1/viajes", headers=h).status_code == 200
        assert (time.perf_counter() - inicio) / 20 < 0.8


class TestQAR3ResumenMovil:
    def test_resumen_ligero_con_proximo_tramo_y_coordenadas(self, cliente, login):
        h = login("ana")
        r = cliente.get("/api/v1/movil/resumen", headers=h)
        datos = r.json()
        assert r.status_code == 200
        assert len(r.content) < 1024, "el contrato móvil debe ser ligero"
        assert len(r.content) < len(cliente.get("/api/v1/viajes", headers=h).content) / 4
        p = datos["proximo"]
        assert p["codigo"] == "AS7K2P" and p["detalle"] == "Puerta B12"
        assert p["lat"] is not None and p["lon"] is not None  # habilita GPS (QA-U1)

    def test_reservas_y_viajes_usan_utc(self, cliente, login):
        datos = cliente.get("/api/v1/viajes", headers=login("ana")).json()
        fechas = [r["inicio"] for v in datos for r in v["reservas"]]
        assert fechas and all(f.endswith("Z") or f.endswith("+00:00") for f in fechas)
