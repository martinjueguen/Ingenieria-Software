# 0003. Descomponer gestión de viajes en Servicio de Reservas, Servicio de Itinerarios y Gestor de Ciclo de Vida

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 2
* Drivers: US-04, US-05, QA-M1

## Contexto y problema

En la Iteración 1 se definió un único módulo "Gestión de viajes y reservas". Ese módulo concentra responsabilidades distintas: el alta/baja/modificación de reservas individuales (US-04), las reglas para agrupar reservas en viajes y el manejo de estados del viaje hasta su archivado (US-05). Mezclarlas acopla los tipos de reserva con la estructura del itinerario y complica incorporar nuevos medios de transporte (QA-M1).

## Factores de decisión (drivers)

* **US-04:** gestión manual de reservas.
* **US-05:** agrupación por viaje y archivado.
* **QA-M1:** nuevo medio de transporte sin tocar los tipos existentes.

## Opciones consideradas

1. Descomponer en Servicio de Reservas, Servicio de Itinerarios y Gestor de Ciclo de Vida.
2. No aplicar la descomposición: mantener un único módulo de gestión de viajes y reservas.

## Decisión

Opción elegida: "Descomponer en tres submódulos especializados", porque separa la validación y persistencia de reservas individuales de las reglas de agrupación cronológica y geográfica, evita el acoplamiento entre tipos de reserva y estructura del itinerario, y simplifica el mantenimiento y las pruebas aisladas.

* **Servicio de Reservas:** alta, baja, modificación y consulta de reservas; valida datos y notifica cambios al gestor de caché y al servicio de itinerarios.
* **Servicio de Itinerarios:** agrupa reservas en viajes según fechas, destinos y secuencia temporal; construye el consolidado del itinerario.
* **Gestor de Ciclo de Vida:** maneja los estados del viaje (planificado, en curso, finalizado, archivado).

### Tácticas aplicadas

* Aumentar la coherencia semántica (*Increase semantic coherence*).
* Encapsular (*Encapsulate*).

### Consecuencias

* Positivas: alta cohesión y bajo acoplamiento; se pueden modificar reglas de reservas o agregar transportes sin alterar la agrupación; pruebas unitarias y de integración por submódulo.
* Negativas: hay que coordinar la comunicación interna entre reservas e itinerarios cuando una acción afecta a ambos (por ejemplo, eliminar la única reserva de un viaje).

## Pros y contras de las opciones

### Opción 1: Tres submódulos especializados

* Bueno, porque cada submódulo tiene una responsabilidad única.
* Bueno, porque encapsular los tipos de reserva favorece agregar nuevos medios de transporte.
* Malo, porque requiere coordinación entre servicios.

### Opción 2: Módulo único

* Bueno, porque no hay coordinación entre submódulos.
* Malo, porque acopla tipos de reserva con la estructura del itinerario y dificulta extender el dominio y probarlo por partes.

## Implementación en el prototipo

* `trotamundos/gestion_viajes/servicio_reservas.py`
* `trotamundos/gestion_viajes/servicio_itinerarios.py`
* `trotamundos/gestion_viajes/gestor_ciclo_vida.py`
* Modelo de dominio (Viaje, estados, registro de tipos de transporte): `trotamundos/dominio/modelo.py`.
* Persistencia: `trotamundos/datos/repositorios.py`. Exposición: `trotamundos/api/rutas_viajes.py`, `trotamundos/api/rutas_reservas.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 2](../add/ADD-Iteración-2.md)
* Relacionados: [ADR 0001](01-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md), [ADR 0004](04-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md), [ADR 0006](06-archivado-automatico-mediante-proceso-programado.md), [ADR 0007](07-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md)
