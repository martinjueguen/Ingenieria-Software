# 0009. Filtrado previo por whitelist, OAuth de solo lectura y tokens cifrados en reposo

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 3
* Drivers: US-02, QA-S2, US-01

## Contexto y problema

Para extraer reservas el sistema accede a la casilla de correo del usuario (US-01), lo que expone correspondencia personal. El usuario debe poder limitar qué remitentes se procesan (US-02) y, ante el robo de credenciales o tokens, no debe exponerse ningún correo (QA-S2: detección < 5 min, revocación < 1 min, 0 correos expuestos).

## Factores de decisión (drivers)

* **US-02:** filtros y lista blanca de remitentes.
* **QA-S2:** compromiso del acceso al correo.
* **US-01:** procesamiento de correo.

## Opciones consideradas

1. Filtrado previo por whitelist y gestión de credenciales con mínimo privilegio (OAuth de solo lectura, tokens cifrados en reposo).
2. No aplicar la táctica: acceso con alcance amplio, tokens sin cifrar y análisis de todos los correos.

## Decisión

Opción elegida: "Whitelist previa, OAuth de solo lectura y tokens cifrados en reposo", porque garantiza que el motor de extracción jamás examine correos privados y mitiga el impacto de una filtración de tokens.

* El escaneo evalúa primero el remitente contra la whitelist del usuario; si no coincide con un dominio autorizado, el correo se descarta sin examinar asunto ni cuerpo.
* La conexión solicita únicamente *scopes* OAuth de solo lectura.
* Los tokens se almacenan cifrados en reposo; el gestor de tokens permite la revocación inmediata ante anomalías o pedido del usuario.

### Tácticas aplicadas

* Limitar acceso (*Limit access*): mínimo privilegio en los *scopes*.
* Autorizar actores (*Authorize actors*): whitelist de remitentes.
* Cifrar datos (*Encrypt data*): tokens cifrados en reposo.

### Consecuencias

* Positivas: ningún correo fuera de los remitentes autorizados se analiza ni almacena; un token interceptado no permite escribir ni borrar en la casilla.
* Negativas: depende del correcto consentimiento OAuth del usuario y de la correcta configuración de sus filtros de remitentes.

## Pros y contras de las opciones

### Opción 1: Whitelist + mínimo privilegio + cifrado

* Bueno, porque protege estrictamente la privacidad.
* Bueno, porque limita el daño ante robo de credenciales.
* Malo, porque si la whitelist está mal configurada se pueden omitir correos de viaje válidos.

### Opción 2: Acceso amplio sin filtrado ni cifrado

* Bueno, porque no requiere configuración del usuario.
* Malo, porque expone la correspondencia personal y amplifica el impacto de un token robado, incumpliendo QA-S2.

## Implementación en el prototipo

* Filtrado por whitelist antes de leer el cuerpo: `trotamundos/integracion/correo/servicio_escaneo.py`.
* Adaptador OAuth de solo lectura: `trotamundos/integracion/correo/gmail.py`.
* Custodia y revocación de tokens: `trotamundos/seguridad/gestor_tokens.py`; cifrado Fernet: `trotamundos/seguridad/cifrado.py`.
* Auditoría de accesos: `trotamundos/seguridad/auditoria.py`.
* Configuración de whitelist y vinculación de casilla: `trotamundos/api/rutas_correo.py`.
* Almacén de tokens y listas blancas: `trotamundos/datos/repositorios.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 3](../add/ADD-Iteración-3.md)
* Relacionados: [ADR 0007](07-adaptadores-desacoplados-con-modelo-canonico-de-reserva.md), [ADR 0008](08-colas-persistentes-y-trabajadores-concurrentes-para-ingesta.md), [ADR 0015](15-listas-de-control-de-acceso-por-itinerario-y-auditoria.md)
