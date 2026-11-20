"""Datos de demostración del prototipo.

Siembra los simuladores de sistemas externos (reservas en los proveedores y
correos en la casilla) y, si la base está vacía, crea usuarios y reservas.
Las fechas son relativas al día actual para que la demo siempre tenga viajes
próximos, en curso y finalizados. Credenciales de demo: ver README.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from trotamundos.dominio.modelo import FuenteReserva, Reserva, Ubicacion, nuevo_id
from trotamundos.seguridad.autenticacion import hashear_clave

if TYPE_CHECKING:
    from trotamundos.app import Sistema

CLAVE_DEMO = "demo1234"
CASILLA_ANA = "ana@gmail.demo"


def _base() -> datetime:
    hoy = datetime.now(timezone.utc)
    return hoy.replace(hour=0, minute=0, second=0, microsecond=0)


def _f(dias: float, hora: int = 0, minuto: int = 0) -> str:
    return (_base() + timedelta(days=dias, hours=hora, minutes=minuto)).isoformat()


EZE = {"iata": "EZE", "city": "Buenos Aires", "country": "AR", "lat": -34.8222, "lon": -58.5358}
MAD = {"iata": "MAD", "city": "Madrid", "country": "ES", "lat": 40.4983, "lon": -3.5676}
BRC = {"iata": "BRC", "city": "Bariloche", "country": "AR", "lat": -41.1512, "lon": -71.1578}


# Reservas de otros viajeros: (ciudad, país, lat, lon, días desde hoy). Alimentan la analítica.
OTROS_VIAJEROS = [
    ("Roma", "IT", 41.9, 12.5, 15), ("Cusco", "PE", -13.53, -71.97, 40), ("Río de Janeiro", "BR", -22.9, -43.2, 60),
    ("Madrid", "ES", 40.42, -3.70, 75), ("Roma", "IT", 41.9, 12.5, 90), ("Cusco", "PE", -13.53, -71.97, 120),
]
CANCELADAS_OTROS_VIAJEROS = {1, 4}


def _proveedor_otro_viajero(i: int) -> str:
    # "otro-hotel" no está integrado: esas reservas son solo manuales y no se sondean.
    return "hoteles-plaza" if i % 2 else "otro-hotel"


def sembrar_simuladores(s: "Sistema") -> None:
    p = s.externos.proveedores
    # Las reservas de otros viajeros con un proveedor integrado también existen en ese
    # proveedor, con el mismo estado: así el sondeo las reconcilia en vez de fallar.
    for i, (ciudad, pais, lat, lon, dias) in enumerate(OTROS_VIAJEROS):
        if _proveedor_otro_viajero(i) != "hoteles-plaza":
            continue
        p["hoteles-plaza"].reservas[f"DEMO-{i}"] = {
            "confirmation_no": f"DEMO-{i}",
            "state": "CANCELED" if i in CANCELADAS_OTROS_VIAJEROS else "BOOKED",
            "hotel": {"name": f"Hotel en {ciudad}", "city": ciudad, "country": pais, "lat": lat, "lon": lon},
            "check_in": _f(dias), "check_out": _f(dias + 4),
        }
    p["aerolineas-sur"].reservas.update({
        "AS7K2P": {"pnr": "AS7K2P", "status": "SCHEDULED", "gate": "B12",
                   "flight": {"number": "AS1234", "from": EZE, "to": MAD,
                              "departure": _f(20, 22), "arrival": _f(21, 14)}},
        "AS9Q1R": {"pnr": "AS9Q1R", "status": "SCHEDULED",
                   "flight": {"number": "AS1235", "from": MAD, "to": EZE,
                              "departure": _f(28, 12), "arrival": _f(28, 21)}},
        "ASBRC1": {"pnr": "ASBRC1", "status": "SCHEDULED",
                   "flight": {"number": "AS800", "from": EZE, "to": BRC,
                              "departure": _f(-30, 9), "arrival": _f(-30, 11)}},
    })
    p["hoteles-plaza"].reservas.update({
        "HP-55821": {"confirmation_no": "HP-55821", "state": "BOOKED", "room": "305",
                     "hotel": {"name": "Hotel Plaza Madrid", "city": "Madrid", "country": "ES",
                               "lat": 40.4203, "lon": -3.7058},
                     "check_in": _f(21, 15), "check_out": _f(24, 10)},
        "HP-77310": {"confirmation_no": "HP-77310", "state": "BOOKED",
                     "hotel": {"name": "Hotel Plaza Sevilla", "city": "Sevilla", "country": "ES",
                               "lat": 37.3891, "lon": -5.9845},
                     "check_in": _f(24, 13), "check_out": _f(28, 8)},
        "HP-10001": {"confirmation_no": "HP-10001", "state": "BOOKED",
                     "hotel": {"name": "Hotel Plaza Bariloche", "city": "Bariloche", "country": "AR",
                               "lat": -41.1335, "lon": -71.3103},
                     "check_in": _f(-30, 14), "check_out": _f(-26, 10)},
    })
    p["rentacar"].reservas.update({
        "RC-99812": {"reservationNumber": "RC-99812", "status": "CONFIRMED", "vehicle": "Fiat 500",
                     "pickup": {"location": "Barajas T4", "city": "Madrid", "country": "ES",
                                "lat": 40.4919, "lon": -3.5934, "datetime": _f(21, 15)},
                     "dropoff": {"location": "Barajas T4", "city": "Madrid", "country": "ES",
                                 "datetime": _f(24, 8)}},
    })
    p["trenes-del-sur"].reservas.update({
        "TS-4471": {"localizador": "TS-4471", "estado": "confirmado", "tren": "AVE 3150",
                    "coche": "4", "asiento": "12A",
                    "salida": {"estacion": "Madrid Atocha", "ciudad": "Madrid", "pais": "ES",
                               "lat": 40.4066, "lon": -3.6892, "hora": _f(24, 9)},
                    "llegada": {"estacion": "Sevilla Santa Justa", "ciudad": "Sevilla", "pais": "ES",
                                "lat": 37.3920, "lon": -5.9750, "hora": _f(24, 11, 40)}},
    })
    correo = s.externos.correo
    if not correo.casillas.get(CASILLA_ANA):
        correo.entregar(CASILLA_ANA, "reservas@hoteles-plaza.demo", "Confirmación de su reserva en Hotel Plaza Sevilla",
                        "Gracias por elegirnos.\n"
                        "Tipo: hotel\n"
                        "Proveedor: hoteles-plaza\n"
                        "Código de reserva: HP-77310\n"
                        "Hotel: Hotel Plaza Sevilla | Sevilla | ES | 37.3891 | -5.9845\n"
                        f"Check-in: {_f(24, 13)}\n"
                        f"Check-out: {_f(28, 8)}\n")
        correo.entregar(CASILLA_ANA, "amigo@personal.demo", "Asado el sábado",
                        "¿Venís el sábado? Traé el vino.")
        correo.entregar(CASILLA_ANA, "promos@aerolineas-sur.demo", "Ofertas de verano",
                        "Volá a Europa con 30% de descuento. ¡Reservá ya!")


def _crear_usuario(s: "Sistema", email: str, nombre: str, rol: str = "viajero", **extra: str) -> str:
    uid = nuevo_id()
    s.repo_usuarios.crear(id=uid, email=email, nombre=nombre, hash_clave=hashear_clave(CLAVE_DEMO), rol=rol, **extra)
    return uid


def cargar_datos_demo(s: "Sistema") -> None:
    if s.repo_usuarios.por_email("ana@trotamundos.demo"):
        return
    ana = _crear_usuario(s, "ana@trotamundos.demo", "Ana Viajera", agencia_preferida="viajes-pampa")
    _crear_usuario(s, "bruno@trotamundos.demo", "Bruno Acompañante", idioma="en", moneda="USD",
                   zona_horaria="Europe/Madrid")
    _crear_usuario(s, "carla@trotamundos.demo", "Carla Curiosa", idioma="pt", moneda="BRL",
                   zona_horaria="America/Sao_Paulo")
    _crear_usuario(s, "datos@trotamundos.demo", "Equipo de Datos", rol="analista")
    _crear_usuario(s, "ops@trotamundos.demo", "Operaciones", rol="operaciones")

    # Reservas de Ana obtenidas de los proveedores (a través de sus adaptadores)
    for proveedor, codigo in [("aerolineas-sur", "AS7K2P"), ("hoteles-plaza", "HP-55821"),
                              ("rentacar", "RC-99812"), ("trenes-del-sur", "TS-4471"),
                              ("aerolineas-sur", "AS9Q1R"), ("aerolineas-sur", "ASBRC1"),
                              ("hoteles-plaza", "HP-10001")]:
        act = s.adaptadores.proveedores.obtener(proveedor).consultar_reserva(codigo)
        s.reservas.aplicar_actualizacion_externa(ana, act, FuenteReserva.PROVEEDOR)
    for remitente in ("aerolineas-sur.demo", "hoteles-plaza.demo"):
        s.repo_whitelist.agregar(ana, remitente)
    madrid = next(v for v in s.repo_viajes.de_usuario(ana) if v.destino == "Madrid")
    s.itinerarios.renombrar(madrid, "España en familia")
    s.repo_comparticiones.agregar(madrid.id, "bruno@trotamundos.demo")

    # Otros viajeros (alimentan la analítica, US-07)
    for i, (ciudad, pais, lat, lon, dias) in enumerate(OTROS_VIAJEROS):
        uid = _crear_usuario(s, f"viajero{i}@trotamundos.demo", f"Viajero {i}")
        r = s.reservas.crear(Reserva(
            id=nuevo_id(), usuario_id=uid, tipo="hotel", proveedor=_proveedor_otro_viajero(i),
            codigo_confirmacion=f"DEMO-{i}", titulo=f"Hotel en {ciudad}",
            inicio=_base() + timedelta(days=dias), fin=_base() + timedelta(days=dias + 4),
            destino=Ubicacion(f"Hotel en {ciudad}", ciudad, pais, lat, lon), fuente=FuenteReserva.MANUAL,
        ))
        if i in CANCELADAS_OTROS_VIAJEROS:
            s.reservas.actualizar(uid, r.id, {"estado": "cancelada"})
