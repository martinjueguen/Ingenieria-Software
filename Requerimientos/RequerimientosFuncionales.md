# Requerimientos Funcionales Principales

- **Procesamiento de Correo:** El sistema debe sondear y escanear el correo electrónico de los usuarios en busca de correos relacionados con viajes para agregar automáticamente las reservas al itinerario.

- **Filtros y Whitelists:** Debe permitir filtrar y crear listas de remitentes seguros (*whitelists*) para ciertos correos electrónicos de viaje.

- **Integración con Terceros:** El sistema debe integrarse de manera fluida con sistemas de viajes e interfaces de agencias de terceros a través de APIs estándar (por ejemplo, intercambios de aerolíneas o rentadoras) para obtener detalles de las reservas, actualizaciones y cancelaciones.

- **Gestión Manual:** Los clientes deben poder agregar, actualizar o eliminar sus reservas existentes de forma manual dentro del panel.

- **Ciclo de Vida del Viaje:** Los elementos en el panel de control deben poder agruparse por viaje, y una vez que el viaje se completa, deben archivarse o eliminarse automáticamente de la vista principal.

- **Resolución de Problemas:** El sistema debe integrarse con la agencia de viajes preferida del usuario para facilitar una rápida resolución de problemas.

- **Analítica de Datos:** "Trotamundos" recopilará datos analíticos de los viajes (tendencias, destinos, cancelaciones) para su monetización por parte del equipo de datos, implicando la ejecución de consultas analíticas pesadas.

## Requerimiento avanzado (2da entrega)

- **Sistema de Recomendación (Opción A):** Incorporar un módulo que aplique técnicas de análisis sobre el historial y preferencias de los usuarios para sugerir proactivamente alternativas de alojamiento, transporte o rutas, con un esquema de optimización *human-in-the-loop* donde el usuario acepta, rechaza o ajusta parámetros para refinar continuamente el modelo. Historia de usuario y escenarios de calidad asociados (US-08, QA-R4, QA-D3, QA-M2, QA-S3): ver [`docs/add/Requerimientos-Funcionales.md`](../docs/add/Requerimientos-Funcionales.md) y [`docs/add/Atributos-de-Calidad.md`](../docs/add/Atributos-de-Calidad.md).
