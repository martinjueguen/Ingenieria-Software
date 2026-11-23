# 0005. Endpoint de resumen ligero para móvil (Trip Summary)

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 2
* Drivers: QA-R3, QA-U1, CON-2

## Contexto y problema

Al abrir la app móvil, el primer contenido útil (resumen del próximo viaje) debe mostrarse en ≤ 1.4 s sobre red 4G (QA-R3). Las conexiones móviles tienen más latencia y variabilidad de ancho de banda que las cableadas; transferir el itinerario completo con el detalle de cada reserva en la pantalla de bienvenida agranda la respuesta JSON y el tiempo de procesamiento en el dispositivo.

## Factores de decisión (drivers)

* **QA-R3:** primer despliegue móvil ≤ 1.4 s.
* **QA-U1:** tener disponible el próximo tramo para geolocalizarlo con GPS.
* **CON-2:** acceso móvil con interfaz rica.

## Opciones consideradas

1. Endpoint de resumen ligero (*Trip Summary*) con carga diferida de los detalles.
2. No aplicar la táctica: el cliente móvil consume el mismo itinerario completo que la web.

## Decisión

Opción elegida: "Endpoint de resumen ligero para móvil", porque limitar el paquete inicial a la información estrictamente necesaria (próximo tramo: número de vuelo, horario, código de reserva y estado) reduce el tamaño de la respuesta y el tiempo de render, dejando los detalles completos y los viajes pasados para solicitudes posteriores bajo demanda (*lazy loading* o paginación).

### Tácticas aplicadas

* Limitar el tamaño de las respuestas (*Bound execution times / Bound response sizes*).
* Reducir la sobrecarga computacional (*Reduce computational overhead*).

### Consecuencias

* Positivas: transferencia mínima por red celular; la app pinta el contenido útil de inmediato; el próximo destino queda disponible para la vista con GPS.
* Negativas: el backend mantiene un contrato o proyección específica para móvil (leve mantenimiento adicional); si el usuario abre el detalle de inmediato hace falta una segunda solicitud.

## Pros y contras de las opciones

### Opción 1: Trip Summary + carga diferida

* Bueno, porque minimiza el JSON enviado y acelera el renderizado.
* Bueno, porque evita serializar campos que no se muestran en la pantalla inicial.
* Malo, porque agrega un endpoint/proyección a mantener.
* Malo, porque el detalle requiere un segundo viaje de red.

### Opción 2: Itinerario completo para todos los clientes

* Bueno, porque hay un único contrato de consulta.
* Malo, porque transfiere y procesa datos que no se usan en la primera pantalla, comprometiendo el umbral de 1.4 s en 4G.

## Implementación en el prototipo

* Endpoint de resumen: `trotamundos/api/rutas_movil.py`.
* Construcción de la proyección del próximo tramo: `trotamundos/gestion_viajes/servicio_itinerarios.py`.
* Vista móvil con GPS: `trotamundos/web/`.
* Contrato: `specs/openapi.json`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](17-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 2](../add/ADD-Iteración-2.md)
* Relacionados: [ADR 0002](02-separar-clientes-web-movil-del-backend-detras-de-una-api.md), [ADR 0004](04-cache-en-memoria-para-itinerarios-activos-con-invalidacion.md)
