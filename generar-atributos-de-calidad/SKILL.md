---
name: atributos-de-calidad-y-arbol-de-utilidad
description: "Genera escenarios de atributos de calidad con el template SEI de seis partes, verifica su completitud, propone cómo completar los campos faltantes y construye árboles de utilidad con refinamientos y prioridades de valor de negocio. Se centra en los 10 atributos tratados en el libro 'software-architecture-in-practice-4': Availability, Deployability, Energy Efficiency, Integrability, Modifiability, Performance, Safety, Security, Testability y Usability. Usar esta skill siempre que el usuario mencione atributos de calidad, requisitos no funcionales , escenarios de Disponibilidad, Desplegabilidad, Eficiencia energética, Integrabilidad, Modificabilidad, Rendimiento, Seguridad, Testabilidad, Usabilidad., árbol de utilidad, o pida revisar/completar/priorizar requisitos de calidad de un sistema — incluso si no usa literalmente estos términos"
---

--Especificacion de la generacion de atributos de calidad de acuerdo con los templates de 6 partes del SEI--

@Pasos a seguir para la generacion:
1. Evalua el requerimiento del usuario.
2. Si el usuario no dio contexto del sistema para determinar los elementos, solicitar la informacion faltante.
3. Compara e identifica el/los tipo/s de atributo/s de calidad segun las descripciones provistas en la seccion @Recursos-de-referencia.
4. Redacta el escenario completando las 6 partes del template de @Atributo_de_calidad.
5. Verifica el resultado contra cada uno de los ejemplos del atributo de calidad resultante presentes en @Recursos-de-referencia.


@Atributo_de_calidad

Usar plantilla:

Fuente de estimulo:
Estimulo:
Ambiente:
Artefacto:
Respuesta:
Medida de la respuesta:
Tipo escenario:

Explicacion de las partes de la plantilla:
>Fuente de estimulo - usuario/persona/sistema que inicia la escena
>Estimulo - input del usuario/persona/sistema que se introduce
>Ambiente - estado actual/contexto del Artefacto
>Artefacto - sistema hardware/software que se esta analizando
>Respuesta - accion que se debe llevar a cabo
>Medidia de la respuesta: tiempo/porcentaje/cantidad/valor que debe tomar la respuesta
>Tipo escenario - tipo del escenario que se trabaja puede ser Eficiencia/Funcionalidad/Mantenibilidad/Portabilidad/Fiabilidad/Usabilidad

--Fin de la especificacion de la generacion de atributos de calidad--

--Chequear completitud de un escenario--

@Pasos a seguir para el chequeo:
1. Lee 


@Recursos-de-referencia

Para determinar el tipo de atributo de calidad del escenario, usar siempre que se tenga que determinar 'Tipo escenario': [tipo escenario](./descripcion-atributos-de-calidad.md)

Ejemplos Eficiencia: [ejemplo eficiencia](./ejemplo-eficiencia/)
Ejemplos Funcionalidad: [ejemplo funcionalidad](./ejemplo-funcionalidad/)
Ejemplos Mantenibilidad: [ejemplo mantenibilidad](./ejemplo-mantenibilidad/)
Ejemplos Portabilidad: [ejemplo portabilidad](./ejemplo-portabilidad/) 
Ejemplos Fiabilidad: [ejemplo fiabilidad](./ejemplo-fiabilidad/)
Ejemplos Usabilidad: [ejemplo usabilidad](./ejemplo-usabilidad/)

