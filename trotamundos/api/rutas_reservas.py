"""Gestión manual de reservas (US-04) — delega en el Servicio de Reservas."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from trotamundos.api.dependencias import IdentidadDep, SistemaDep
from trotamundos.api.esquemas import CambioReserva, NuevaReserva, ReservaDTO
from trotamundos.dominio.modelo import TIPOS_RESERVA, ErrorDominio, FuenteReserva, Reserva, nuevo_id
from trotamundos.gestion_viajes.servicio_reservas import ReservaNoEncontrada

router = APIRouter(tags=["reservas"])


@router.get("/tipos-reserva", summary="Medios de transporte y servicios soportados (extensible, QA-M1)")
def tipos() -> list[dict]:
    return [{"codigo": t.codigo, "nombre": t.nombre, "campos_requeridos": list(t.campos_requeridos)}
            for t in (TIPOS_RESERVA.obtener(c) for c in TIPOS_RESERVA.codigos())]


@router.post("/reservas", response_model=ReservaDTO, status_code=status.HTTP_201_CREATED,
             summary="Agregar una reserva manualmente")
def crear(datos: NuevaReserva, identidad: IdentidadDep, sistema: SistemaDep) -> ReservaDTO:
    reserva = Reserva(
        id=nuevo_id(), usuario_id=identidad.usuario_id, tipo=datos.tipo, proveedor=datos.proveedor,
        codigo_confirmacion=datos.codigo_confirmacion, titulo=datos.titulo, inicio=datos.inicio, fin=datos.fin,
        destino=datos.destino.a_dominio(), origen=datos.origen.a_dominio() if datos.origen else None,
        detalles=datos.detalles, fuente=FuenteReserva.MANUAL, viaje_id=datos.viaje_id,
    )
    try:
        return ReservaDTO.de(sistema.reservas.crear(reserva))
    except ErrorDominio as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e


@router.get("/reservas/{reserva_id}", response_model=ReservaDTO, summary="Consultar una reserva")
def obtener(reserva_id: str, identidad: IdentidadDep, sistema: SistemaDep) -> ReservaDTO:
    try:
        return ReservaDTO.de(sistema.reservas.obtener(identidad.usuario_id, reserva_id))
    except ReservaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada") from None


@router.patch("/reservas/{reserva_id}", response_model=ReservaDTO, summary="Actualizar una reserva")
def actualizar(reserva_id: str, cambios: CambioReserva, identidad: IdentidadDep, sistema: SistemaDep) -> ReservaDTO:
    datos = cambios.model_dump(exclude_none=True)
    for campo in ("destino", "origen"):
        if campo in datos:
            datos[campo] = getattr(cambios, campo).a_dominio()
    try:
        return ReservaDTO.de(sistema.reservas.actualizar(identidad.usuario_id, reserva_id, datos))
    except ReservaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada") from None
    except ErrorDominio as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e


@router.delete("/reservas/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una reserva")
def eliminar(reserva_id: str, identidad: IdentidadDep, sistema: SistemaDep) -> None:
    try:
        sistema.reservas.eliminar(identidad.usuario_id, reserva_id)
    except ReservaNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada") from None
