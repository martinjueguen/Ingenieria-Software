"""Nombres de los eventos que circulan por el bus (ADR-0001, ADR-0008).

Cada nombre tiene su contrato en `specs/eventos/<nombre>.schema.json`; el bus
valida todo mensaje publicado contra su contrato (spec-driven, ADR-0018).
"""

# Ingesta de correo: el Servicio de Escaneo publica correos ya filtrados por whitelist
CORREO_RECIBIDO = "correo.recibido"
# Ingesta de proveedores: webhook o sondeo publican la actualización cruda del proveedor
PROVEEDOR_ACTUALIZACION = "proveedor.actualizacion"
# Consulta (sondeo o reintento) a la API de un proveedor; los reintentos usan backoff (ADR-0010)
PROVEEDOR_CONSULTA = "proveedor.consulta"
# Evento de dominio: alta/modificación/cancelación/baja de una reserva
RESERVA_CAMBIADA = "reserva.cambiada"

TODOS = (CORREO_RECIBIDO, PROVEEDOR_ACTUALIZACION, PROVEEDOR_CONSULTA, RESERVA_CAMBIADA)
