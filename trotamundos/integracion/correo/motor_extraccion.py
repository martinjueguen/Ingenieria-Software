"""Motor de extracción y parsing de correos de viaje — Capa 2.

ADD It.3 (ADR-0007, ADR-0008), US-01. Consume los correos filtrados, identifica
códigos de reserva, fechas, números de vuelo/tren y nombres de hotel, y los
convierte al Modelo Canónico.

El prototipo reconoce correos de confirmación con campos "Clave: valor" (el
equivalente a los datos estructurados que las aerolíneas y hoteles incluyen en
sus correos). Ubicaciones con el formato `nombre | ciudad | país | lat | lon`.
"""

from __future__ import annotations

import re
import unicodedata

from trotamundos.dominio.modelo import EstadoReserva, Ubicacion, a_utc
from trotamundos.integracion.puertos import ActualizacionCanonica


class CorreoSinReserva(ValueError):
    """El correo autorizado no contiene una reserva reconocible (no se reintenta)."""


def _normalizar(clave: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


_ALIAS = {
    "codigo_de_reserva": "codigo", "codigo_de_confirmacion": "codigo", "localizador": "codigo",
    "pnr": "codigo", "confirmacion": "codigo",
    "vuelo": "numero_vuelo", "tren": "numero_tren",
    "salida": "inicio", "check_in": "inicio", "retiro": "inicio",
    "llegada": "fin", "check_out": "fin", "devolucion": "fin",
    "desde": "origen", "hacia": "destino", "hotel": "destino", "lugar": "destino",
}

_ESTADOS = {"confirmada": EstadoReserva.CONFIRMADA, "modificada": EstadoReserva.MODIFICADA,
            "cancelada": EstadoReserva.CANCELADA}


def _ubicacion(texto: str) -> Ubicacion:
    partes = [p.strip() for p in texto.split("|")]
    partes += [""] * (5 - len(partes))
    lat = float(partes[3]) if partes[3] else None
    lon = float(partes[4]) if partes[4] else None
    return Ubicacion(partes[0], partes[1], partes[2], lat, lon)


def _campos(cuerpo: str) -> dict[str, str]:
    campos: dict[str, str] = {}
    for linea in cuerpo.splitlines():
        if ":" not in linea:
            continue
        clave, valor = linea.split(":", 1)
        clave = _normalizar(clave)
        campos[_ALIAS.get(clave, clave)] = valor.strip()
    return campos


def proveedor_desde_remitente(remitente: str) -> str:
    dominio = remitente.rsplit("@", 1)[-1]
    return dominio.split(".")[0]


def extraer(remitente: str, asunto: str, cuerpo: str) -> ActualizacionCanonica:
    c = _campos(cuerpo)
    tipo = c.get("tipo", "").lower()
    if not tipo:
        tipo = ("vuelo" if "numero_vuelo" in c else "tren" if "numero_tren" in c
                else "hotel" if "hotel" in _normalizar(asunto) else "")
    if not tipo or "codigo" not in c or "inicio" not in c or "destino" not in c:
        raise CorreoSinReserva("No se encontraron los datos mínimos de una reserva")
    destino = _ubicacion(c["destino"])
    origen = _ubicacion(c["origen"]) if c.get("origen") else None
    inicio = a_utc(c["inicio"])
    fin = a_utc(c["fin"]) if c.get("fin") else inicio
    detalles = {k: c[k] for k in ("numero_vuelo", "numero_tren", "puerta", "habitacion", "asiento", "vehiculo")
                if c.get(k)}
    if tipo == "vuelo":
        titulo = f"Vuelo {c.get('numero_vuelo', '')} → {destino.ciudad or destino.nombre}"
    elif tipo == "tren":
        titulo = f"Tren {c.get('numero_tren', '')} → {destino.ciudad or destino.nombre}"
    else:
        titulo = destino.nombre
    return ActualizacionCanonica(
        proveedor=c.get("proveedor") or proveedor_desde_remitente(remitente),
        tipo=tipo,
        codigo_confirmacion=c["codigo"],
        estado=_ESTADOS.get(c.get("estado", "").lower(), EstadoReserva.CONFIRMADA),
        titulo=c.get("titulo") or titulo.strip(),
        inicio=inicio,
        fin=fin,
        destino=destino,
        origen=origen,
        detalles=detalles,
    )
