# 0006. Archivado automático mediante proceso programado en segundo plano

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 2
* Drivers: US-05, QA-R2

## Contexto y problema

Los viajes completados deben archivarse o retirarse automáticamente de la vista principal (US-05). Si la regla de archivado se evaluara en el momento en que el usuario abre la aplicación, una petición de lectura pasaría a incluir chequeos y escrituras, agregando procesamiento y bloqueos en el camino crítico que debe responder en ≤ 800 ms (QA-R2).

## Factores de decisión (drivers)

* **US-05:** archivado automático de viajes finalizados.
* **QA-R2:** no penalizar la latencia de las lecturas interactivas.

## Opciones consideradas

1. Proceso periódico programado en segundo plano (*scheduled background job*).
2. No aplicar la táctica: evaluar y archivar durante la petición interactiva del usuario.

## Decisión

Opción elegida: "Proceso programado en segundo plano", porque mantiene las consultas del usuario como lecturas limpias y rápidas y resuelve el archivado por lotes. El Gestor de Ciclo de Vida revisa periódicamente, en momentos de baja carga, los viajes cuya fecha de finalización expiró y actualiza su estado a "Archivado".

### Tácticas aplicadas

* Programar recursos (*Schedule resources*).
* Diferir vinculación / procesamiento (*Defer binding / Asynchronous execution*).

### Consecuencias

* Positivas: no penaliza las consultas interactivas; archivado ordenado por lotes en una única operación periódica.
* Negativas: consistencia temporal leve; puede haber una ventana de pocas horas entre que un viaje finaliza y efectivamente se archiva.

## Pros y contras de las opciones

### Opción 1: Proceso programado

* Bueno, porque separa el mantenimiento del camino crítico de lectura.
* Bueno, porque permite procesar grandes volúmenes de forma controlada.
* Malo, porque introduce una ventana de desfase hasta la próxima ejecución.

### Opción 2: Archivado en la petición

* Bueno, porque el estado se actualiza en el instante en que se consulta.
* Malo, porque agrega escrituras, bloqueos y sobrecarga a cada lectura, comprometiendo QA-R2.

## Implementación en el prototipo

* Regla y transición de estado: `trotamundos/gestion_viajes/gestor_ciclo_vida.py`.
* Estados del viaje: `trotamundos/dominio/modelo.py`.
* Programación periódica: `trotamundos/asincrono/planificador.py`.
* Invalidación de la caché tras archivar: `trotamundos/datos/cache.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces; el planificador corre dentro del mismo proceso. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 2](../add/ADD-Iteración-2.md)
* Relacionados: [ADR 0003](0003-descomponer-gestion-de-viajes-en-reservas-itinerarios-y-ciclo-de-vida.md), [ADR 0004](0004-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md), [ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md)
