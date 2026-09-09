Escenario: En un vehículo autónomo, el radar lidar frontal pierde comunicación temporal debido a interferencias extremas mientras transita a alta velocidad por carretera.

Tipo escenario: Seguridad Física

Solución (Plantilla de 6 partes):
1. Fuente: Radar Lidar frontal (sensor físico)
2. Estímulo: Omisión de lecturas durante más de 50 ms
3. Ambiente: Modo de conducción autónoma en tiempo de ejecución
4. Artefacto: Subsistema de control de navegación y frenado
5. Respuesta: Detectar el estado mediante supervisión de condiciones (condition monitoring), activar una alerta en el tablero y conmutar a la cámara estereoscópica de respaldo mediante analytic redundancy, reduciendo preventivamente la velocidad
6. Medida de la Respuesta: Restablecimiento del control seguro en menos de 80 ms, evitando salir del espacio de estados seguros y sin colisiones