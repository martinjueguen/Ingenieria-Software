# 0014. Almacén analítico (OLAP) segregado con sincronización asíncrona

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 4
* Drivers: US-07, QA-R2

## Contexto y problema

El equipo de datos necesita ejecutar consultas pesadas de tendencias, destinos, cancelaciones y estacionalidad sobre millones de registros históricos para monetizarlas (US-07). Ejecutarlas sobre la base transaccional provocaría saturación de conexiones y contención de CPU y disco, degradando los 800 ms de respuesta web (QA-R2) para los usuarios activos. En la Iteración 1 ya se decidió separar el procesamiento analítico de la persistencia operativa; aquí se concreta.

## Factores de decisión (drivers)

* **US-07:** analítica de datos y monetización.
* **QA-R2:** la analítica no debe degradar la latencia web.

## Opciones consideradas

1. Almacén de datos analítico (Data Warehouse, OLAP) segregado, alimentado por replicación asíncrona.
2. No aplicar la táctica: ejecutar las consultas analíticas sobre la base transaccional (OLTP).

## Decisión

Opción elegida: "Almacén analítico segregado con sincronización asíncrona", porque aislar las cargas analíticas en un almacén dedicado evita la contención con la base transaccional y garantiza que la monetización no degrade las operaciones interactivas.

Un exportador analítico asíncrono, desacoplado, toma los eventos de cambios de viajes y reservas y los consolida en el almacén (columnar, optimizado para agregaciones). El equipo de datos consulta exclusivamente contra ese almacén.

### Tácticas aplicadas

* Mantener múltiples copias de datos (*Maintain multiple copies of data*).
* Gestionar el tamaño de las tareas (*Manage work sizes / Resource allocation*).

### Consecuencias

* Positivas: aislamiento de rendimiento; modelado especializado para reportes históricos.
* Negativas: consistencia eventual en la reportería (los viajes tardan minutos en estar disponibles para analítica).

## Pros y contras de las opciones

### Opción 1: OLAP segregado

* Bueno, porque las consultas largas no bloquean las tablas de los usuarios.
* Bueno, porque los datos se modelan para agregación.
* Malo, porque los reportes no reflejan el instante exacto.

### Opción 2: Analítica sobre OLTP

* Bueno, porque los datos siempre están al día y no hay pipeline adicional.
* Malo, porque los escaneos masivos compiten con las transacciones web y comprometen QA-R2.

## Implementación en el prototipo

* Almacén analítico: `trotamundos/datos/almacen_analitico.py`; base operativa: `trotamundos/datos/base_datos.py`.
* Exportador asíncrono (consumidor de eventos de cambios): `trotamundos/asincrono/consumidores.py`.
* Endpoint de consultas analíticas: `trotamundos/api/rutas_analitica.py`.
* Contratos de eventos: `specs/eventos/*.schema.json`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces; el almacén analítico es una base SQLite separada de la operativa. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 4](../add/ADD-Iteración-4.md)
* [ADD Iteración 1](../add/ADD-Iteración-1.md) (decisión de separar analítica y persistencia operativa)
* Relacionados: [ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md), [ADR 0004](0004-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md)
