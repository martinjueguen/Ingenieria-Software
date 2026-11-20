"""ADD Iteración 3: US-01, US-02, US-03, US-06, QA-R1, QA-I1, QA-I2, QA-S2, QA-D2 (ADR-0007 a ADR-0011)."""

from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import drenar
from trotamundos.dominio.modelo import EstadoReserva, Ubicacion, a_utc
from trotamundos.integracion.proveedores.base import AdaptadorProveedorBase
from trotamundos.integracion.puertos import ActualizacionCanonica
from trotamundos.integracion.simuladores import SimuladorProveedorViajes


def _reservas(cliente, h) -> list[dict]:
    return [r for v in cliente.get("/api/v1/viajes", headers=h).json() for r in v["reservas"]]


@pytest.fixture
def ana_vinculada(cliente, login):
    h = login("ana")
    r = cliente.post("/api/v1/correo/vincular", json={"proveedor": "gmail", "direccion": "ana@gmail.demo"}, headers=h)
    assert r.status_code == 201, r.text
    return h


class TestUS01US02Correo:
    def test_escanea_solo_remitentes_autorizados_y_agrega_la_reserva(self, cliente, sistema, ana_vinculada):
        h = ana_vinculada
        resultado = cliente.post("/api/v1/correo/sondear", headers=h).json()
        assert resultado == {"encolados": 2, "descartados": 1}  # el correo personal se descarta
        drenar(sistema)
        sevilla = [r for r in _reservas(cliente, h) if r["codigo_confirmacion"] == "HP-77310"]
        assert len(sevilla) == 1 and sevilla[0]["fuente"] == "correo"
        # Se integra al viaje existente (agrupación por fechas)
        espana = next(v for v in cliente.get("/api/v1/viajes", headers=h).json() if v["nombre"] == "España en familia")
        assert sevilla[0]["viaje_id"] == espana["id"]

    def test_correo_personal_nunca_se_abre(self, cliente, sistema, ana_vinculada):
        cliente.post("/api/v1/correo/sondear", headers=ana_vinculada)
        casilla = sistema.externos.correo.casillas["ana@gmail.demo"]
        personal = next(m for m in casilla if m.remitente == "amigo@personal.demo")
        assert personal.id not in sistema.externos.correo.lecturas_de_cuerpo

    def test_whitelist_configurable(self, cliente, sistema, ana_vinculada):
        h = ana_vinculada
        cliente.delete("/api/v1/correo/whitelist/hoteles-plaza.demo", headers=h)
        assert cliente.post("/api/v1/correo/sondear", headers=h).json()["descartados"] == 2
        sistema.externos.correo.entregar("ana@gmail.demo", "billetes@trenes-del-sur.demo", "Billete",
                                         "Tipo: tren\nLocalizador: TS-1\nTren: AVE 1\n"
                                         "Hacia: Córdoba | Córdoba | ES\nSalida: 2027-01-10T08:00:00Z")
        cliente.post("/api/v1/correo/whitelist", json={"remitente": "trenes-del-sur.demo"}, headers=h)
        assert cliente.post("/api/v1/correo/sondear", headers=h).json()["encolados"] == 1
        drenar(sistema)
        assert any(r["codigo_confirmacion"] == "TS-1" and r["tipo"] == "tren" for r in _reservas(cliente, h))

    def test_correo_autorizado_sin_reserva_no_genera_error(self, cliente, sistema, ana_vinculada):
        cliente.post("/api/v1/correo/sondear", headers=ana_vinculada)
        drenar(sistema)
        assert sistema.bus.mensajes_muertos() == []


class TestQAS2AccesoAlCorreo:
    def test_token_cifrado_y_solo_lectura(self, cliente, sistema, ana_vinculada):
        cuenta = cliente.get("/api/v1/correo/cuenta", headers=ana_vinculada).json()
        assert cuenta["alcances"] == ["correo.lectura"]
        fila = sistema.bd.consultar_uno("SELECT token_cifrado FROM cuentas_correo")
        token_real = next(iter(sistema.externos.correo.tokens))
        assert token_real.encode() not in fila["token_cifrado"]

    def test_rechaza_proveedor_que_otorga_alcances_de_escritura(self, cliente, sistema, login):
        sistema.externos.correo.otorgar_alcances_extra = True
        r = cliente.post("/api/v1/correo/vincular", json={"direccion": "ana@gmail.demo"}, headers=login("ana"))
        assert r.status_code == 403
        assert sistema.externos.correo.tokens == {}  # el token se revocó

    def test_uso_de_token_robado_se_detecta_revoca_notifica_y_audita(self, cliente, sistema, ana_vinculada, login):
        r = cliente.post("/api/v1/simulacion/correo/uso-token", json={"direccion": "ana@gmail.demo"})
        assert "bloqueado" in r.json()["resultado"]
        assert cliente.get("/api/v1/correo/cuenta", headers=ana_vinculada).json()["estado"] == "revocada"
        assert sistema.externos.correo.tokens == {}
        assert any(n["tipo"] == "seguridad" for n in cliente.get("/api/v1/notificaciones", headers=ana_vinculada).json())
        auditoria = cliente.get("/api/v1/operaciones/auditoria?resultado=anomalia", headers=login("ops")).json()
        assert auditoria and auditoria[0]["accion"] == "correo.revocar"
        # Sin token vigente el escaneo ya no puede leer nada
        assert cliente.post("/api/v1/correo/sondear", headers=ana_vinculada).json() == {"encolados": 0, "descartados": 0}


class TestUS03QAR1ActualizacionesDeProveedores:
    def test_webhook_se_encola_y_se_refleja_en_el_panel(self, cliente, sistema, login):
        h = login("ana")
        sistema.externos.proveedores["aerolineas-sur"].emitir_cambio("AS7K2P", {"status": "DELAYED", "gate": "C7"})
        antes = next(r for r in _reservas(cliente, h) if r["codigo_confirmacion"] == "AS7K2P")
        assert antes["detalles"]["puerta"] == "B12"  # todavía en la cola: el webhook no bloquea
        drenar(sistema)
        despues = next(r for r in _reservas(cliente, h) if r["codigo_confirmacion"] == "AS7K2P")
        assert despues["detalles"]["puerta"] == "C7" and despues["estado"] == "modificada"
        metricas = sistema.reservas.metricas_propagacion()
        assert metricas["muestras"] >= 1 and metricas["cumple"] and metricas["max_s"] < 300

    def test_webhook_http_con_formato_propietario(self, cliente, sistema, login):
        carga = dict(sistema.externos.proveedores["rentacar"].reservas["RC-99812"], status="CANCELLED")
        r = cliente.post("/api/v1/proveedores/rentacar/webhook", json=carga)
        assert r.status_code == 202
        drenar(sistema)
        auto = next(x for x in _reservas(cliente, login("ana")) if x["codigo_confirmacion"] == "RC-99812")
        assert auto["estado"] == "cancelada"

    def test_proveedor_desconocido(self, cliente):
        assert cliente.post("/api/v1/proveedores/nadie/webhook", json={}).status_code == 404


class TestQAD2FallaDeProveedor:
    def test_caida_detectada_panel_operativo_y_reconciliacion(self, cliente, sistema, login):
        h = login("ana")
        hoteles = sistema.externos.proveedores["hoteles-plaza"]
        hoteles.caido = True
        estado = sistema.planificador.ejecutar_ahora("salud-proveedores")  # heartbeat (cada 10 s < 30 s)
        assert estado["hoteles-plaza"] == "caido"
        drenar(sistema)
        r = cliente.get("/api/v1/viajes", headers=h)
        assert r.status_code == 200  # 0 minutos de inactividad del panel
        hotel = next(x for x in _reservas(cliente, h) if x["codigo_confirmacion"] == "HP-55821")
        assert hotel["sincronizacion"] == "desactualizada"  # "última actualización"
        ops = cliente.get("/api/v1/operaciones/notificaciones", headers=login("ops")).json()
        assert any(n["tipo"] == "proveedor.caido" for n in ops)
        # Mientras está caído, el proveedor cambia la reserva; al recuperarse se reconcilia.
        hoteles.reservas["HP-55821"]["room"] = "512"
        hoteles.caido = False
        sistema.planificador.ejecutar_ahora("salud-proveedores")
        drenar(sistema)
        hotel = next(x for x in _reservas(cliente, h) if x["codigo_confirmacion"] == "HP-55821")
        assert hotel["sincronizacion"] == "al_dia" and hotel["detalles"]["habitacion"] == "512"

    def test_sondeo_de_proveedores_sin_fallas_con_los_datos_de_demo(self, sistema):
        drenar(sistema)
        assert sistema.planificador.ejecutar_ahora("sondeo-proveedores")["consultas_encoladas"] > 0
        drenar(sistema)
        assert sistema.bus.mensajes_muertos() == []
        pendientes = sistema.bus.bd.consultar_uno(
            "SELECT COUNT(*) AS n FROM mensajes WHERE cola = 'consultas-proveedores' AND estado != 'hecho'")
        assert pendientes["n"] == 0
        cancelada = sistema.repo_reservas.buscar_por_proveedor("hoteles-plaza", "DEMO-1")[0]
        assert cancelada.estado == EstadoReserva.CANCELADA  # el sondeo no deshace la cancelación

    def test_reintentos_con_backoff_exponencial(self, sistema):
        drenar(sistema)  # vaciar los eventos de la carga inicial
        sistema.bus.backoff_base = 10.0
        sistema.externos.proveedores["trenes-del-sur"].caido = True
        sistema.sincronizador.encolar_consultas("trenes-del-sur")
        assert sistema.bus.procesar_siguiente()
        fila = sistema.bus.bd.consultar_uno(
            "SELECT intentos, estado, disponible_en, ultimo_error FROM mensajes WHERE cola='consultas-proveedores'")
        assert fila["intentos"] == 1 and fila["estado"] == "pendiente" and "503" in fila["ultimo_error"]
        espera = (a_utc(fila["disponible_en"]) - a_utc(sistema.bus.bd.consultar_uno(
            "SELECT creado_en FROM mensajes WHERE cola='consultas-proveedores'")["creado_en"])).total_seconds()
        assert 9 <= espera <= 12


class _AdaptadorAutobus(AdaptadorProveedorBase):
    """Proveedor nuevo escrito solo para el test (QA-I1 / QA-M1)."""

    tipo_reserva = "autobus"

    def _traducir(self, c: dict[str, Any]) -> ActualizacionCanonica:
        return ActualizacionCanonica(
            proveedor=self.codigo, tipo="autobus", codigo_confirmacion=c["boleto"],
            estado=EstadoReserva.CONFIRMADA, titulo=f"Micro a {c['destino']}",
            inicio=a_utc(c["sale"]), fin=a_utc(c["llega"]), destino=Ubicacion(c["destino"], c["destino"], "AR"),
        )


class TestQAI1QAM1NuevoProveedorYMedio:
    def test_agregar_proveedor_de_autobuses_sin_modificar_modulos(self, cliente, sistema, login):
        sim = SimuladorProveedorViajes("micros-andinos")
        sim.reservas["BUS-1"] = {"boleto": "BUS-1", "destino": "Mendoza",
                                 "sale": "2027-03-01T22:00:00Z", "llega": "2027-03-02T10:00:00Z"}
        sistema.adaptadores.proveedores.registrar(_AdaptadorAutobus("micros-andinos", sim))
        h = login("carla")
        usuario = sistema.repo_usuarios.por_email("carla@trotamundos.demo")["id"]
        from trotamundos.dominio.modelo import FuenteReserva
        act = sistema.adaptadores.proveedores.obtener("micros-andinos").consultar_reserva("BUS-1")
        sistema.reservas.aplicar_actualizacion_externa(usuario, act, FuenteReserva.PROVEEDOR)
        assert cliente.post("/api/v1/proveedores/micros-andinos/webhook",
                            json=dict(sim.reservas["BUS-1"], llega="2027-03-02T11:30:00Z")).status_code == 202
        drenar(sistema)
        reserva = _reservas(cliente, h)[0]
        assert reserva["tipo"] == "autobus" and reserva["fin"].startswith("2027-03-02T11:30")


class TestUS06AgenciaPreferida:
    def test_envia_contexto_del_viaje_a_la_agencia(self, cliente, sistema, login):
        h = login("ana")
        viaje = next(v for v in cliente.get("/api/v1/viajes", headers=h).json() if v["nombre"] == "España en familia")
        vuelo = next(r for r in viaje["reservas"] if r["codigo_confirmacion"] == "AS7K2P")
        r = cliente.post(f"/api/v1/viajes/{viaje['id']}/soporte", headers=h, json={
            "motivo": "cancelacion", "descripcion": "Cancelaron mi vuelo", "reservas_afectadas": [vuelo["id"]]})
        assert r.status_code == 201
        caso = sistema.externos.agencias["viajes-pampa"].casos[r.json()["caso"]]
        afectadas = [x["codigo_confirmacion"] for x in caso["reservas"] if x["afectada"]]
        assert afectadas == ["AS7K2P"] and caso["viajero"]["email"] == "ana@trotamundos.demo"

    def test_requiere_agencia_preferida(self, cliente, login):
        h = login("carla")
        cliente.post("/api/v1/reservas", headers=h, json={
            "tipo": "hotel", "proveedor": "x", "codigo_confirmacion": "X1", "titulo": "Hotel",
            "inicio": "2027-01-01T00:00:00Z", "fin": "2027-01-02T00:00:00Z", "destino": {"nombre": "Hotel"}})
        viaje = cliente.get("/api/v1/viajes", headers=h).json()[0]
        r = cliente.post(f"/api/v1/viajes/{viaje['id']}/soporte", headers=h,
                         json={"motivo": "otro", "descripcion": "Ayuda"})
        assert r.status_code == 409
