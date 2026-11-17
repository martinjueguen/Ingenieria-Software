# 0010. Detección de excepciones y reintentos con backoff exponencial, manteniendo el último estado conocido

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 3
* Drivers: QA-D2, QA-R1

## Contexto y problema

Los servicios de terceros (APIs de aerolíneas, hoteles o correo) sufren caídas temporales o demoras. Ante una omisión o error del proveedor, el panel no puede quedar inactivo: debe seguir mostrando la última información conocida, detectar la falla en < 30 s, reintentar y reconciliar en < 5 min tras la recuperación (QA-D2), sin afectar la propagación de actualizaciones (QA-R1).

## Factores de decisión (drivers)

* **QA-D2:** falla de un proveedor externo con 0 minutos de inactividad del panel.
* **QA-R1:** reconciliación rápida una vez recuperado el proveedor.

## Opciones consideradas

1. Detección de excepciones en el conector y reintento con retroceso exponencial, manteniendo el último estado conocido.
2. No aplicar la táctica: propagar el error del proveedor al usuario y descartar la actualización fallida.

## Decisión

Opción elegida: "Detección de excepciones y reintentos con backoff exponencial", porque evita que la falla de un tercero bloquee las operaciones del sistema y reconcilia automáticamente los datos pendientes cuando el proveedor se restablece.

El conector captura la excepción, deja intacta la última información confirmada del viaje (indicando en la interfaz la fecha y hora de la última actualización) y encola un evento de reintento con retroceso exponencial.

### Tácticas aplicadas

* Detección de excepciones (*Exception detection*).
* Reintento (*Retry*) espaciado en el tiempo para no sobrecargar el enlace.

### Consecuencias

* Positivas: continuidad operativa del panel; reconciliación transparente al restablecerse el canal externo.
* Negativas: durante la caída del proveedor el usuario puede ver datos que no reflejan el último cambio en tiempo real.

## Pros y contras de las opciones

### Opción 1: Excepciones + retry con backoff + último estado conocido

* Bueno, porque la indisponibilidad de un tercero no interrumpe el panel.
* Bueno, porque la actualización pendiente se aplica sola al recuperarse.
* Malo, porque se muestran datos potencialmente desactualizados mientras dura la falla.

### Opción 2: Propagar el error

* Bueno, porque es más simple.
* Malo, porque el panel queda degradado o inactivo ante cada caída externa y las actualizaciones se pierden, incumpliendo QA-D2.

## Implementación en el prototipo

* Reintentos con backoff exponencial y cola de mensajes muertos: `trotamundos/asincrono/bus_eventos.py`.
* Captura de excepciones en los conectores: `trotamundos/integracion/proveedores/` y `trotamundos/integracion/correo/gmail.py`.
* Mantener el último estado conocido y su marca temporal: `trotamundos/gestion_viajes/servicio_reservas.py`, `trotamundos/dominio/modelo.py`.
* Simulación de proveedores caídos para pruebas: `trotamundos/integracion/simuladores.py`.
* Indicación de "última actualización" en la interfaz: `trotamundos/web/`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 3](../add/ADD-Iteración-3.md)
* Relacionados: [ADR 0007](0007-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md), [ADR 0008](0008-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md)
