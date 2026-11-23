# 0013. Servicios sin estado con autoescalado horizontal de API y workers

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 4
* Drivers: QA-E1

## Contexto y problema

El tráfico sufre picos estacionales previsibles (jueves a lunes) y ráfagas impredecibles de +300 % por disrupciones climáticas. Con 15 millones de cuentas y 2 millones de usuarios activos semanales, el sistema debe mantener la tasa de error < 0.1 % y la latencia web ≤ 1.5 s durante el pico (QA-E1). Un dimensionamiento fijo desperdicia recursos en baja demanda o se satura en los picos.

## Factores de decisión (drivers)

* **QA-E1:** pico por disrupción masiva.

## Opciones consideradas

1. Servicios sin estado (*stateless*) con autoescalado horizontal basado en métricas y balanceo de carga.
2. No aplicar la táctica: capacidad fija dimensionada de antemano.

## Decisión

Opción elegida: "Autoescalado horizontal basado en métricas para la capa de API y los trabajadores de eventos", porque hacer elásticas las instancias de la API y los workers de ingesta permite multiplicar los recursos en minutos y absorber la concurrencia masiva sin exceder 1.5 s ni degradar el servicio.

* API y workers se diseñan sin estado.
* La API escala por CPU, memoria y tráfico detrás de un balanceador regional.
* Los workers escalan según la longitud de las colas del bus de eventos.

### Tácticas aplicadas

* Aumentar los recursos (*Increase resources*).
* Introducir concurrencia (*Introduce concurrency*) distribuida mediante balanceadores.

### Consecuencias

* Positivas: escala durante los picos y reduce recursos en baja demanda; estabilidad bajo estrés.
* Negativas: retardo de 1 a 2 minutos mientras las nuevas instancias se inicializan y entran al grupo de balanceo.

## Pros y contras de las opciones

### Opción 1: Stateless + autoescalado

* Bueno, porque adapta la capacidad a la demanda real.
* Bueno, porque sostiene la tasa de error y la latencia exigidas.
* Malo, porque hay un retardo de arranque de instancias (mitigado por las colas, que absorben el trabajo mientras tanto).

### Opción 2: Capacidad fija

* Bueno, porque es más simple de operar.
* Malo, porque o sobredimensiona costos o se satura ante ráfagas del 300 %.

## Implementación en el prototipo

* Pool de workers y autoescalador por longitud de cola: `trotamundos/asincrono/workers.py`.
* Métrica de longitud de colas: `trotamundos/asincrono/bus_eventos.py`.
* Protección de la API ante sobrecarga: `trotamundos/api/proteccion_carga.py`.
* Estado fuera de los servicios (base de datos y caché): `trotamundos/datos/base_datos.py`, `trotamundos/datos/cache.py`.
* Umbrales de escalado: `trotamundos/config.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces; el escalado se simula variando la cantidad de hilos del pool. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 4](../add/ADD-Iteración-4.md)
* Relacionados: [ADR 0008](08-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md), [ADR 0004](04-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md), [ADR 0012](12-despliegue-multirregion-activo-pasivo-caliente-con-geodns.md)
