Tipo escenario: Seguridad de la Información

Descripción del escenario:
Un atacante externo intenta realizar transacciones bancarias utilizando credenciales interceptadas en un ataque de suplantación de identidad.

Solución (Plantilla de 6 partes):
1. Fuente: Atacante externo no identificado
2. Estímulo: Intento de acceso no autorizado y ejecución de transacciones
3. Ambiente: Operaciones en línea conectadas a la red
4. Artefacto: Servicios transaccionales de la banca en línea
5. Respuesta: Autenticar al usuario mediante autenticación multifactor (authenticate actors), validar permisos (authorize actors) y registrar la actividad en la pista de auditoría (audit)
6. Medida de la Respuesta: Intento no autorizado bloqueado al 100%, 0 fondos comprometidos y registro completo generado en la bitácora de auditoría en menos de 1 segundo