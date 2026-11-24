# 0024. Privacidad en el aprendizaje de preferencias: historial propio y agregados anonimizados

* Estado: aceptado
* Fecha: 2026-11-24
* Iteración ADD: 5
* Drivers: QA-S3, QA-S1, US-07

## Contexto y problema

Para personalizar, el recomendador usa el historial de viajes, que es información personal. Además conviene usar lo que eligen otros viajeros (popularidad) y el equipo de datos necesita medir la efectividad de las recomendaciones (US-07). Hay que definir qué datos puede usar el modelo, qué llega al almacén analítico y quién puede decidir sobre una sugerencia.

## Factores de decisión (drivers)

* **QA-S3:** 100 % de las decisiones sobre sugerencias ajenas rechazadas y 0 identificadores de usuario en el almacén analítico.
* **QA-S1:** coherencia con el control de acceso a itinerarios.
* **US-07:** analítica sobre datos anonimizados.

## Opciones consideradas

1. Usar el historial completo de todos los usuarios (filtrado colaborativo sobre datos identificados) y guardar el feedback identificado.
2. Usar solo el historial propio del viajero más agregados anonimizados de los demás, y guardar el feedback anonimizado.

## Decisión

Opción elegida: "Historial propio y agregados anonimizados", porque permite personalizar y medir sin exponer a ningún viajero.

* La afinidad se calcula solo con las reservas del propio viajero.
* La popularidad sale de un conteo de viajeros distintos que aceptaron cada producto, tomado del almacén analítico.
* El feedback se guarda en el almacén con el identificador anonimizado (el mismo mecanismo que ADR 0014).
* Cada decisión verifica que la sugerencia pertenezca al usuario autenticado; si no, responde `404` (no revela que existe).

### Tácticas aplicadas

* Autorizar actores.
* Limitar la exposición de datos (anonimización y minimización).

### Consecuencias

* Positivas: personalización sin cruzar datos identificados entre usuarios; la analítica de efectividad cumple la misma política que el resto del OLAP.
* Negativas: se renuncia a técnicas colaborativas más precisas que requieren datos identificados.

## Pros y contras de las opciones

### Opción 1: Datos identificados de todos

* Bueno, porque habilita filtrado colaborativo más preciso.
* Malo, porque expone información personal en el modelo y en la analítica, incumpliendo QA-S3.

### Opción 2: Historial propio + agregados anónimos

* Bueno, porque cumple la privacidad por diseño.
* Malo, porque la personalización es algo menos precisa.

## Implementación en el prototipo

* Contexto del usuario (historial propio y popularidad): `ServicioRecomendaciones._contexto` en `trotamundos/recomendacion/servicio.py`.
* Feedback anonimizado y popularidad: `registrar_feedback`, `aceptaciones_por_producto` y `efectividad_recomendaciones` en `trotamundos/datos/almacen_analitico.py`; endpoint `GET /analitica/recomendaciones`.
* Verificación del dueño: `ServicioRecomendaciones._pendiente`.
* Tests: `tests/test_iteracion5_recomendaciones.py::TestCalidad::test_feedback_anonimizado_en_olap` y `test_solo_el_dueno_decide_sobre_sus_sugerencias`.

En el prototipo la infraestructura corre en proceso o sobre SQLite, detrás de interfaces ([ADR 0017](17-stack-tecnologico-del-prototipo.md)).

## Enlaces

* [ADD Iteración 5](../add/ADD-Iteración-5.md)
* Relacionados: [ADR 0014](14-almacen-analitico-olap-segregado-con-sincronizacion-asincrona.md), [ADR 0015](15-listas-de-control-de-acceso-por-itinerario-y-auditoria.md), [ADR 0020](20-estrategia-de-puntuacion-intercambiable-con-modelo-hibrido.md)
