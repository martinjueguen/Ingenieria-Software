# 0018. Desarrollo guiado por especificaciones: contrato OpenAPI y JSON Schema de eventos verificados por tests

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: transversal (implementación del prototipo)
* Drivers: QA-M1 ("100 % de los cambios trazables a un ADR y a una spec"), QA-I1, QA-I2, consigna del TPE (spec-driven)

## Contexto y problema

La consigna pide un prototipo que respete especificaciones definidas contractualmente. QA-M1 exige trazabilidad de cada cambio a un ADR y a una spec. Los contratos de comunicación del ADD son dos: los conectores REST cliente-servidor (It.1 y 2) y los eventos del bus (It.1 y 3). Ambos tienen que estar escritos y verificados.

## Factores de decisión (drivers)

* Que el contrato sea un artefacto versionado que se revise en cada cambio.
* Que la implementación no pueda divergir del contrato sin que algo falle.
* Que los productores de eventos no puedan publicar mensajes malformados.

## Opciones consideradas

1. Contratos versionados en `specs/` y verificados automáticamente (snapshot OpenAPI + validación JSON Schema en el bus).
2. Documentar los contratos solo en la wiki.
3. Generar el código a partir de un OpenAPI escrito a mano.

## Decisión

Opción elegida: "Contratos versionados y verificados automáticamente":

* **REST:** `specs/openapi.json` es el contrato de `/api/v1`. Los DTO de `trotamundos/api/esquemas.py` son su fuente tipada. `tests/test_contratos.py` compara el OpenAPI que expone la API con el contrato versionado. Un cambio de contrato se hace a propósito (`python -m scripts.exportar_contrato`) y se ve en el diff.
* **Eventos:** cada tema del bus tiene su JSON Schema en `specs/eventos/<tema>.schema.json`. `BusEventos.publicar` valida cada carga y rechaza la que no cumple (`ContratoInvalido`). No se puede suscribir a un tema sin contrato.
* **Trazabilidad:** cada módulo cita en su docstring el elemento del ADD y el ADR que implementa. Los tests están agrupados por iteración y driver. `docs/trazabilidad.md` cruza driver → ADR → spec → código → test.

### Consecuencias

* Positivas: los contratos no pueden divergir de la implementación sin romper el build. Un adaptador o consumidor nuevo (QA-I1, QA-M1) tiene el contrato a la vista.
* Negativas: cualquier cambio de API exige regenerar y revisar el contrato.

## Pros y contras de las opciones

### Opción 1: Contratos verificados

* Bueno, porque detecta automáticamente las divergencias.
* Malo, porque agrega un paso al cambiar la API.

### Opción 2: Solo wiki

* Bueno, porque no tiene costo inicial.
* Malo, porque la documentación se desactualiza sin que nadie lo note.

### Opción 3: Generación de código desde OpenAPI

* Bueno, porque el contrato queda como única fuente.
* Malo, porque las herramientas de generación para Python/FastAPI agregan complejidad desproporcionada para el prototipo.

## Implementación en el prototipo

* `specs/openapi.json`, `specs/eventos/*.schema.json`
* `trotamundos/asincrono/bus_eventos.py` (validación al publicar), `trotamundos/api/esquemas.py`
* `tests/test_contratos.py`, `scripts/exportar_contrato.py`

## Enlaces

* [ADR 0017](0017-stack-tecnologico-del-prototipo.md), [ADR 0007](0007-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md), [ADR 0008](0008-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md)
* [Trazabilidad](../trazabilidad.md)
