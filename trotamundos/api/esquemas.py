"""Esquemas (DTO) del contrato REST — parte de la especificación `specs/openapi.json`.

ADD It.2 "API / Acceso al sistema": valida la estructura de las solicitudes y
evita que los clientes dependan de la implementación interna. Las fechas viajan
siempre en UTC ISO-8601 (ADR-0016).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from trotamundos.dominio.modelo import Reserva, Ubicacion, Viaje
from trotamundos.gestion_viajes.servicio_itinerarios import ItinerarioConsolidado


class UbicacionDTO(BaseModel):
    nombre: str
    ciudad: str = ""
    pais: str = ""
    lat: float | None = None
    lon: float | None = None

    def a_dominio(self) -> Ubicacion:
        return Ubicacion(**self.model_dump())


class Credenciales(BaseModel):
    email: str
    clave: str


class Sesion(BaseModel):
    token: str
    usuario: "Perfil"


class Perfil(BaseModel):
    id: str
    email: str
    nombre: str
    rol: str
    idioma: str
    zona_horaria: str
    moneda: str
    agencia_preferida: str | None = None


class CambioPerfil(BaseModel):
    idioma: str | None = None
    zona_horaria: str | None = None
    moneda: str | None = Field(default=None, min_length=3, max_length=3)
    agencia_preferida: str | None = None


class ReservaDTO(BaseModel):
    id: str
    viaje_id: str | None
    tipo: str
    proveedor: str
    codigo_confirmacion: str
    titulo: str
    inicio: datetime
    fin: datetime
    origen: UbicacionDTO | None
    destino: UbicacionDTO
    estado: Literal["confirmada", "modificada", "cancelada"]
    detalles: dict[str, Any]
    fuente: Literal["manual", "correo", "proveedor"]
    sincronizacion: Literal["al_dia", "desactualizada"]
    ultima_actualizacion: datetime

    @classmethod
    def de(cls, r: Reserva) -> "ReservaDTO":
        return cls(
            id=r.id, viaje_id=r.viaje_id, tipo=r.tipo, proveedor=r.proveedor,
            codigo_confirmacion=r.codigo_confirmacion, titulo=r.titulo, inicio=r.inicio, fin=r.fin,
            origen=UbicacionDTO(**r.origen.__dict__) if r.origen else None,
            destino=UbicacionDTO(**r.destino.__dict__), estado=r.estado.value, detalles=r.detalles,
            fuente=r.fuente.value, sincronizacion=r.sincronizacion.value,
            ultima_actualizacion=r.ultima_actualizacion,
        )


class NuevaReserva(BaseModel):
    tipo: str
    proveedor: str = Field(min_length=1)
    codigo_confirmacion: str = Field(min_length=1)
    titulo: str = Field(min_length=1)
    inicio: datetime
    fin: datetime
    destino: UbicacionDTO
    origen: UbicacionDTO | None = None
    detalles: dict[str, Any] = Field(default_factory=dict)
    viaje_id: str | None = None


class CambioReserva(BaseModel):
    titulo: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    destino: UbicacionDTO | None = None
    origen: UbicacionDTO | None = None
    detalles: dict[str, Any] | None = None
    estado: Literal["confirmada", "modificada", "cancelada"] | None = None
    viaje_id: str | None = None


class ViajeDTO(BaseModel):
    id: str
    nombre: str
    destino: str
    inicio: datetime
    fin: datetime
    estado: Literal["planificado", "en_curso", "finalizado", "archivado"]
    es_propietario: bool = True
    reservas: list[ReservaDTO]

    @classmethod
    def de(cls, it: ItinerarioConsolidado, es_propietario: bool = True) -> "ViajeDTO":
        v: Viaje = it.viaje
        return cls(id=v.id, nombre=v.nombre, destino=v.destino, inicio=v.inicio, fin=v.fin,
                   estado=v.estado.value, es_propietario=es_propietario,
                   reservas=[ReservaDTO.de(r) for r in it.reservas])


class CambioViaje(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)


class ResumenMovil(BaseModel):
    """Contrato ligero del primer despliegue móvil (ADR-0005, QA-R3)."""

    proximo: "TramoResumido | None"
    viajes_activos: int


class TramoResumido(BaseModel):
    viaje_id: str
    viaje: str
    reserva_id: str
    tipo: str
    titulo: str
    codigo: str
    inicio: datetime
    estado: str
    sincronizacion: str
    destino: str
    lat: float | None
    lon: float | None
    detalle: str | None = Field(default=None, description="Puerta, asiento o habitación si se conoce")


class VinculoCorreo(BaseModel):
    proveedor: str = "gmail"
    direccion: str

    @field_validator("direccion")
    @classmethod
    def _email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("dirección de correo inválida")
        return v.lower()


class EntradaWhitelist(BaseModel):
    remitente: str = Field(min_length=3, description="Dirección exacta o dominio (ej. aerolinea.com)")


class SolicitudSoporte(BaseModel):
    motivo: Literal["cancelacion", "retraso", "cambio", "reembolso", "otro"]
    descripcion: str = Field(min_length=1, max_length=2000)
    reservas_afectadas: list[str] = Field(default_factory=list)


class Comparticion(BaseModel):
    email: str = Field(pattern=r"^[^@ ]+@[^@ ]+\.[^@ ]+$", description="Persona designada")


class Publicacion(BaseModel):
    red: str = "redsocial"
    mensaje: str = "¡Mirá mi próximo viaje!"


Sesion.model_rebuild()
ResumenMovil.model_rebuild()


# --------------------------------------------------------------------------- #
# Sistema de Recomendación (ADD It.5)                                          #
# --------------------------------------------------------------------------- #


class OfertaDTO(BaseModel):
    proveedor: str
    tipo: str
    titulo: str
    inicio: datetime
    fin: datetime
    origen: UbicacionDTO | None
    destino: UbicacionDTO
    precio_usd: float
    atributos: dict[str, Any]


class RecomendacionDTO(BaseModel):
    id: str
    puntaje: float
    caracteristicas: dict[str, float] = Field(description="Valores 0..1 de precio, comodidad, cercania, "
                                                          "popularidad y afinidad")
    explicacion: list[str] = Field(description="Claves i18n de las razones principales")
    oferta: OfertaDTO

    @classmethod
    def de(cls, r: Any) -> "RecomendacionDTO":
        o = r.oferta
        return cls(id=r.id, puntaje=r.puntaje, caracteristicas=r.caracteristicas, explicacion=r.explicacion,
                   oferta=OfertaDTO(proveedor=o.proveedor, tipo=o.tipo, titulo=o.titulo, inicio=o.inicio, fin=o.fin,
                                    origen=UbicacionDTO(**o.origen.__dict__) if o.origen else None,
                                    destino=UbicacionDTO(**o.destino.__dict__), precio_usd=o.precio,
                                    atributos=o.atributos))


class GrupoRecomendaciones(BaseModel):
    grupo: str
    viaje_id: str
    motivo: Literal["alojamiento", "transporte", "disrupcion"]
    descripcion: str
    reserva_origen_id: str | None
    sugerencias: list[RecomendacionDTO]


class Rechazo(BaseModel):
    motivo: Literal["precio", "ubicacion", "comodidad", "horario", "otro"] | None = None


class ParametrosRecomendacion(BaseModel):
    presupuesto_max: float | None = Field(default=None, gt=0, description="USD por reserva")
    distancia_max_km: float | None = Field(default=None, gt=0, description="Alojamiento: distancia máxima al centro")
    categoria_minima: int | None = Field(default=None, ge=1, le=5, description="Alojamiento: estrellas mínimas")
    transporte_preferido: Literal["tren", "vuelo", "autobus"] | None = None


class PreferenciasRecomendacion(BaseModel):
    parametros: ParametrosRecomendacion
    pesos: dict[str, float] = Field(description="Pesos aprendidos de las decisiones del viajero")
