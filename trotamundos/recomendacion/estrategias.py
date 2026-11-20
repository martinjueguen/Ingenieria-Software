"""Estrategias de puntuación y aprendizaje de preferencias (ADD It.5).

Patrón Strategy: el servicio depende de `EstrategiaPuntuacion`, de modo que el
algoritmo se puede reemplazar (p. ej. por un modelo entrenado) sin tocar el
resto del módulo.

`EstrategiaHibrida` combina:
- contenido: precio, comodidad y cercanía/rapidez de cada oferta;
- popularidad: aceptaciones anonimizadas de otros viajeros (almacén OLAP);
- afinidad: historial propio del viajero (proveedores y tipos que usa).
El puntaje es el promedio ponderado por los pesos aprendidos de ese viajero.

Human-in-the-loop: `actualizar_pesos` ajusta los pesos con cada decisión
(aprendizaje online por preferencias): al aceptar una oferta, ganan peso las
características en las que superaba a las otras del grupo; al rechazarla, lo
pierden. Un motivo de rechazo explícito refuerza la característica indicada.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from trotamundos.integracion.puertos import Oferta
from trotamundos.recomendacion.modelo import CARACTERISTICAS, Parametros

TASA_APRENDIZAJE = 0.6
PESO_MIN, PESO_MAX = 0.05, 5.0
BONO_TRANSPORTE_PREFERIDO = 0.15
MOTIVOS_RECHAZO = {"precio": "precio", "ubicacion": "cercania", "comodidad": "comodidad", "horario": None, "otro": None}
ETIQUETAS = {"precio": "rec.f.precio", "comodidad": "rec.f.comodidad", "cercania": "rec.f.cercania",
             "popularidad": "rec.f.popularidad", "afinidad": "rec.f.afinidad"}


@dataclass
class ContextoUsuario:
    pesos: dict[str, float]
    parametros: Parametros
    proveedores_usados: dict[str, float] = field(default_factory=dict)  # proporción de reservas
    tipos_usados: dict[str, float] = field(default_factory=dict)
    aceptaciones_globales: dict[str, int] = field(default_factory=dict)  # producto → aceptaciones (OLAP)


@dataclass(frozen=True)
class Puntuacion:
    oferta: Oferta
    caracteristicas: dict[str, float]
    puntaje: float
    explicacion: list[str]


class EstrategiaPuntuacion(ABC):
    nombre: str

    @abstractmethod
    def puntuar(self, ofertas: list[Oferta], contexto: ContextoUsuario) -> list[Puntuacion]:
        """Devuelve las ofertas puntuadas, de mayor a menor puntaje."""


def _normalizar_inverso(valor: float, minimo: float, maximo: float) -> float:
    return 0.5 if maximo == minimo else 1 - (valor - minimo) / (maximo - minimo)


class EstrategiaHibrida(EstrategiaPuntuacion):
    nombre = "hibrida-v1"

    def puntuar(self, ofertas: list[Oferta], ctx: ContextoUsuario) -> list[Puntuacion]:
        if not ofertas:
            return []
        precios = [o.precio for o in ofertas]
        duraciones = [o.atributos["duracion_min"] for o in ofertas if "duracion_min" in o.atributos]
        max_acept = max([ctx.aceptaciones_globales.get(o.titulo, 0) for o in ofertas] + [1])
        resultado = []
        for o in ofertas:
            x = {
                "precio": _normalizar_inverso(o.precio, min(precios), max(precios)),
                "comodidad": float(o.atributos.get("comodidad", 0.5)),
                "cercania": self._cercania(o, duraciones),
                "popularidad": ctx.aceptaciones_globales.get(o.titulo, 0) / max_acept,
                "afinidad": 0.6 * ctx.proveedores_usados.get(o.proveedor, 0.0) + 0.4 * ctx.tipos_usados.get(o.tipo, 0.0),
            }
            total_pesos = sum(ctx.pesos[c] for c in CARACTERISTICAS)
            puntaje = sum(ctx.pesos[c] * x[c] for c in CARACTERISTICAS) / total_pesos
            if ctx.parametros.transporte_preferido and o.tipo == ctx.parametros.transporte_preferido:
                puntaje += BONO_TRANSPORTE_PREFERIDO
            aportes = sorted(CARACTERISTICAS, key=lambda c: ctx.pesos[c] * x[c], reverse=True)
            explicacion = [ETIQUETAS[c] for c in aportes[:2] if x[c] >= 0.5]
            resultado.append(Puntuacion(o, {c: round(v, 4) for c, v in x.items()}, round(puntaje, 4), explicacion))
        return sorted(resultado, key=lambda p: p.puntaje, reverse=True)

    @staticmethod
    def _cercania(o: Oferta, duraciones: list[float]) -> float:
        if "distancia_centro_km" in o.atributos:
            return max(0.0, 1 - o.atributos["distancia_centro_km"] / 5)
        if "duracion_min" in o.atributos and duraciones:
            return _normalizar_inverso(o.atributos["duracion_min"], min(duraciones), max(duraciones))
        return 0.5


def actualizar_pesos(pesos: dict[str, float], elegida: dict[str, float], otras: dict[str, float],
                     aceptada: bool, motivo_rechazo: str | None = None) -> dict[str, float]:
    signo = 1 if aceptada else -1
    nuevos = dict(pesos)
    for c in CARACTERISTICAS:
        nuevos[c] += signo * TASA_APRENDIZAJE * (elegida.get(c, 0.5) - otras.get(c, 0.5))
    reforzar = MOTIVOS_RECHAZO.get(motivo_rechazo or "")
    if not aceptada and reforzar:
        nuevos[reforzar] += TASA_APRENDIZAJE
    return {c: round(min(PESO_MAX, max(PESO_MIN, v)), 4) for c, v in nuevos.items()}
