Escenario: Un usuario de una aplicación de diseño realiza por error una eliminación masiva de elementos gráficos y emite la orden de cancelar o deshacer el cambio.

Tipo escenario: Usabilidad

Solución (Plantilla de 6 partes):
1. Fuente: Usuario final
2. Estímulo: Comando de cancelación / deshacer (undo)
3. Ambiente: Operación en tiempo de ejecución durante el trabajo activo
4. Artefacto: Interfaz gráfica de usuario y gestor de estado
5. Respuesta: El sistema intercepta el comando (user initiative) y restaura el estado guardado mediante la táctica undo y el patrón Memento
6. Medida de la Respuesta: Estado anterior recuperado en menos de 0,5 segundos, sin congelamiento de pantalla ni corrupción del documento