# 0008. Colas de mensajería persistentes y trabajadores concurrentes para ingesta

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 3
* Drivers: US-01, QA-R1, QA-E1

## Contexto y problema

Las reservas llegan por webhooks de aerolíneas y por el sondeo periódico de casillas de correo (US-01). El análisis sintáctico de correos y actualizaciones es costoso y debe completarse de forma que el cambio sea visible en la app en ≤ 5 minutos (QA-R1). Ante disrupciones masivas una aerolínea puede emitir miles de actualizaciones en poco tiempo (QA-E1). Procesar cada evento en el acto bloquearía al servidor interactivo y lo expondría a ráfagas.

## Factores de decisión (drivers)

* **US-01:** procesamiento automático de correos.
* **QA-R1:** propagación de actualizaciones en ≤ 5 minutos.
* **QA-E1:** absorber ráfagas sin desbordar la base de datos (favorecido, no seleccionado en esta iteración).

## Opciones consideradas

1. Pipeline de ingesta asíncrona con colas persistentes en el bus de eventos y un grupo de trabajadores concurrentes.
2. No aplicar la táctica: procesar sincrónicamente cada evento al recibirlo.

## Decisión

Opción elegida: "Colas de mensajería persistentes y trabajadores concurrentes", porque desacoplan la recepción del tiempo de procesamiento y permiten ejecutar el parsing y la actualización de viajes en paralelo, de forma controlada, sin comprometer al servidor interactivo.

Flujo: la recepción (webhook o sondeo) deposita el mensaje en una cola persistente; un *worker* del pool lo toma, extrae y normaliza los datos al modelo canónico, el Servicio de Reservas persiste e invalida la caché del viaje.

### Tácticas aplicadas

* Encolar solicitudes (*Queue requests*).
* Introducir concurrencia (*Introduce concurrency*) mediante un *worker pool*.

### Consecuencias

* Positivas: cumplimiento de la ventana de 5 minutos; las colas amortiguan picos y protegen al backend; entrega confiable sin pérdida de mensajes ante caídas.
* Negativas: consistencia eventual; los cambios externos tardan segundos o minutos en reflejarse en la base operativa.

## Pros y contras de las opciones

### Opción 1: Colas persistentes + workers concurrentes

* Bueno, porque el procesamiento paralelo sostiene QA-R1.
* Bueno, porque las colas absorben ráfagas de actualizaciones.
* Malo, porque introduce consistencia eventual.

### Opción 2: Procesamiento sincrónico

* Bueno, porque el cambio se aplica en el momento de recepción.
* Malo, porque el parsing bloquea al receptor, no amortigua picos y un fallo durante el procesamiento puede perder el evento.

## Implementación en el prototipo

* Colas persistentes en SQLite (con reintentos y cola de mensajes muertos): `trotamundos/asincrono/bus_eventos.py`.
* Pool de workers: `trotamundos/asincrono/workers.py`.
* Consumidores de ingesta (aplicar cambios, invalidar caché): `trotamundos/asincrono/consumidores.py`.
* Sondeo de correo: `trotamundos/integracion/correo/servicio_escaneo.py` y `trotamundos/asincrono/planificador.py`; extracción: `trotamundos/integracion/correo/motor_extraccion.py`.
* Recepción de webhooks/correo: `trotamundos/api/rutas_proveedores.py`, `trotamundos/api/rutas_correo.py`.
* Contratos de mensajes: `specs/eventos/*.schema.json`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 3](../add/ADD-Iteración-3.md)
* Relacionados: [ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md), [ADR 0004](0004-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md), [ADR 0007](0007-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md), [ADR 0010](0010-deteccion-de-excepciones-y-reintentos-con-backoff-exponencial.md), [ADR 0013](0013-servicios-sin-estado-con-autoescalado-horizontal.md)
