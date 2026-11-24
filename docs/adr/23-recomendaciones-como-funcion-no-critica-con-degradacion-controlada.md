# 0023. Recomendaciones como función no crítica, con degradación controlada ante fallas y sobrecarga

* Estado: aceptado
* Fecha: 2026-11-24
* Iteración ADD: 5
* Drivers: QA-D3, QA-E1, QA-D2

## Contexto y problema

El recomendador depende de catálogos externos que pueden caerse, y su carga crece justamente durante las disrupciones masivas (más cancelaciones, más alternativas que calcular), que es cuando el sistema ya está en su pico (QA-E1). Una sugerencia es un valor agregado; ver el itinerario no. La nueva funcionalidad no puede comprometer la disponibilidad del panel (QA-D3).

## Factores de decisión (drivers)

* **QA-D3:** 0 minutos de inactividad del panel ante fallas del recomendador o de un catálogo; 0 mensajes perdidos.
* **QA-E1:** sostener el pico sin degradar las funciones críticas.
* **QA-D2:** coherencia con el manejo de fallas de proveedores.

## Opciones consideradas

1. Tratar las recomendaciones igual que el resto: reintentar hasta que todos los catálogos respondan y atender todas las solicitudes bajo carga.
2. Clasificar las recomendaciones como función no crítica: omitir catálogos caídos y suspender el módulo bajo sobrecarga.

## Decisión

Opción elegida: "Función no crítica con degradación controlada", porque prioriza explícitamente el panel de viajes sobre la funcionalidad de valor agregado.

* **Catálogo caído durante el precálculo:** se registra la falla, se omite ese catálogo y se sugiere con los demás; el mensaje se procesa igual (no va a la cola de mensajes muertos).
* **Catálogo caído al aceptar:** la API responde `503` con `Retry-After` y la sugerencia sigue pendiente.
* **Sobrecarga:** la protección de carga de la API (ADR 0013) rechaza primero las rutas no críticas (`/recomendaciones` y `/analitica`) con `503`, mientras el panel sigue respondiendo.

### Tácticas aplicadas

* Detección de excepciones y retiro temporal del componente fallido.
* Degradación (*Degradation*) y desprendimiento de carga (*Load shedding*) por prioridad.

### Consecuencias

* Positivas: ninguna falla del módulo afecta las funciones críticas; la carga nueva no compite con el panel en los picos.
* Negativas: en un pico extremo el usuario puede quedarse sin sugerencias justo durante una disrupción; con un catálogo caído las sugerencias son menos variadas.

## Pros y contras de las opciones

### Opción 1: Mismo tratamiento que las funciones críticas

* Bueno, porque las sugerencias estarían siempre completas.
* Malo, porque una caída externa o un pico podrían degradar el panel, incumpliendo QA-D3 y QA-E1.

### Opción 2: Función no crítica

* Bueno, porque aísla las fallas y protege el panel bajo carga.
* Malo, porque las sugerencias pueden faltar temporalmente.

## Implementación en el prototipo

* Omisión de catálogos caídos (`_buscar`): `trotamundos/recomendacion/servicio.py`.
* `503 + Retry-After` al aceptar con el proveedor caído: `trotamundos/api/rutas_recomendaciones.py`.
* Rutas no críticas y desprendimiento de carga: `trotamundos/api/proteccion_carga.py`.
* Tests: `tests/test_iteracion5_recomendaciones.py::TestCalidad::test_catalogo_caido_no_impide_sugerir_con_los_demas`, `test_funcion_no_critica_bajo_sobrecarga` y `TestAceptar::test_catalogo_caido_al_aceptar_responde_503`.

En el prototipo los sistemas externos se simulan detrás de interfaces ([ADR 0017](17-stack-tecnologico-del-prototipo.md)).

## Enlaces

* [ADD Iteración 5](../add/ADD-Iteración-5.md)
* Relacionados: [ADR 0010](10-deteccion-de-excepciones-y-reintentos-con-backoff-exponencial.md), [ADR 0013](13-servicios-sin-estado-con-autoescalado-horizontal.md), [ADR 0022](22-puerto-de-catalogo-de-ofertas-separado-con-modelo-canonico.md)
