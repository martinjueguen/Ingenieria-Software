# 0015. Listas de control de acceso por itinerario compartido y registro de auditoría

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 4
* Drivers: QA-S1

## Contexto y problema

Los datos de viaje son información personal sensible (ubicaciones y fechas de traslado). Los usuarios pueden compartir itinerarios, pero solo las personas designadas por el dueño deben poder verlos: el 100 % de los accesos no autorizados debe bloquearse, con 0 itinerarios expuestos, y los intentos deben auditarse (QA-S1).

## Factores de decisión (drivers)

* **QA-S1:** acceso indebido a itinerarios compartidos.

## Opciones consideradas

1. Lista de Control de Acceso explícita por itinerario, con validación de identidad y auditoría.
2. No aplicar la táctica: compartir mediante enlaces públicos sin verificación de identidad.

## Decisión

Opción elegida: "Listas de control de acceso explícitas por itinerario en el módulo de seguridad", porque restringir la visualización a personas designadas mediante verificación de identidad y autorización a nivel de registro impide que atacantes o terceros no autorizados accedan a los viajes.

* El propietario invita explícitamente a personas designadas (por correo o identificador de usuario) con permiso de solo lectura.
* El controlador de autorización verifica, antes de entregar datos, que el solicitante sea el propietario o un invitado de la lista.
* Todos los accesos e intentos denegados se registran en el registro de auditoría.

### Tácticas aplicadas

* Autorizar actores (*Authorize actors*).
* Limitar acceso (*Limit access*).

### Consecuencias

* Positivas: seguridad granular por viaje sin enlaces públicos expuestos; trazabilidad de intentos denegados y visualizaciones.
* Negativas: los invitados deben poseer una cuenta autenticada para validar su designación.

## Pros y contras de las opciones

### Opción 1: ACL por itinerario + auditoría

* Bueno, porque cada viaje tiene su propio control de acceso.
* Bueno, porque todo intento queda auditado.
* Malo, porque exige cuenta autenticada a los invitados.

### Opción 2: Enlaces públicos

* Bueno, porque los invitados no necesitan cuenta.
* Malo, porque cualquiera que obtenga el enlace accede al itinerario, incumpliendo QA-S1.

## Implementación en el prototipo

* Verificación de identidad: `trotamundos/seguridad/autenticacion.py`.
* ACL por itinerario: `trotamundos/seguridad/autorizacion.py`.
* Registro de auditoría: `trotamundos/seguridad/auditoria.py`.
* Endpoints para compartir y consultar itinerarios compartidos: `trotamundos/api/rutas_compartir.py`; publicación en redes: `trotamundos/integracion/redes_sociales.py`.
* Persistencia de la ACL y la auditoría: `trotamundos/datos/repositorios.py`.
* Interfaz de compartición: `trotamundos/web/`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 4](../add/ADD-Iteración-4.md)
* Relacionados: [ADR 0009](09-filtrado-por-whitelist-oauth-solo-lectura-y-tokens-cifrados.md), [ADR 0001](01-arquitectura-cliente-servidor-con-procesamiento-asincrono-orientado-a-eventos.md)
