Tipo escenario: Rendimiento

Descripción del escenario: 
El sistema deberá generar el reporte mensual de ventas consolidado a partir de la base de datos transaccional, sin bloquear el uso normal de la plataforma por parte de otros usuarios mientras se ejecuta el proceso.

Solución (Plantilla de 6 partes):
1. Fuente: Administrador del sistema
2. Estímulo: Solicitud de generación del reporte mensual con más de 500.000 registros de ventas
3. Ambiente: Operación normal, en horario de baja demanda (proceso batch nocturno)
4. Artefacto: Módulo de generación de reportes y base de datos transaccional
5. Respuesta: El sistema genera el reporte en segundo plano sin afectar el rendimiento de las operaciones de otros usuarios
6. Medida de la Respuesta: Reporte generado en menos de 10 minutos, con uso de CPU del servidor de base de datos por debajo del 70% durante el proceso