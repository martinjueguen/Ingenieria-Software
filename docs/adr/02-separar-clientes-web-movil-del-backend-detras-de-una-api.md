# 0002. Separar clientes web/móvil del backend detrás de una API

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 1
* Drivers: CRN-1, CON-2, QA-R2, QA-R3

## Contexto y problema

El sistema debe ser accesible desde la web y desde dispositivos móviles con una interfaz rica que aproveche capacidades nativas como el GPS (CON-2), con tiempos exigentes en ambos canales (800 ms web, 1.4 s primer despliegue móvil). Dentro de la arquitectura cliente-servidor elegida ([ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md)) hay que decidir cómo se relacionan los clientes con la lógica de negocio.

## Factores de decisión (drivers)

* **CRN-1:** estructura general del sistema.
* **CON-2:** acceso web y móvil con capacidades nativas.
* **QA-R2 / QA-R3:** optimizar los tiempos de respuesta por plataforma.

## Opciones consideradas

1. Clientes web y móvil separados del backend, que acceden únicamente a través de una API.
2. No aplicar la separación: clientes acoplados a la implementación interna del backend.

## Decisión

Opción elegida: "Clientes web y móvil separados del backend detrás de una API", porque separa las interfaces de usuario de la lógica de negocio, permite evolucionar cada cliente de manera independiente y facilita optimizar los tiempos de respuesta de cada plataforma.

La capa "API / Acceso al sistema" actúa como punto de entrada: recibe las solicitudes, valida su estructura, las deriva a los módulos correspondientes y devuelve las respuestas, evitando que las interfaces dependan de la implementación interna.

### Tácticas aplicadas

* Encapsular el backend detrás de una interfaz (API) bien definida.
* Usar un intermediario (la API) entre clientes y módulos de negocio.

### Consecuencias

* Positivas: cada cliente evoluciona por separado; la API permite contratos específicos por plataforma (por ejemplo, el resumen móvil del [ADR 0005](0005-endpoint-de-resumen-ligero-para-movil.md)); los cambios internos del backend no impactan en los clientes.
* Negativas: hay que mantener y versionar el contrato de la API; toda interacción pasa por solicitudes de red.

## Pros y contras de las opciones

### Opción 1: Clientes separados detrás de una API

* Bueno, porque desacopla presentación y lógica de negocio.
* Bueno, porque permite adaptar la entrega de datos a las limitaciones de cada plataforma.
* Malo, porque agrega un contrato a mantener.

### Opción 2: Clientes acoplados al backend

* Bueno, porque evita diseñar y mantener un contrato explícito.
* Malo, porque las interfaces quedan atadas a la implementación interna y cualquier cambio del backend las afecta.
* Malo, porque dificulta optimizar las respuestas por plataforma (web vs. móvil).

## Implementación en el prototipo

* Clientes: `trotamundos/web/` (cliente web y vista móvil con GPS).
* API: `trotamundos/api/` (`rutas_viajes.py`, `rutas_reservas.py`, `rutas_movil.py`, etc.).
* Contrato: `specs/openapi.json`.
* Composición: `trotamundos/app.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 1](../add/ADD-Iteración-1.md)
* Relacionados: [ADR 0001](0001-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md), [ADR 0005](0005-endpoint-de-resumen-ligero-para-movil.md), [ADR 0016](0016-almacenamiento-en-utc-y-paquetes-de-localizacion-externos.md)
