# Architecture Decision Records (ADRs) - Trotamundos

Registro de las decisiones de arquitectura del sistema Trotamundos, en formato [MADR](https://adr.github.io/madr/). Cada ADR refleja una decisión tomada en el Paso 5 de las iteraciones del método ADD documentado en [`../add/`](../add/Home.md).

| N.º | Título | Iteración ADD | Estado | Drivers |
|---|---|:---:|---|---|
| [0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md) | Arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos | 1 | Aceptado | CRN-1, QA-R1, QA-D1, QA-E1, QA-S2 |
| [0002](0002-separar-clientes-web-movil-del-backend-detras-de-una-api.md) | Separar clientes web/móvil del backend detrás de una API | 1 | Aceptado | CRN-1, CON-2, QA-R2, QA-R3 |
| [0003](0003-descomponer-gestion-de-viajes-en-reservas-itinerarios-y-ciclo-de-vida.md) | Descomponer gestión de viajes en Servicio de Reservas, Servicio de Itinerarios y Gestor de Ciclo de Vida | 2 | Aceptado | US-04, US-05, QA-M1 |
| [0004](0004-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md) | Caché en memoria para itinerarios activos con invalidación ante modificaciones | 2 | Aceptado | QA-R2, QA-E1, US-04 |
| [0005](0005-endpoint-de-resumen-ligero-para-movil.md) | Endpoint de resumen ligero para móvil (Trip Summary) | 2 | Aceptado | QA-R3, QA-U1, CON-2 |
| [0006](0006-archivado-automatico-mediante-proceso-programado.md) | Archivado automático mediante proceso programado en segundo plano | 2 | Aceptado | US-05, QA-R2 |
| [0007](0007-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md) | Adaptadores desacoplados con modelo canónico de reserva | 3 | Aceptado | US-03, QA-I1, QA-I2, CON-1, QA-M1 |
| [0008](0008-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md) | Colas de mensajería persistentes y trabajadores concurrentes para ingesta | 3 | Aceptado | US-01, QA-R1, QA-E1 |
| [0009](0009-filtrado-por-whitelist-oauth-solo-lectura-y-tokens-cifrados.md) | Filtrado previo por whitelist, OAuth de solo lectura y tokens cifrados en reposo | 3 | Aceptado | US-02, QA-S2, US-01 |
| [0010](0010-deteccion-de-excepciones-y-reintentos-con-backoff-exponencial.md) | Detección de excepciones y reintentos con backoff exponencial, manteniendo el último estado conocido | 3 | Aceptado | QA-D2, QA-R1 |
| [0011](0011-adaptador-de-salida-hacia-la-agencia-de-viajes-preferida.md) | Adaptador de salida hacia la agencia de viajes preferida | 3 | Aceptado | US-06, QA-I1, CON-1 |
| [0012](0012-despliegue-multirregion-activo-pasivo-caliente-con-geodns.md) | Despliegue multirregión activo-pasivo caliente con GeoDNS y heartbeat | 4 | Aceptado | QA-D1, CON-3 |
| [0013](0013-servicios-sin-estado-con-autoescalado-horizontal.md) | Servicios sin estado con autoescalado horizontal de API y workers | 4 | Aceptado | QA-E1 |
| [0014](0014-almacen-analitico-olap-segregado-con-sincronizacion-asincrona.md) | Almacén analítico (OLAP) segregado con sincronización asíncrona | 4 | Aceptado | US-07, QA-R2 |
| [0015](0015-listas-de-control-de-acceso-por-itinerario-y-auditoria.md) | Listas de control de acceso por itinerario compartido y registro de auditoría | 4 | Aceptado | QA-S1 |
| [0016](0016-almacenamiento-en-utc-y-paquetes-de-localizacion-externos.md) | Almacenamiento en UTC y paquetes de localización externos | 4 | Aceptado | QA-U2, CON-3 |
| [0017](0017-stack-tecnologico-del-prototipo.md) | Stack tecnológico del prototipo: Python + FastAPI + SQLite, infraestructura en proceso detrás de interfaces | Prototipo | Aceptado | CRN-1, QA-M1, QA-I1 |
| [0018](0018-spec-driven-contratos-openapi-y-json-schema.md) | Desarrollo guiado por especificaciones: contrato OpenAPI y JSON Schema de eventos | Prototipo | Aceptado | QA-M1, QA-I1, QA-I2 |

## Convenciones

* Nombre de archivo: `NNNN-titulo-en-kebab-case.md`.
* Estados posibles: propuesto, aceptado, rechazado, deprecado, reemplazado por ADR NNNN.
* Las opciones consideradas provienen de las alternativas y conceptos del Paso 4 de cada iteración ADD; cuando el ADD trata un único concepto, la opción descartada es "no aplicar la táctica".
* La sección "Implementación en el prototipo" indica dónde vive cada decisión en el paquete `trotamundos/`. En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite detrás de interfaces; la decisión de stack se documenta en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).
