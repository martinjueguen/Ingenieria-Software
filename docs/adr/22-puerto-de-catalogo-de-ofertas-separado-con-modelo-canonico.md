# 0022. Puerto de catálogo de ofertas separado del adaptador de reservas, con modelo canónico de Oferta

* Estado: aceptado
* Fecha: 2026-11-24
* Iteración ADD: 5
* Drivers: QA-M2, QA-I1, US-08, CON-1

## Contexto y problema

Para sugerir alternativas el sistema tiene que **buscar disponibilidad** en los proveedores y, si el usuario acepta, **reservar**. Hasta ahora los adaptadores de proveedores (ADR 0007) solo sincronizan reservas existentes. No todos los proveedores ofrecen un catálogo consultable, y cada uno lo expone con su propio formato.

## Factores de decisión (drivers)

* **QA-M2 / QA-I1:** incorporar el catálogo de un proveedor nuevo sin modificar el servicio ni los demás adaptadores.
* **CON-1:** integración mediante las APIs estándar de cada proveedor.
* **US-08:** buscar y reservar alternativas de alojamiento y transporte.

## Opciones consideradas

1. Agregar los métodos de búsqueda y reserva al adaptador de reservas existente.
2. Que el recomendador consuma directamente la API de cada proveedor.
3. Un puerto `AdaptadorCatalogo` separado, con un modelo canónico `Oferta`, registrado por proveedor.

## Decisión

Opción elegida: "Puerto de catálogo separado con modelo canónico", porque aplica el mismo patrón Adaptador que ya funciona para las reservas, sin obligar a los proveedores sin catálogo a implementarlo.

Cada adaptador de catálogo traduce el formato del proveedor a `Oferta` (proveedor, tipo, título, horario, origen y destino, precio y atributos como estrellas, distancia al centro o duración). El recomendador solo conoce `Oferta`. Al aceptar, el adaptador reserva en el proveedor y la reserva confirmada entra al viaje por el mismo camino que cualquier actualización externa (modelo canónico de reserva).

### Tácticas aplicadas

* Patrón Adaptador y modelo canónico de datos.
* Segregación de interfaces (un proveedor puede tener catálogo o no).

### Consecuencias

* Positivas: catálogos nuevos se incorporan registrando un adaptador; el recomendador queda aislado de los formatos externos.
* Negativas: un modelo canónico más que mantener.

## Pros y contras de las opciones

### Opción 1: Ampliar el adaptador de reservas

* Bueno, porque hay un solo adaptador por proveedor.
* Malo, porque obliga a modificar adaptadores existentes y a implementar búsqueda en proveedores que no la ofrecen.

### Opción 2: Consumo directo de las APIs

* Bueno, porque no hay capa intermedia.
* Malo, porque acopla el recomendador a cada formato externo; cada proveedor nuevo cambia el servicio.

### Opción 3: Puerto separado + `Oferta` canónica

* Bueno, porque reutiliza el mecanismo de registro de adaptadores (QA-I1).
* Malo, porque agrega una abstracción y un modelo más.

## Implementación en el prototipo

* Puerto `AdaptadorCatalogo`, `Oferta` y `BusquedaOfertas`: `trotamundos/integracion/puertos.py`.
* Adaptador estándar: `trotamundos/integracion/catalogo.py`.
* Catálogos simulados de hoteles, autos, trenes y vuelos: `trotamundos/integracion/simuladores_catalogo.py`.
* Registro de catálogos: `trotamundos/integracion/registro.py`, `trotamundos/app.py`.
* Tests: `tests/test_iteracion5_recomendaciones.py::TestAceptar::test_reserva_en_el_proveedor_y_la_agrega_al_viaje`.

En el prototipo los sistemas externos se simulan detrás de interfaces ([ADR 0017](17-stack-tecnologico-del-prototipo.md)).

## Enlaces

* [ADD Iteración 5](../add/ADD-Iteración-5.md)
* Relacionados: [ADR 0007](07-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md), [ADR 0023](23-recomendaciones-como-funcion-no-critica-con-degradacion-controlada.md)
