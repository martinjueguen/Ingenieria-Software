Escenario: Una plataforma de salud requiere integrar un nuevo servicio de historial clínico provisto por un tercero que utiliza estructuras de datos y formatos XML heterogéneos.

Tipo escenario: Integrabilidad

Solución (Plantilla de 6 partes):
1. Fuente: Proveedor de componentes / Stakeholder de la misión
2. Estímulo: Petición para integrar un nuevo servicio externo heterogéneo
3. Ambiente: Tiempo de desarrollo e integración
4. Artefacto: Subsistema de historia clínica e interfaz del servicio
5. Respuesta: Encapsular e intermediar la comunicación mediante un adaptador o envoltorio (wrapper / tailor interface) para resolver las diferencias de sintaxis y semántica de los datos
6. Medida de la Respuesta: Integración y pruebas completadas en 3 semanas, con un esfuerzo menor a 0,5 personas-mes y sin alterar las APIs de los demás módulos