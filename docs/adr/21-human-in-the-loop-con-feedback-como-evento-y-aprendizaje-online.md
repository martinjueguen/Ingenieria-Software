# 0021. Optimización human-in-the-loop: feedback como evento y aprendizaje online de pesos por viajero

* Estado: aceptado
* Fecha: 2026-11-24
* Iteración ADD: 5
* Drivers: US-08, QA-R4

## Contexto y problema

La Opción A exige un esquema *human-in-the-loop*: el usuario interactúa con las sugerencias, aceptándolas o ajustando parámetros, y esa interacción refina continuamente el modelo. Hay que decidir cómo se captura la interacción y cuándo impacta en el modelo, sin agregar trabajo al camino de la solicitud (QA-R4).

## Factores de decisión (drivers)

* **US-08:** el modelo se refina continuamente con las decisiones del usuario.
* **QA-R4:** el aprendizaje no puede bloquear la interacción.
* El usuario tiene que ver el efecto de su decisión sin esperar al día siguiente.

## Opciones consideradas

1. Solo filtros explícitos configurados por el usuario, sin aprendizaje.
2. Registrar las decisiones y reentrenar el modelo en un batch periódico.
3. Publicar cada decisión como evento y actualizar online los pesos del viajero en un consumidor asíncrono.

## Decisión

Opción elegida: "Feedback como evento y aprendizaje online", porque el efecto se ve en segundos, no bloquea al usuario y el mismo evento sirve para medir la efectividad.

El usuario puede:
* **Aceptar:** se reserva la oferta en el proveedor y se agrega al viaje; las otras sugerencias del grupo se descartan.
* **Rechazar**, opcionalmente con motivo (precio, ubicación, comodidad, horario, otro): no se vuelve a sugerir.
* **Ajustar parámetros:** presupuesto máximo, distancia máxima al centro, categoría mínima, medio de transporte preferido.

Cada decisión se publica como `recomendacion.feedback` (contrato JSON Schema). El consumidor `aprendizaje-recomendaciones` actualiza los pesos: al aceptar, suben las características en las que la elegida superaba al promedio de su grupo; al rechazar, bajan; un motivo explícito refuerza esa característica. Los pesos se acotan entre un mínimo y un máximo. Luego registra el hecho en el almacén analítico y recalcula las sugerencias del viajero.

### Tácticas aplicadas

* Publicar-suscribir con contrato de evento.
* Mantener un modelo del usuario (parámetros explícitos y pesos aprendidos).

### Consecuencias

* Positivas: refinamiento continuo y visible; combina preferencias explícitas e implícitas; la efectividad (tasa de aceptación) queda disponible para el equipo de datos.
* Negativas: con pocas decisiones los pesos pueden oscilar (se mitiga acotándolos).

## Pros y contras de las opciones

### Opción 1: Solo filtros explícitos

* Bueno, porque es predecible.
* Malo, porque no hay aprendizaje y no cumple el refinamiento continuo que pide la Opción A.

### Opción 2: Reentrenamiento batch

* Bueno, porque permite modelos más complejos.
* Malo, porque el usuario no ve el efecto de su decisión hasta el próximo ciclo.

### Opción 3: Evento + aprendizaje online

* Bueno, porque el efecto es inmediato y no bloquea la solicitud.
* Bueno, porque el evento desacopla el aprendizaje de la analítica.
* Malo, porque un aprendizaje incremental simple puede ser ruidoso con pocos datos.

## Implementación en el prototipo

* Decisiones del usuario y publicación del feedback (`aceptar`, `rechazar`, `ajustar`): `trotamundos/recomendacion/servicio.py`.
* Consumidor `al_recibir_feedback`: `trotamundos/recomendacion/servicio.py`.
* Actualización de pesos (`actualizar_pesos`): `trotamundos/recomendacion/estrategias.py`.
* Parámetros explícitos (`Parametros.admite`): `trotamundos/recomendacion/modelo.py`.
* Endpoints: `trotamundos/api/rutas_recomendaciones.py`; pestaña Sugerencias en `trotamundos/web/app.js`.
* Contrato: `specs/eventos/recomendacion.feedback.schema.json`.
* Tests: `tests/test_iteracion5_recomendaciones.py::TestHumanInTheLoop`, `TestAceptar` y `TestCalidad::test_contrato_del_feedback`.

En el prototipo la infraestructura corre en proceso o sobre SQLite, detrás de interfaces ([ADR 0017](17-stack-tecnologico-del-prototipo.md)).

## Enlaces

* [ADD Iteración 5](../add/ADD-Iteración-5.md)
* Relacionados: [ADR 0019](19-modulo-de-recomendacion-con-precalculo-asincrono-dirigido-por-eventos.md), [ADR 0020](20-estrategia-de-puntuacion-intercambiable-con-modelo-hibrido.md), [ADR 0018](18-spec-driven-contratos-openapi-y-json-schema.md)
