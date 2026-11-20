# 0017. Stack tecnológico del prototipo: Python + FastAPI + SQLite, con infraestructura en proceso detrás de interfaces

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: transversal (implementación del prototipo)
* Drivers: CRN-1, QA-M1, QA-I1, QA-I2 y la consigna del TPE ("implementación prototipo que demuestre la viabilidad de la arquitectura")

## Contexto y problema

El ADD (iteraciones 1 a 4) es agnóstico de tecnología. Para el prototipo había que elegir lenguaje, framework y cómo materializar la infraestructura del diseño: bus de eventos, caché en memoria, base OLTP replicada, almacén OLAP, regiones, GeoDNS y autoescalado.

Restricciones del entorno del equipo: Python 3.15 y Java 8 instalados, sin Node ni Docker. El prototipo tiene que correr con un solo comando y demostrar los escenarios de calidad sin cuentas reales de Gmail, aerolíneas ni hoteles.

## Factores de decisión (drivers)

* Que corra con lo que ya está instalado y se pueda probar enseguida.
* Contratos explícitos y verificables (spec-driven, ADR-0018).
* Que cada elemento del ADD se pueda rastrear a un módulo de código.
* Poder reemplazar después la infraestructura simulada por la real (Redis, RabbitMQ, PostgreSQL) sin tocar el núcleo.

## Opciones consideradas

1. Python + FastAPI + SQLite, con infraestructura en proceso detrás de interfaces.
2. Python + FastAPI con infraestructura real (PostgreSQL, Redis, RabbitMQ) vía docker-compose.
3. Java + Spring Boot.

## Decisión

Opción elegida: "Python + FastAPI + SQLite, con infraestructura en proceso detrás de interfaces", porque corre con lo instalado, FastAPI genera el contrato OpenAPI desde los DTO tipados y cada pieza de infraestructura queda encapsulada en una clase cuya interfaz es la que tendría el servicio real.

| Elemento del ADD | Producción (diseño) | Prototipo |
|---|---|---|
| Bus de eventos / colas persistentes | Broker (RabbitMQ, Kafka, SQS) | `BusEventos` sobre SQLite con reintentos, backoff y cola de muertos |
| Caché en memoria | Redis | `GestorCache` (diccionario con TTL) |
| BD operacional OLTP replicada | Clúster relacional multirregión | SQLite + `ReplicadorRegional` (backup síncrono post-commit) |
| Almacén analítico OLAP | Data warehouse columnar | SQLite separado (`AlmacenAnalitico`) |
| Grupos de autoescalado | Instancias / contenedores | Hilos (`GrupoWorkers` + autoescalador por longitud de cola) |
| Global Traffic Manager / GeoDNS | DNS administrado | Proxy HTTP con heartbeat (`gestor_trafico.py`) |
| Proveedores, Gmail, agencias, red social | Sistemas externos reales | `integracion/simuladores.py` con formatos propietarios e inyección de fallas |
| Cliente web y app móvil | SPA + app nativa | HTML/JS sin framework; vista móvil web con GPS del navegador |

### Consecuencias

* Positivas: se arranca con `python -m trotamundos`; los tests corren en segundos; la demo reproduce cada escenario de calidad (caída de proveedor, token robado, caída de región).
* Negativas: los números absolutos de rendimiento y escalabilidad no son representativos de producción. SQLite serializa las escrituras y los workers son hilos de un mismo proceso. Lo que se demuestra es el mecanismo (táctica), no la escala.

## Pros y contras de las opciones

### Opción 1: Python + FastAPI + SQLite en proceso

* Bueno, porque no requiere instalar nada más.
* Bueno, porque las interfaces conservan la forma del diseño y permiten migrar.
* Malo, porque no mide el comportamiento real de un broker o un clúster.

### Opción 2: Infraestructura real con Docker

* Bueno, porque es más fiel a las iteraciones 3 y 4.
* Malo, porque requiere instalar Docker Desktop (WSL2 y virtualización), hoy no disponibles.

### Opción 3: Java + Spring Boot

* Bueno, porque es un ecosistema maduro para servicios.
* Malo, porque requiere JDK 17 o superior y Maven, y aporta más configuración para un prototipo.

## Implementación en el prototipo

* Dependencias: `requirements.txt`. Configuración por variables de entorno: `trotamundos/config.py`.
* Raíz de composición (único lugar que conoce las implementaciones concretas): `trotamundos/app.py`.
* Migración futura: implementar `BusEventos`, `GestorCache` y los repositorios contra los servicios reales y cambiar su construcción en `app.py`.

## Enlaces

* [ADR 0018](0018-spec-driven-contratos-openapi-y-json-schema.md), [ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md), [ADR 0012](0012-despliegue-multirregion-activo-pasivo-caliente-con-geodns.md)
