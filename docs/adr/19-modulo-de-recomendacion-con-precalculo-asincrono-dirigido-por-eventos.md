# 0019. Módulo de recomendación en la Capa 2 con precálculo asíncrono dirigido por eventos

* Estado: aceptado
* Fecha: 2026-11-24
* Iteración ADD: 5
* Drivers: US-08, QA-R4, QA-R2, QA-R1

## Contexto y problema

La 2da entrega incorpora un Sistema de Recomendación (US-08) que sugiere alojamiento, transporte o rutas para lo que le falta a cada viaje. Generar una sugerencia implica analizar el itinerario, consultar los catálogos de varios proveedores externos y puntuar las ofertas. Si ese trabajo se hace cuando el usuario abre las sugerencias, la respuesta depende de la latencia de terceros y pone en riesgo los 800 ms del panel (QA-R2, QA-R4). A la vez, ante una cancelación durante el viaje, las alternativas tienen que aparecer pronto.

## Factores de decisión (drivers)

* **QA-R4:** 0 cálculos en el camino de la solicitud; sugerencias actualizadas ≤ 5 min después de un cambio.
* **QA-R2:** la nueva funcionalidad no puede degradar los 800 ms del panel.
* **US-08:** sugerencias proactivas y ante disrupciones.

## Opciones consideradas

1. Calcular las sugerencias en línea en cada solicitud.
2. Calcularlas en un proceso batch nocturno.
3. Precalcularlas de forma asíncrona cada vez que cambia el viaje (eventos), más un recálculo periódico.

## Decisión

Opción elegida: "Precálculo asíncrono dirigido por eventos", porque mantiene la consulta como una lectura simple, reutiliza el bus de eventos y los *workers* elásticos (ADR 0008, ADR 0013) y reacciona en minutos a una cancelación.

El Servicio de Recomendaciones se suscribe a `reserva.cambiada` y a `recomendacion.solicitada` (pedido del usuario o del planificador). El consumidor detecta las necesidades del viaje, busca ofertas, las puntúa (ADR 0020) y guarda las sugerencias ordenadas en la base operacional. La API solo las lee.

### Tácticas aplicadas

* Introducir concurrencia / procesamiento asíncrono.
* Mantener múltiples copias de los cómputos (resultado precalculado).
* Política de planificación (recálculo proactivo periódico).

### Consecuencias

* Positivas: la consulta de sugerencias no depende de terceros; las disrupciones generan alternativas y una notificación sin intervención del usuario.
* Negativas: consistencia eventual (segundos) tras un cambio; se guardan sugerencias que quizás no se miren.

## Pros y contras de las opciones

### Opción 1: Cálculo en línea

* Bueno, porque siempre está actualizado y no ocupa almacenamiento.
* Malo, porque la latencia y las caídas de los catálogos externos llegan directamente al usuario, incumpliendo QA-R4 y QA-R2.

### Opción 2: Batch nocturno

* Bueno, porque es barato y simple.
* Malo, porque no reacciona a cambios durante el día: una cancelación en pleno viaje no tendría alternativas hasta el día siguiente.

### Opción 3: Precálculo asíncrono por eventos

* Bueno, porque la consulta es una lectura y el cálculo escala con los *workers*.
* Bueno, porque reacciona a cada cambio del viaje.
* Malo, porque agrega consistencia eventual y almacenamiento.

## Implementación en el prototipo

* Servicio y consumidores (`al_cambiar_reserva`, `al_solicitar`): `trotamundos/recomendacion/servicio.py`.
* Detección de necesidades (alojamiento, ruta, disrupción): `trotamundos/recomendacion/generador.py`.
* Suscripciones al bus y tarea periódica `recomendaciones-proactivas`: `trotamundos/app.py`; período en `trotamundos/config.py`.
* Persistencia de sugerencias: `trotamundos/recomendacion/repositorio.py`.
* Contrato del evento: `specs/eventos/recomendacion.solicitada.schema.json`.
* Tests: `tests/test_iteracion5_recomendaciones.py::TestPrecalculoDeSugerencias` (incluye `test_la_consulta_no_calcula`) y `TestDisrupcion`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 5](../add/ADD-Iteración-5.md)
* Relacionados: [ADR 0001](01-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md), [ADR 0008](08-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md), [ADR 0020](20-estrategia-de-puntuacion-intercambiable-con-modelo-hibrido.md), [ADR 0021](21-human-in-the-loop-con-feedback-como-evento-y-aprendizaje-online.md)
