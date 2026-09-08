---
name: generar-atributos-de-calidad
description: "Genera y estructura escenarios de atributos de calidad de software (eficiencia, funcionalidad, mantenibilidad, portabilidad, fiabilidad, usabilidad) siguiendo el formato SEI. Usala cuando el usuario pida crear, definir o revisar un escenario de calidad, atributo de calidad, o requerimiento no funcional."
---


@Atributo_de_calidad

usar estandar:

Fuente de estimulo:
Estimulo:
Ambiente:
Artefacto:
Respuesta:
Medida de la respuesta:
Tipo escenario:



explicacion:


Fuente de estimulo - usuario/persona/sistema que inicia la escena
Estimulo - input del usuario/persona/sistema que se introduce
Ambiente - estado actual/contexto del Artefacto
Artefacto - sistema hardware/software que se esta analizando
Respuesta - accion que se debe llevar a cabo
Medidia de la respuesta: tiempo/porcentaje/cantidad/valor que debe tomar la respuesta
Tipo escenario - tipo del escenario que se trabaja puede ser Eficiencia/Funcionalidad/Mantenibilidad/Portabilidad/Fiabilidad/Usabilidad

@consideraciones

Si considera que no hay suficiente informacion para determinar los elementos (Fuente de estimulo/Estimulo/Ambiente/Artefacto/Respuesta/Medida de respuesta) pregunte al ususario por mas contexto.
Si usuario no provee mas contexto, asumir partes faltantes.
Cuando recibe atributos de calidad chequear si esta completo, si no lo esta, completarlo.
Usar Recursos siempre que se tenga que determinar 'Tipo escenario'.
Una ves determinado el 'Tipo escenario' leer TODOS los ejemplos de ese tipo.


@Recursos

Para determinar el tipo del escenario, usar siempre que se tenga que determinar 'Tipo escenario': [tipo escenario](descripcion-atributos-de-calidad.md)


Ejemplos Eficiencia: [ejemplo eficiencia](./ejemplo-eficiencia/eficiencia1.md)[ejemplo eficiencia](./ejemplo-eficiencia/eficiencia2.md)
Ejemplos Funcionalidad: [ejemplo funcionalidad](./ejemplo-funcionalidad/funcionalidad1.md)[ejemplo funcionalidad](./ejemplo-funcionalidad/funcionalidad2.md)
Ejemplos Mantenibilidad: [ejemplo mantenibilidad](./ejemplo-mantenibilidad/mantenibilidad1.md)[ejemplo mantenibilidad](./ejemplo-mantenibilidad/mantenibilidad2.md)
Ejemplos Portabilidad: [ejemplo portabilidad](./ejemplo-portabilidad/portabilidad1.md) [ejemplo portabilidad](./ejemplo-portabilidad/portabilidad2.md) 
Ejemplos Fiabilidad: [ejemplo fiabilidad](./ejemplo-fiabilidad/fiabilidad1.md) [ejemplo fiabilidad](./ejemplo-fiabilidad/fiabilidad2.md)
Ejemplos Usabilidad: [ejemplo usabilidad](./ejemplo-usabilidad/usabilidad1.md) [ejemplo usabilidad](./ejemplo-usabilidad/usabilidad2.md)






