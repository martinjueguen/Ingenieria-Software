Escenario: Una aplicación móvil de navegación GPS detecta que la batería del teléfono inteligente ha caído a un nivel crítico, por debajo del 15%, y busca reducir el consumo de energía mientras el usuario conduce.

Tipo escenario: Eficiencia Energética

Solución (Plantilla de 6 partes):
1. Fuente: Agente automatizado / Sistema operativo del dispositivo móvil
2. Estímulo: Petición automática de conservación de energía por umbral de batería baja
3. Ambiente: Tiempo de ejecución en modo de batería baja (low-battery mode)
4. Artefacto: Aplicación móvil de navegación y sensores
5. Respuesta: Aplicar el patrón de fusión de sensores (sensor fusion) para inferir movimiento mediante el acelerómetro de bajo consumo antes de consultar el chip GPS de alto consumo
6. Medida de la Respuesta: Ahorro del 40% de la carga de batería por hora, prolongando la operatividad por 1,5 horas adicionales sin interrumpir la ruta calculada