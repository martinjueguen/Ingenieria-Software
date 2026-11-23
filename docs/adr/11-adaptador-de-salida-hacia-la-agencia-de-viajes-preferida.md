# 0011. Adaptador de salida hacia la agencia de viajes preferida

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 3
* Drivers: US-06, QA-I1, CON-1

## Contexto y problema

Ante un retraso, cancelación o contingencia, el viajero quiere conectar su panel con el soporte de su agencia de viajes preferida enviando el contexto de su reserva, sin explicar todo el itinerario desde cero (US-06). Existen distintas plataformas de agencias, con formatos propios, y esa diversidad no debe filtrarse hacia la lógica de presentación del panel.

## Factores de decisión (drivers)

* **US-06:** resolución de problemas con la agencia preferida.
* **QA-I1:** incorporar integraciones sin modificar módulos existentes.
* **CON-1:** integración mediante APIs estándar.

## Opciones consideradas

1. Módulo adaptador de salida que serializa el itinerario en un formato estándar de contingencia.
2. No aplicar la táctica: integrar cada agencia directamente desde la lógica del panel.

## Decisión

Opción elegida: "Adaptador de salida hacia la agencia preferida", porque encapsular la conexión en un adaptador específico simplifica el enlace con distintas plataformas de agencias sin alterar la lógica de presentación del panel.

El conector recibe la solicitud de asistencia iniciada por el usuario, empaqueta el itinerario, las reservas afectadas y sus códigos de confirmación en el formato requerido por la agencia y lo transmite a su canal de soporte oficial.

### Tácticas aplicadas

* Usar un intermediario (*Use an intermediary*).
* Encapsular (*Encapsulate*).

### Consecuencias

* Positivas: el contexto estructurado de la reserva llega directo al soporte; nuevas agencias se suman con un adaptador sin tocar el panel.
* Negativas: hay que mantener la traducción hacia el formato de cada agencia.

## Pros y contras de las opciones

### Opción 1: Adaptador de salida

* Bueno, porque aísla las particularidades de cada agencia.
* Bueno, porque reutiliza el modelo canónico como fuente del contexto.
* Malo, porque agrega un módulo de traducción por agencia.

### Opción 2: Integración directa desde el panel

* Bueno, porque evita una capa intermedia.
* Malo, porque acopla la presentación a cada plataforma de agencia y cada alta implica modificarla.

## Implementación en el prototipo

* Adaptador de salida: `trotamundos/integracion/agencia.py`, implementando el puerto de `trotamundos/integracion/puertos.py`.
* Endpoint de solicitud de soporte: `trotamundos/api/rutas_soporte.py`.
* Contexto del itinerario (modelo canónico): `trotamundos/dominio/modelo.py`, `trotamundos/gestion_viajes/servicio_itinerarios.py`.
* Agencia simulada: `trotamundos/integracion/simuladores.py`.
* Contrato: `specs/openapi.json`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 3](../add/ADD-Iteración-3.md)
* Relacionados: [ADR 0007](07-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md)
