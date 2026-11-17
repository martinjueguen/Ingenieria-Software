# 0012. Despliegue multirregión activo-pasivo caliente con GeoDNS y heartbeat

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 4
* Drivers: QA-D1, CON-3

## Contexto y problema

Una interrupción del centro de datos principal dejaría a millones de viajeros sin acceso a sus itinerarios en momentos críticos. El sistema debe tolerar la caída completa de una región con 0 reservas confirmadas perdidas y ≤ 5 min/mes de indisponibilidad no planificada (QA-D1), y estar preparado para operar globalmente (CON-3).

## Factores de decisión (drivers)

* **QA-D1:** caída de una región.
* **CON-3:** operación multirregión internacional.

## Opciones consideradas

1. Despliegue en dos regiones geográficas (primaria y secundaria) con Global Traffic Manager/GeoDNS, chequeos de salud y conmutación automática.
2. No aplicar la táctica: despliegue en una única región.

## Decisión

Opción elegida: "Despliegue multirregión en esquema activo-pasivo caliente con balanceador DNS geográfico", porque una réplica completa en una segunda región, con conmutación automática ante la detección de anomalías, mantiene la indisponibilidad acumulada por debajo de los 5 minutos mensuales.

* Un Global Traffic Manager (GeoDNS) monitorea cada región con *heartbeats*; si la región activa deja de responder, redirige el tráfico a la secundaria en menos de 1 minuto.
* La base transaccional primaria replica continuamente hacia la réplica de la región secundaria para lograr *failover* sin pérdida de reservas confirmadas.

### Tácticas aplicadas

* Redundancia activa (*Active redundancy*): instancias operativas y listas en ambas ubicaciones (réplica caliente).
* Monitoreo y chequeo de salud (*Heartbeat / Ping-Echo*).
* Retiro de servicio / reconfiguración (*Removal from service*).

### Consecuencias

* Positivas: continuidad ante fallas regionales catastróficas; posibilidad de dirigir usuarios a la región más cercana.
* Negativas: costos de infraestructura significativamente mayores al duplicar componentes; requiere sincronización continua entre las bases de ambas regiones.

## Pros y contras de las opciones

### Opción 1: Multirregión activo-pasivo caliente con GeoDNS

* Bueno, porque tolera desastres regionales y cumple el límite de 5 min/mes.
* Bueno, porque da soporte formal a la operación global.
* Malo, porque duplica costos y exige replicación entre regiones.

### Opción 2: Región única

* Bueno, porque es más barata y no requiere replicación.
* Malo, porque la caída de la región deja todo el sistema inaccesible, incumpliendo QA-D1 y CON-3.

## Implementación en el prototipo

* Simulador de Global Traffic Manager/GeoDNS con heartbeat y conmutación: `trotamundos/infraestructura/gestor_trafico.py`.
* Arranque de cada región (proceso independiente con su base, bus y rol activo/pasivo): `trotamundos/infraestructura/region.py`.
* Replicación de la base transaccional entre regiones: `trotamundos/datos/replicacion.py`.
* Endpoint de salud consultado por el heartbeat: `trotamundos/api/rutas_salud.py`.
* Parámetros (intervalos, umbrales): `trotamundos/config.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. Cada región es un proceso independiente con su propia base SQLite; la primaria replica a la secundaria después de cada commit (RPO = 0) y la secundaria queda pasiva (sin workers ni planificador) hasta que el Global Traffic Manager la promueve con `POST /api/v1/region/promover`. En la prueba local, la conmutación tardó unos 5 s (3 heartbeats de 1 s) sin perder reservas confirmadas. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 4](../add/ADD-Iteración-4.md)
* Relacionados: [ADR 0013](0013-servicios-sin-estado-con-autoescalado-horizontal.md), [ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md)
