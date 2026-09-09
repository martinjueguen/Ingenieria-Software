Tipo escenario: Disponibilidad 

Descripción del escenario:
En una plataforma bancaria en línea, la base de datos primaria de transacciones sufre una falla de hardware en el procesador durante una jornada pico de pago de salarios.

Solución (Plantilla de 6 partes):
1. Fuente: Servidor interno de base de datos (hardware)
2. Estímulo: Caída (crash) del procesador principal
3. Ambiente: Operación normal bajo carga máxima (peak load)
4. Artefacto: Base de datos relacional de transacciones
5. Respuesta: El sistema detecta la falla mediante un watchdog, notifica al administrador e inicia la conmutación por error (failover) automática hacia una réplica redundante en caliente (active/hot spare)
6. Medida de la Respuesta: Conmutación completada en menos de 2 segundos, sin interrupción perceptible para el cliente y con 0 datos confirmados perdidos