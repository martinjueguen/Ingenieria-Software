El equipo de desarrollo deberá poder incorporar un nuevo método de pago (por ejemplo, una billetera digital) al módulo de checkout sin afectar el funcionamiento de los métodos de pago existentes.

1. Fuente: Desarrollador del equipo de mantenimiento
2. Estímulo: Solicitud de agregar un nuevo método de pago al sistema
3. Ambiente: Fase de diseño/desarrollo, fuera de producción
4. Artefacto: Módulo de checkout y componente de gestión de pagos
5. Respuesta: El nuevo método se integra modificando únicamente el módulo de pagos, sin cambios en otros componentes del sistema
6. Medida de la Respuesta: Tiempo de implementación menor a 3 días-persona, con 0 regresiones en pruebas de los métodos de pago existentes
7. Tipo escenario: mantenibilidad