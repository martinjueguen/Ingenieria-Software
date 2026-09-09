Escenario: El departamento financiero solicita agregar una nueva regla de cálculo de impuestos regionales en un sistema de facturación electrónica sin modificar el código fuente principal.

Tipo escenario: Modificabilidad

Solución (Plantilla de 6 partes):
1. Fuente: Analista de negocio / Administrador del sistema
2. Estímulo: Directiva para modificar y agregar reglas del módulo de cálculo de impuestos
3. Ambiente: Tiempo de inicio o configuración (initialization / configuration time)
4. Artefacto: Módulo de facturación y archivos de reglas de negocio
5. Respuesta: Aplicar la táctica de vinculación diferida mediante la lectura de archivos de configuración externos (resource files / defer binding)
6. Medida de la Respuesta: Incorporación de la regla en menos de 2 horas de configuración administrativa, 0 líneas de código fuente modificadas y 0 defectos introducidos