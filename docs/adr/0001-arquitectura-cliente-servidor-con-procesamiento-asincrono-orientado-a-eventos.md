# 0001. Arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 1
* Drivers: CRN-1, QA-R1, QA-D1, QA-E1, QA-S2

## Contexto y problema

Trotamundos es un sistema greenfield en un dominio maduro que debe consolidar reservas de viaje provenientes de correos, APIs de proveedores turísticos y carga manual, accesible desde web y móvil. Hay que definir la estructura general del sistema (CRN-1) de modo que soporte los atributos de calidad más prioritarios: propagación de actualizaciones en ≤ 5 min, tolerancia a la caída de una región, picos de +300 % de tráfico y protección del acceso al correo. Varias tareas (escaneo de correo, consulta a proveedores, analítica) son lentas o pesadas y no deben bloquear las solicitudes interactivas.

## Factores de decisión (drivers)

* **CRN-1:** definir la estructura general del sistema.
* **QA-R1 (H,H):** actualizaciones visibles en ≤ 5 minutos.
* **QA-D1 (H,H):** caída de una región sin pérdida de reservas.
* **QA-E1 (H,H):** picos por disrupción masiva.
* **QA-S2 (H,H):** compromiso del acceso al correo.

## Opciones consideradas

1. Arquitectura cliente-servidor monolítica.
2. Arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos.

## Decisión

Opción elegida: "Arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos", porque el modelo cliente-servidor atiende rápido las consultas interactivas mientras que el bus de eventos saca del camino crítico las tareas lentas o pesadas (correo, actualizaciones externas, analítica), y permite escalar y reintentar esos procesos de forma independiente.

Decisiones asociadas registradas en el Paso 5 de la Iteración 1:

* Incorporar un sistema de mensajería con procesamiento asíncrono (persistencia de eventos y reintentos).
* Crear un módulo de gestión de viajes y reservas (refinado en [ADR 0003](0003-descomponer-gestion-de-viajes-en-reservas-itinerarios-y-ciclo-de-vida.md)).
* Crear un módulo de integración con proveedores externos (refinado en [ADR 0007](0007-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md)).
* Separar el procesamiento analítico de la persistencia operativa (refinado en [ADR 0014](0014-almacen-analitico-olap-segregado-con-sincronizacion-asincrona.md)).
* Incorporar mecanismos de autenticación y autorización (refinados en [ADR 0009](0009-filtrado-por-whitelist-oauth-solo-lectura-y-tokens-cifrados.md) y [ADR 0015](0015-listas-de-control-de-acceso-por-itinerario-y-auditoria.md)).
* Separar los clientes web y móvil del backend ([ADR 0002](0002-separar-clientes-web-movil-del-backend-detras-de-una-api.md)).

### Tácticas aplicadas

* Estructura en capas: Cliente, Servidor de aplicaciones y Datos.
* Bus de eventos que desacopla productores y consumidores, con persistencia de mensajes y reintentos.

### Consecuencias

* Positivas: las consultas se atienden directamente desde el servidor; los consumidores de carga pesada escalan sin escalar todo el sistema; los eventos pendientes no se pierden ante fallas temporales de proveedores; nuevas integraciones se agregan como consumidores/adaptadores que respetan los contratos de eventos.
* Negativas: mayor complejidad inicial (diseño de eventos, contratos, infraestructura de mensajería); consistencia eventual que obliga a controlar el límite de 5 minutos; dependencia de la infraestructura de mensajería; mayor esfuerzo de monitoreo de colas, retrasos y reintentos.

## Pros y contras de las opciones

### Opción 1: Cliente-servidor monolítica

* Bueno, porque es más simple de desarrollar, probar y desplegar.
* Bueno, porque los módulos se comunican directamente sin mensajería y es más fácil mantener la consistencia de datos.
* Malo, porque escalar una parte (correo, proveedores) obliga a replicar toda la aplicación.
* Malo, porque un error puede afectar a gran parte del sistema por el acoplamiento entre funcionalidades.
* Malo, porque las tareas pesadas compiten por recursos con las operaciones interactivas.
* Malo, porque cambiar una integración exige reconstruir y redesplegar todo, y sumar proveedores o medios de transporte aumenta el acoplamiento.

### Opción 2: Cliente-servidor con procesamiento asíncrono orientado a eventos

* Bueno, porque las tareas lentas se procesan en segundo plano y ayudan a cumplir las latencias web y móvil.
* Bueno, porque los consumidores escalan de manera independiente.
* Bueno, porque con mensajería persistente y reintentos se toleran fallas de proveedores.
* Bueno, porque las integraciones y nuevos medios de transporte se agregan como componentes que respetan contratos.
* Malo, porque agrega complejidad, consistencia eventual, dependencia de la mensajería y necesidad de monitoreo.

## Implementación en el prototipo

* Raíz de composición que arma las capas y conecta productores/consumidores: `trotamundos/app.py`, configuración en `trotamundos/config.py`.
* Capa cliente: `trotamundos/web/`. Capa de acceso: `trotamundos/api/`.
* Bus de eventos: `trotamundos/asincrono/bus_eventos.py`; consumidores en `trotamundos/asincrono/consumidores.py`; workers en `trotamundos/asincrono/workers.py`.
* Capa de datos: `trotamundos/datos/base_datos.py` y `trotamundos/datos/repositorios.py`.
* Contratos de eventos: `specs/eventos/*.schema.json`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces que permiten reemplazarla por productos reales. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 1](../add/ADD-Iteración-1.md)
* [Restricciones y Concerns](../add/Restricciones-y-Concerns.md)
* Relacionados: [ADR 0002](0002-separar-clientes-web-movil-del-backend-detras-de-una-api.md), [ADR 0008](0008-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md), [ADR 0013](0013-servicios-sin-estado-con-autoescalado-horizontal.md)
