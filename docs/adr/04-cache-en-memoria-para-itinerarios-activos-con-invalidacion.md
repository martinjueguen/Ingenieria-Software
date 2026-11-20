# 0004. Caché en memoria para itinerarios activos con invalidación ante modificaciones

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 2
* Drivers: QA-R2, QA-E1, US-04

## Contexto y problema

El panel web debe responder en ≤ 800 ms (QA-R2). Los usuarios consultan sus itinerarios reiteradas veces durante el viaje, mientras que las modificaciones son mucho menos frecuentes. Construir el itinerario implica consultas relacionales con múltiples JOINs sobre la base transaccional, que además debe soportar avalanchas de lecturas ante disrupciones (QA-E1). A su vez, tras una modificación manual (US-04) o una actualización externa el usuario no debe ver datos viejos.

## Factores de decisión (drivers)

* **QA-R2:** latencia web ≤ 800 ms.
* **QA-E1:** amortiguar picos de lectura sobre la base transaccional.
* **US-04:** las modificaciones manuales deben reflejarse de inmediato.

## Opciones consideradas

1. Caché de lectura en memoria para itinerarios activos, con política de invalidación ante modificaciones.
2. No aplicar la táctica: resolver cada lectura contra la base de datos transaccional.

## Decisión

Opción elegida: "Caché en memoria para itinerarios activos con invalidación", porque servir las lecturas desde memoria evita accesos a disco y la ejecución repetida de consultas complejas, garantiza la latencia web y protege a la base transaccional.

Se registran dos decisiones del Paso 5:

* **Incorporar un componente de caché en memoria** entre la capa de aplicación y la base de datos para los itinerarios activos (*cache hit/miss*).
* **Implementar una política de invalidación** que invalida o actualiza la entrada del viaje inmediatamente después de que el usuario crea, edita o elimina una reserva, o de que se recibe una actualización externa, para que las siguientes consultas reflejen los cambios.

### Tácticas aplicadas

* Mantener múltiples copias de datos (*Maintain multiple copies of data / Caching*).
* Reducir la sobrecarga computacional (*Reduce computational overhead*).

### Consecuencias

* Positivas: respuestas del orden de decenas de milisegundos; menor tráfico de lectura concurrente sobre la base transaccional; amortigua lecturas masivas ante contingencias.
* Negativas: exige invalidación rigurosa para no mostrar datos desactualizados; requiere memoria adicional en el servidor o en un servicio dedicado.

## Pros y contras de las opciones

### Opción 1: Caché en memoria con invalidación

* Bueno, porque reduce drásticamente el tiempo de respuesta.
* Bueno, porque alivia la base de datos.
* Malo, porque agrega complejidad de consistencia.
* Malo, porque consume RAM adicional.

### Opción 2: Lectura directa contra la base transaccional

* Bueno, porque no hay riesgo de datos desactualizados ni lógica de invalidación.
* Malo, porque cada consulta ejecuta JOINs complejos y compromete los 800 ms.
* Malo, porque ante picos la carga de lectura recae completa sobre la base operativa.

## Implementación en el prototipo

* Gestor de caché: `trotamundos/datos/cache.py`.
* Lectura con *cache hit/miss*: `trotamundos/gestion_viajes/servicio_itinerarios.py`.
* Invalidación tras modificaciones manuales: `trotamundos/gestion_viajes/servicio_reservas.py`; tras actualizaciones externas: `trotamundos/asincrono/consumidores.py`.
* Persistencia subyacente: `trotamundos/datos/repositorios.py`, `trotamundos/datos/base_datos.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces; la caché es un almacén en memoria del proceso. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 2](../add/ADD-Iteración-2.md)
* Relacionados: [ADR 0003](0003-descomponer-gestion-de-viajes-en-reservas-itinerarios-y-ciclo-de-vida.md), [ADR 0008](0008-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md), [ADR 0013](0013-servicios-sin-estado-con-autoescalado-horizontal.md)
