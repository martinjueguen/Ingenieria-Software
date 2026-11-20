"""Simuladores del catálogo de ofertas de los proveedores (sistemas externos).

NO forman parte de Trotamundos. Reemplazan a las APIs de disponibilidad de
hoteles, trenes, aerolíneas y arrendadoras para el prototipo del Sistema de
Recomendación (ADD It.5). Devuelven ofertas en un formato "estándar de
distribución" (camelCase, precios en USD) que el adaptador traduce al formato
canónico. Al reservar una oferta, el simulador registra la reserva en el
sistema del proveedor con su formato propietario, igual que una compra real.
"""

from __future__ import annotations

import hashlib
import math
import secrets
from datetime import datetime, timedelta
from typing import Any

from trotamundos.dominio.modelo import a_utc
from trotamundos.integracion.simuladores import SimuladorProveedorViajes, SistemaCaido

# ciudad: (país, lat, lon, aeropuerto IATA, estación de tren principal)
CIUDADES: dict[str, tuple[str, float, float, str | None, str | None]] = {
    "Buenos Aires": ("AR", -34.6037, -58.3816, "EZE", None),
    "Madrid": ("ES", 40.4168, -3.7038, "MAD", "Madrid Atocha"),
    "Sevilla": ("ES", 37.3891, -5.9845, "SVQ", "Sevilla Santa Justa"),
    "Córdoba": ("ES", 37.8882, -4.7794, None, "Córdoba Central"),
    "Barcelona": ("ES", 41.3874, 2.1686, "BCN", "Barcelona Sants"),
    "Bariloche": ("AR", -41.1335, -71.3103, "BRC", None),
    "Roma": ("IT", 41.9028, 12.4964, "FCO", "Roma Termini"),
    "Cusco": ("PE", -13.5319, -71.9675, "CUZ", None),
    "Río de Janeiro": ("BR", -22.9068, -43.1729, "GIG", None),
}

HOTELES = [  # (marca, estrellas, km al centro, USD por noche)
    ("Plaza Express", 3, 3.5, 70.0),
    ("Hotel Plaza", 4, 1.0, 140.0),
    ("Plaza Gran", 5, 0.4, 260.0),
]
AUTOS = [("Fiat 500", 40.0, 0.5), ("Seat Ibiza", 48.0, 0.6), ("VW Golf", 65.0, 0.8)]  # (modelo, USD/día, comodidad)
SALIDAS_TREN = [(7, 0), (12, 0), (17, 30)]
SALIDAS_VUELO = [(9, 30), (19, 0)]


def km_entre(a: str, b: str) -> float:
    _, la1, lo1, *_ = CIUDADES[a]
    _, la2, lo2, *_ = CIUDADES[b]
    r = math.pi / 180
    x = math.sin((la2 - la1) * r / 2) ** 2 + math.cos(la1 * r) * math.cos(la2 * r) * math.sin((lo2 - lo1) * r / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def _dias(desde: datetime, hasta: datetime) -> list[datetime]:
    dia = desde.replace(hour=0, minute=0, second=0, microsecond=0)
    dias = []
    while dia <= hasta:
        dias.append(dia)
        dia += timedelta(days=1)
    return dias


def _id(*partes: Any) -> str:
    return hashlib.sha1("|".join(map(str, partes)).encode()).hexdigest()[:12]


class SimuladorCatalogo:
    """API de disponibilidad de un proveedor. `tipo`: hotel | tren | vuelo | auto."""

    def __init__(self, tipo: str, sistema_reservas: SimuladorProveedorViajes) -> None:
        self.tipo = tipo
        self.proveedor = sistema_reservas
        self.codigo = sistema_reservas.codigo
        self.ofertas: dict[str, dict[str, Any]] = {}

    def _verificar(self) -> None:
        if self.proveedor.caido:
            raise SistemaCaido(f"{self.codigo}: catálogo no disponible")

    # ---- Búsqueda -------------------------------------------------------- #

    def buscar(self, tipo: str, destino: str, desde: str, hasta: str, origen: str | None = None) -> list[dict[str, Any]]:
        self._verificar()
        if tipo != self.tipo or destino not in CIUDADES:
            return []
        d, h = a_utc(desde), a_utc(hasta)
        generador = {"hotel": self._hoteles, "auto": self._autos, "tren": self._tramos, "vuelo": self._tramos}[tipo]
        ofertas = generador(destino, d, h, origen)
        for o in ofertas:
            self.ofertas[o["offerId"]] = o
        return ofertas

    def _lugar(self, ciudad: str, nombre: str, dlat: float = 0.0) -> dict[str, Any]:
        pais, lat, lon, *_ = CIUDADES[ciudad]
        return {"name": nombre, "city": ciudad, "country": pais, "lat": round(lat + dlat, 5), "lon": lon}

    def _hoteles(self, ciudad: str, desde: datetime, hasta: datetime, _: str | None) -> list[dict[str, Any]]:
        noches = max(1, (hasta.date() - desde.date()).days)
        entrada = desde.replace(hour=14, minute=0, second=0, microsecond=0)
        salida = (entrada + timedelta(days=noches)).replace(hour=10)
        return [{
            "offerId": _id(self.codigo, "hotel", ciudad, marca, entrada.date(), noches),
            "kind": "hotel", "name": f"{marca} {ciudad}", "to": self._lugar(ciudad, f"{marca} {ciudad}", km / 111),
            "start": entrada.isoformat(), "end": salida.isoformat(), "priceUsd": round(tarifa * noches, 2),
            "stars": estrellas, "distanceKm": km, "nights": noches,
        } for marca, estrellas, km, tarifa in HOTELES]

    def _autos(self, ciudad: str, desde: datetime, hasta: datetime, _: str | None) -> list[dict[str, Any]]:
        dias = max(1, math.ceil((hasta - desde).total_seconds() / 86400))
        return [{
            "offerId": _id(self.codigo, "auto", ciudad, modelo, desde.isoformat(), dias),
            "kind": "auto", "name": f"Auto {modelo}", "to": self._lugar(ciudad, f"Oficina {ciudad} centro"),
            "start": desde.isoformat(), "end": (desde + timedelta(days=dias)).isoformat(),
            "priceUsd": round(tarifa * dias, 2), "comfort": comodidad, "vehicle": modelo,
        } for modelo, tarifa, comodidad in AUTOS]

    def _tramos(self, destino: str, desde: datetime, hasta: datetime, origen: str | None) -> list[dict[str, Any]]:
        if not origen or origen not in CIUDADES or origen == destino:
            return []
        es_tren = self.tipo == "tren"
        indice = 4 if es_tren else 3
        if not CIUDADES[origen][indice] or not CIUDADES[destino][indice]:
            return []
        km = km_entre(origen, destino)
        if es_tren and (CIUDADES[origen][0] != CIUDADES[destino][0] or km > 1200):
            return []
        if not es_tren and km < 300:
            return []
        duracion = int(km / 220 * 60 + 20) if es_tren else int(km / 750 * 60 + 45)
        ofertas = []
        for dia in _dias(desde, hasta):
            for hora, minuto in (SALIDAS_TREN if es_tren else SALIDAS_VUELO):
                sale = dia.replace(hour=hora, minute=minuto)
                llega = sale + timedelta(minutes=duracion)
                if sale < desde or llega > hasta:
                    continue
                pico = hora in (7, 17, 19)
                precio = (km * 0.12 + 15) * (1.3 if pico else 1.0) if es_tren else (km * 0.15 + 60) * (1.2 if pico else 1.0)
                numero = f"{'AVE' if es_tren else 'AS'} {2000 + (hora * 60 + minuto) % 997}"
                ofertas.append({
                    "offerId": _id(self.codigo, self.tipo, origen, destino, sale.isoformat()),
                    "kind": self.tipo, "name": f"{'Tren' if es_tren else 'Vuelo'} {numero} {origen} → {destino}",
                    "number": numero,
                    "from": self._lugar(origen, CIUDADES[origen][indice] or origen),
                    "to": self._lugar(destino, CIUDADES[destino][indice] or destino),
                    "start": sale.isoformat(), "end": llega.isoformat(), "priceUsd": round(precio, 2),
                    "durationMin": duracion, "comfort": 0.8 if es_tren else 0.6,
                })
        return ofertas

    # ---- Reserva --------------------------------------------------------- #

    def reservar(self, oferta_id: str, titular: str) -> str:
        """Registra la reserva en el sistema del proveedor, en su formato propietario."""
        self._verificar()
        o = self.ofertas[oferta_id]
        codigo, registro = {
            "hotel": self._registro_hotel, "auto": self._registro_auto,
            "tren": self._registro_tren, "vuelo": self._registro_vuelo,
        }[o["kind"]](o)
        registro["holder"] = titular
        self.proveedor.reservas[codigo] = registro
        return codigo

    @staticmethod
    def _registro_hotel(o: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        codigo = f"HP-{secrets.randbelow(90000) + 10000}"
        t = o["to"]
        return codigo, {"confirmation_no": codigo, "state": "BOOKED", "check_in": o["start"], "check_out": o["end"],
                        "hotel": {"name": o["name"], "city": t["city"], "country": t["country"],
                                  "lat": t["lat"], "lon": t["lon"]}}

    @staticmethod
    def _registro_auto(o: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        codigo = f"RC-{secrets.randbelow(90000) + 10000}"
        t = o["to"]
        lugar = {"location": t["name"], "city": t["city"], "country": t["country"], "lat": t["lat"], "lon": t["lon"]}
        return codigo, {"reservationNumber": codigo, "status": "CONFIRMED", "vehicle": o["vehicle"],
                        "pickup": {**lugar, "datetime": o["start"]}, "dropoff": {**lugar, "datetime": o["end"]}}

    @staticmethod
    def _registro_tren(o: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        codigo = f"TS-{secrets.randbelow(9000) + 1000}"

        def estacion(x: dict[str, Any], hora: str) -> dict[str, Any]:
            return {"estacion": x["name"], "ciudad": x["city"], "pais": x["country"], "lat": x["lat"],
                    "lon": x["lon"], "hora": hora}
        return codigo, {"localizador": codigo, "estado": "confirmado", "tren": o["number"],
                        "salida": estacion(o["from"], o["start"]), "llegada": estacion(o["to"], o["end"])}

    @staticmethod
    def _registro_vuelo(o: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        codigo = "AS" + secrets.token_hex(2).upper()

        def aeropuerto(x: dict[str, Any]) -> dict[str, Any]:
            return {"iata": CIUDADES[x["city"]][3], "city": x["city"], "country": x["country"],
                    "lat": x["lat"], "lon": x["lon"]}
        return codigo, {"pnr": codigo, "status": "SCHEDULED",
                        "flight": {"number": o["number"].replace(" ", ""), "from": aeropuerto(o["from"]),
                                   "to": aeropuerto(o["to"]), "departure": o["start"], "arrival": o["end"]}}
