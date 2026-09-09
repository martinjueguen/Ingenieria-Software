Escenario: El equipo de desarrollo de una plataforma de comercio electrónico libera un parche de seguridad para el microservicio de procesamiento de pagos utilizando un despliegue canario (canary testing).

Tipo escenario: Desplegabilidad

Solución (Plantilla de 6 partes):
Fuente: Equipo DevOps / Sistema de integración continua
Estímulo: Solicitud aprobada para reemplazar la versión activa del servicio con un parche de seguridad
Ambiente: Entorno de producción en ejecución parcial
Artefacto: Microservicio de procesamiento de pagos
Respuesta: El sistema automatiza el despliegue mediante scripts, dirige el 5% de las solicitudes al nuevo contenedor mediante canary testing y monitorea posibles anomalías
Medida de la Respuesta: Proceso completado en menos de 15 minutos, con 0 tiempo de inactividad global y capacidad de rollback automático en menos de 30 segundos si aumenta la tasa de errores