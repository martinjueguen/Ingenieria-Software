# 0007. Adaptadores desacoplados con modelo canónico de reserva

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 3
* Drivers: US-03, QA-I1, QA-I2, CON-1, QA-M1

## Contexto y problema

Cada aerolínea, hotel, arrendadora o servicio de correo expone formatos y protocolos heterogéneos (CON-1). El sistema debe obtener reservas, actualizaciones y cancelaciones de todos ellos (US-03) y poder sumar un nuevo proveedor de viajes, correo o red social en ≤ 2 semanas sin modificar módulos existentes ni el motor de extracción (QA-I1, QA-I2). Si el núcleo conociera los formatos propietarios, cada alta o cambio de API externa lo impactaría.

## Factores de decisión (drivers)

* **US-03:** integración con APIs de terceros.
* **QA-I1:** nuevo proveedor de viajes en ≤ 2 semanas, 0 módulos modificados.
* **QA-I2:** nuevo proveedor de correo o red social sin cambiar el motor de extracción.
* **CON-1:** uso de APIs estándar de la industria.
* **QA-M1:** facilitar nuevos medios de transporte (trenes, micros).

## Opciones consideradas

1. Capa de adaptadores (patrón Adaptador) que traducen a un Modelo Canónico de Reserva.
2. No aplicar la táctica: el núcleo consume directamente los formatos de cada proveedor.

## Decisión

Opción elegida: "Adaptadores desacoplados con modelo canónico común", porque aíslan al resto del sistema de las particularidades externas: el motor de reservas y los itinerarios solo conocen el modelo interno, y dar de alta un proveedor consiste en crear su adaptador.

Cada servicio externo cuenta con un conector que consume su API, consulta cambios de estado, traduce las respuestas al modelo canónico y notifica errores de comunicación.

### Tácticas aplicadas

* Usar un intermediario (*Use an intermediary*).
* Encapsular (*Encapsulate*): detalles de cada API detrás de una interfaz unificada.

### Consecuencias

* Positivas: si una aerolínea cambia su API o se agrega un proveedor, solo se toca su adaptador; estandarización interna del dominio; base para incorporar nuevos medios de transporte.
* Negativas: hay que mantener módulos de traducción específicos y sincronizarlos ante cambios de versión de las APIs de terceros.

## Pros y contras de las opciones

### Opción 1: Adaptadores + modelo canónico

* Bueno, porque aísla el núcleo de los cambios externos.
* Bueno, porque el dominio trabaja con un único modelo de datos.
* Malo, porque multiplica los módulos de traducción a mantener.

### Opción 2: Consumo directo de formatos propietarios

* Bueno, porque evita la capa de traducción.
* Malo, porque acopla el núcleo a cada proveedor y cualquier alta o cambio de API obliga a modificarlo, incumpliendo QA-I1 y QA-I2.

## Implementación en el prototipo

* Interfaces (puertos) de los adaptadores: `trotamundos/integracion/puertos.py`.
* Registro de adaptadores disponibles: `trotamundos/integracion/registro.py`.
* Adaptadores de proveedores: `trotamundos/integracion/proveedores/` (aerolínea, hotel, arrendadora, tren).
* Adaptador de correo: `trotamundos/integracion/correo/gmail.py`; redes sociales: `trotamundos/integracion/redes_sociales.py`.
* Modelo canónico de reserva y registro de tipos de transporte: `trotamundos/dominio/modelo.py`.
* Proveedores simulados para pruebas: `trotamundos/integracion/simuladores.py`. Exposición: `trotamundos/api/rutas_proveedores.py`.
* Contratos: `specs/eventos/*.schema.json`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 3](../add/ADD-Iteración-3.md)
* Relacionados: [ADR 0003](0003-descomponer-gestion-de-viajes-en-reservas-itinerarios-y-ciclo-de-vida.md), [ADR 0008](0008-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md), [ADR 0010](0010-deteccion-de-excepciones-y-reintentos-con-backoff-exponencial.md), [ADR 0011](0011-adaptador-de-salida-hacia-la-agencia-de-viajes-preferida.md)
