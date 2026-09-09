Tipo escenario: Testabilidad

Descripción del escenario:
Un equipo de QA automatiza la ejecución de pruebas sobre un módulo de cálculo de préstamos, aislándolo de las dependencias con la base de datos real.

Solución (Plantilla de 6 partes):
1. Fuente: Herramienta automatizada de CI/CD / Probador de integración
2. Estímulo: Inicio automático de pruebas tras completar una integración
3. Ambiente: Entorno aislado de pruebas / sandbox
4. Artefacto: Módulo de cálculo de préstamos
5. Respuesta: Aislar las dependencias mediante la táctica de abstraer fuentes de datos (abstract data sources), utilizando el patrón de inyección de dependencias (Dependency Injection)
6. Medida de la Respuesta: Suite de pruebas ejecutada en menos de 3 minutos, con un 100% de repetibilidad y 0 impacto en la base de datos real