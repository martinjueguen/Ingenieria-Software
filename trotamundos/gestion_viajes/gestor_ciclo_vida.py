"""Gestor de Ciclo de Vida — submódulo de "Gestión de viajes y reservas".

ADD It.2, Conceptos 1 y 4 (ADR-0003, ADR-0006), US-05: gestiona los estados
del viaje (planificado → en curso → finalizado → archivado). Lo ejecuta el
planificador como proceso periódico en segundo plano (*Schedule resources*),
nunca dentro de una solicitud interactiva (protege QA-R2).
"""

from __future__ import annotations

from datetime import datetime

from trotamundos.datos.cache import GestorCache
from trotamundos.datos.repositorios import RepositorioViajes
from trotamundos.dominio.modelo import EstadoViaje, ahora_utc, estado_por_fechas


class GestorCicloVida:
    def __init__(self, viajes: RepositorioViajes, cache: GestorCache) -> None:
        self.viajes = viajes
        self.cache = cache
        self.ultima_ejecucion: str | None = None

    def ejecutar(self, momento: datetime | None = None) -> dict[str, int]:
        momento = momento or ahora_utc()
        resultado = {"revisados": 0, "archivados": 0, "actualizados": 0}
        usuarios_afectados: set[str] = set()
        for viaje in self.viajes.no_archivados():
            resultado["revisados"] += 1
            nuevo = estado_por_fechas(viaje.inicio, viaje.fin, momento)
            if nuevo == EstadoViaje.FINALIZADO:
                nuevo = EstadoViaje.ARCHIVADO
                resultado["archivados"] += 1
            elif nuevo != viaje.estado:
                resultado["actualizados"] += 1
            if nuevo != viaje.estado:
                self.viajes.guardar(viaje.con(estado=nuevo))
                usuarios_afectados.add(viaje.usuario_id)
        for usuario_id in usuarios_afectados:
            self.cache.invalidar_usuario(usuario_id)
        self.ultima_ejecucion = momento.isoformat()
        return resultado
