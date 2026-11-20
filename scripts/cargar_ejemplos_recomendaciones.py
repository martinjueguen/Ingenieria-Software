"""Carga viajes de ejemplo para ver el Sistema de Recomendación en acción.

Usa la API REST de un servidor que esté corriendo, así que los datos se
guardan en su base (por defecto, la de `var/`) y pasan por el flujo normal:
cada reserva publica `reserva.cambiada` y el recomendador calcula en segundo
plano. Se puede correr más de una vez: las reservas repetidas se ignoran.

Ejemplos que deja cargados (clave de todos: demo1234):
- ana@trotamundos.demo: con la demo original ya tiene sugerencias (hotel en
  Sevilla y cómo volver de Sevilla a Madrid). Si su "España en familia" quedó
  solo con el auto en Madrid y el hotel en Sevilla, le agrega los vuelos y el tren.
- bruno@trotamundos.demo: viaje a Roma con el vuelo de ida cancelado.
  Sugiere vuelos alternativos (disrupción).
- carla@trotamundos.demo: Río → Barcelona → Córdoba → Madrid → Río.
  Sugiere cómo ir de Barcelona a Madrid (trenes y vuelos), de Córdoba a Madrid
  (solo trenes) y hoteles en Barcelona y Córdoba.

Las reservas usan proveedores no integrados (iberia, renfe, latam, ita), por
eso son manuales y el sondeo de proveedores no las consulta.

Uso:  python -m scripts.cargar_ejemplos_recomendaciones [--url http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

CLAVE = "demo1234"
LUGARES = {
    "Buenos Aires": ("Aeropuerto EZE", "AR", -34.8222, -58.5358),
    "Madrid": ("Aeropuerto MAD", "ES", 40.4983, -3.5676),
    "Madrid Atocha": ("Estación Madrid Atocha", "ES", 40.4066, -3.6892),
    "Sevilla": ("Estación Sevilla Santa Justa", "ES", 37.3920, -5.9750),
    "Roma": ("Aeropuerto FCO", "IT", 41.8003, 12.2389),
    "Río de Janeiro": ("Aeropuerto GIG", "BR", -22.8090, -43.2506),
    "Barcelona": ("Aeropuerto BCN", "ES", 41.2974, 2.0833),
    "Córdoba": ("Estación Córdoba Central", "ES", 37.8882, -4.7794),
}


def lugar(clave: str, ciudad: str | None = None) -> dict[str, Any]:
    nombre, pais, lat, lon = LUGARES[clave]
    return {"nombre": nombre, "ciudad": ciudad or clave, "pais": pais, "lat": lat, "lon": lon}


def tramo(tipo: str, proveedor: str, codigo: str, numero: str, desde: str, hasta: str,
          sale: datetime, horas: float, ciudad_desde: str | None = None, ciudad_hasta: str | None = None) -> dict:
    campo = "numero_vuelo" if tipo == "vuelo" else "numero_tren"
    origen, destino = lugar(desde, ciudad_desde), lugar(hasta, ciudad_hasta)
    return {
        "tipo": tipo, "proveedor": proveedor, "codigo_confirmacion": codigo,
        "titulo": f"{'Vuelo' if tipo == 'vuelo' else 'Tren'} {numero} {origen['ciudad']} → {destino['ciudad']}",
        "inicio": sale.isoformat(), "fin": (sale + timedelta(hours=horas)).isoformat(),
        "origen": origen, "destino": destino, "detalles": {campo: numero},
    }


class Cliente:
    def __init__(self, url: str, email: str) -> None:
        self.http = httpx.Client(base_url=url + "/api/v1", timeout=15)
        r = self.http.post("/auth/login", json={"email": email, "clave": CLAVE})
        r.raise_for_status()
        self.http.headers["Authorization"] = f"Bearer {r.json()['token']}"
        self.email = email

    def _existente(self, codigo: str) -> dict | None:
        viajes = self.http.get("/viajes", params={"incluir_archivados": True}).json()
        return next((r for v in viajes for r in v["reservas"] if r["codigo_confirmacion"] == codigo), None)

    def reservar(self, datos: dict) -> dict | None:
        r = self.http.post("/reservas", json=datos)
        if r.status_code == 422 and "Ya existe" in r.text:
            previa = self._existente(datos["codigo_confirmacion"])
            mismas_fechas = previa and datetime.fromisoformat(previa["inicio"]) == datetime.fromisoformat(datos["inicio"])
            if previa is None or (mismas_fechas and previa["estado"] != "cancelada"):
                print(f"  = {datos['codigo_confirmacion']} ya estaba cargada")
                return None
            self.http.delete(f"/reservas/{previa['id']}").raise_for_status()  # ejemplo viejo: se reemplaza
            r = self.http.post("/reservas", json=datos)
        r.raise_for_status()
        print(f"  + {datos['titulo']} ({datos['codigo_confirmacion']})")
        return r.json()

    def cancelar(self, reserva: dict) -> None:
        self.http.patch(f"/reservas/{reserva['id']}", json={"estado": "cancelada"}).raise_for_status()
        print(f"  x {reserva['titulo']} cancelada")


def _dia(base: datetime, dias: int, hora: int, minuto: int = 0) -> datetime:
    return (base + timedelta(days=dias)).replace(hour=hora, minute=minuto, second=0, microsecond=0)


def ejemplo_ana(url: str) -> None:
    print("ana@trotamundos.demo")
    c = Cliente(url, "ana@trotamundos.demo")
    espana = next((v for v in c.http.get("/viajes").json() if v["nombre"] == "España en familia"), None)
    if espana is None:
        print("  (no tiene 'España en familia'; se omite)")
        return
    auto = next((r for r in espana["reservas"] if r["tipo"] == "auto"), None)
    hotel = next((r for r in espana["reservas"] if r["tipo"] == "hotel" and r["destino"]["ciudad"] == "Sevilla"), None)
    if not auto or not hotel:
        print("  (su viaje es el de la demo original, que ya genera sugerencias; no se agrega nada)")
        return
    llegada_madrid = datetime.fromisoformat(auto["inicio"]) - timedelta(hours=1)
    sale_tren = datetime.fromisoformat(hotel["inicio"]) - timedelta(hours=4)
    sale_vuelta = datetime.fromisoformat(hotel["fin"]) + timedelta(hours=4)
    c.reservar(tramo("vuelo", "iberia", "IB-EJ6844", "IB6844", "Buenos Aires", "Madrid",
                     llegada_madrid - timedelta(hours=12), 12))
    c.reservar(tramo("tren", "renfe", "RF-EJ3150", "AVE 3150", "Madrid Atocha", "Sevilla", sale_tren, 2.7,
                     ciudad_desde="Madrid"))
    c.reservar(tramo("vuelo", "iberia", "IB-EJ6845", "IB6845", "Madrid", "Buenos Aires", sale_vuelta, 13))


def ejemplo_bruno(url: str, base: datetime) -> None:
    print("bruno@trotamundos.demo")
    c = Cliente(url, "bruno@trotamundos.demo")
    ida = c.reservar(tramo("vuelo", "ita", "AZ-EJ0061", "AZ61", "Madrid", "Roma", _dia(base, 30, 10), 2.5))
    c.reservar({
        "tipo": "hotel", "proveedor": "hotel-trastevere", "codigo_confirmacion": "TR-EJ2201",
        "titulo": "Hotel Trastevere", "inicio": _dia(base, 30, 14).isoformat(), "fin": _dia(base, 34, 10).isoformat(),
        "destino": {"nombre": "Hotel Trastevere", "ciudad": "Roma", "pais": "IT", "lat": 41.889, "lon": 12.47},
    })
    c.reservar(tramo("vuelo", "ita", "AZ-EJ0062", "AZ62", "Roma", "Madrid", _dia(base, 34, 15), 2.5))
    if ida:
        c.cancelar(ida)  # la aerolínea canceló el vuelo de ida → disrupción


def ejemplo_carla(url: str, base: datetime) -> None:
    print("carla@trotamundos.demo")
    c = Cliente(url, "carla@trotamundos.demo")
    # Tramos separados por menos de 2 días: así se agrupan en un mismo viaje (regla de la iteración 2).
    c.reservar(tramo("vuelo", "latam", "LA-EJ8070", "LA8070", "Río de Janeiro", "Barcelona", _dia(base, 45, 1), 11))
    c.reservar(tramo("tren", "renfe", "RF-EJ0381", "AVE 381", "Madrid Atocha", "Córdoba", _dia(base, 47, 9), 1.8,
                     ciudad_desde="Madrid"))
    c.reservar(tramo("vuelo", "latam", "LA-EJ8071", "LA8071", "Madrid", "Río de Janeiro", _dia(base, 49, 8), 11))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = datetime.now(timezone.utc)
    try:
        httpx.get(args.url + "/api/v1/salud", timeout=5).raise_for_status()
    except httpx.HTTPError:
        raise SystemExit(f"No hay un servidor de Trotamundos en {args.url}. Levantalo con: python -m trotamundos")
    ejemplo_ana(args.url)
    ejemplo_bruno(args.url, base)
    ejemplo_carla(args.url, base)

    print("\nEsperando a que el recomendador procese los eventos…")
    time.sleep(6)
    for email in ("ana@trotamundos.demo", "bruno@trotamundos.demo", "carla@trotamundos.demo"):
        grupos = Cliente(args.url, email).http.get("/recomendaciones").json()
        print(f"\n{email}: {len(grupos)} grupo(s) de sugerencias")
        for g in grupos:
            print(f"  [{g['motivo']}] {g['descripcion']}")
            for s in g["sugerencias"]:
                o = s["oferta"]
                print(f"      {o['titulo']}  USD {o['precio_usd']:.2f}")


if __name__ == "__main__":
    main()
