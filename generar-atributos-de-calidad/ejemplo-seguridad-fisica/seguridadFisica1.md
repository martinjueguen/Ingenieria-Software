Tipo escenario: Seguridad Física

Descripción del escenario:
Un sensor en el sistema de monitoreo del paciente falla al no reportar un valor de vital importancia después de 100 ms. La falla se registra, se enciende una luz de advertencia en la consola y se activa un sensor de respaldo de menor fidelidad. El sistema monitorea al paciente utilizando el sensor de respaldo después de no más de 300 ms.

Solución (Plantilla de 6 partes):
1. Fuente: Un sensor
2. Estímulo: Falla de omisión al no reportar un valor crítico para la vida tras 100 ms
3. Ambiente: Operaciones normales
4. Artefacto: Sistema de monitoreo de paciente / Sensor
5. Respuesta: La falla se registra en la bitácora, se enciende una luz de advertencia en la consola y se activa un sensor de respaldo
6. Medida de la Respuesta: El sistema monitorea al paciente con el sensor de respaldo en un tiempo no mayor a 300 ms