---
name: generar-atributos-de-calidad
description: "Genera escenarios de atributos de calidad con el template SEI de seis partes, verifica su completitud, propone cómo completar los campos faltantes y construye árboles de utilidad con refinamientos y prioridades de valor de negocio. Se centra en los 10 atributos tratados en el libro 'software-architecture-in-practice-4': Availability, Deployability, Energy Efficiency, Integrability, Modifiability, Performance, Safety, Security, Testability y Usability. Usar esta skill siempre que el usuario mencione atributos de calidad, requisitos no funcionales , escenarios de Disponibilidad, Desplegabilidad, Eficiencia energética, Integrabilidad, Modificabilidad, Rendimiento, Seguridad, Testabilidad, Usabilidad., árbol de utilidad, o pida revisar/completar/priorizar requisitos de calidad de un sistema — incluso si no usa literalmente estos términos"
---

--Especificacion de la generacion de atributos de calidad de acuerdo con los templates de 6 partes del SEI--

#Pasos a seguir para la generacion:
1. Evalua el requerimiento del usuario.
2. Si el usuario no dio contexto del sistema para determinar los elementos, solicitar la informacion faltante.
3. Compara e identifica el/los tipo/s de atributo/s de calidad segun las descripciones provistas en la seccion [Recursos de referencia](#Recursos-de-referencia), SIEMPRE entrar en "tipo escenario" antes de determinar el/los tipo/s de atributo/s de calidad.
4. Ver TODOS los ejemplos disponibles para el atributo de calidad definido en [Recursos de referencia](#Recursos-de-referencia) NO ver ejemplos de atributos de calidad distintos al definido.
5. Imprimir el tipo del escenario.
6. Imprimir el escenario completando las 6 partes del template de [Template](#Atributo_de_calidad).
7. NO reescribir el escenario


#Atributo_de_calidad

Usar plantilla:

Fuente de estimulo:
Estimulo:
Ambiente:
Artefacto:
Respuesta:
Medida de la respuesta:

Explicacion de las partes de la plantilla:
>Fuente de estimulo - usuario/persona/sistema que inicia la escena
>Estimulo - input del usuario/persona/sistema que se introduce
>Ambiente - estado actual/contexto del Artefacto
>Artefacto - sistema hardware/software que se esta analizando
>Respuesta - accion que se debe llevar a cabo
>Medidia de la respuesta: tiempo/porcentaje/cantidad/valor que debe tomar la respuesta

--Fin de la especificacion de la generacion de atributos de calidad--



--Chequeo de completitud de un escenario--

#Pasos para chequeo de escenarios
1. Identificar el atributo de calidad consultando la seccion [Recursos de referencia](#Recursos-de-referencia) SIEMPRE entrar en "tipo escenario" antes de determinar el/los tipo/s de atributo/s de calidad.
2. Separar el escenario en las seis [partes del escenario] (Fuente de estimulo/Estimulo/Ambiente/Artefacto/Respuesta/Medida de la respuesta)
3. Intentar mapear explícitamente cada fragmento del escenario a una de las siguientes partes, para guiarte pordes pensar en las siguientes preguntas:
    Fuente de estimulo	¿Quién o qué origina el estímulo?
    Estímulo	¿Qué evento, cambio, fallo, ataque, solicitud o acción ocurre?
    Ambiente	¿En qué estado, modo, etapa o condición se encuentra el sistema cuando ocurre?
    Artefacto	¿Qué sistema, componente, módulo, dato, servicio o parte del sistema es afectada?
    Respuesta	¿Qué debe hacer el sistema como consecuencia del estímulo?
    Medida de respuesta	¿Cómo se determina objetivamente si la respuesta es aceptable?
    Paso 3 — Determinar si cada parte está presente
4. Para cada una de las seis partes asignar uno de estos estados:
    Completa: la información está presente y es suficientemente específica para el escenario.
    Parcial: existe alguna información, pero es demasiado vaga o no permite analizar adecuadamente el requisito.
    Faltante: la parte no aparece o no puede inferirse razonablemente.
5. Proponer cómo completarlo
Para cada parte parcial o faltante:
indicar qué información falta;
formular una pregunta concreta que permitiría obtenerla;
proponer un ejemplo plausible de completado, identificado claramente como propuesta. Utiliza los ejemplos de [Recursos de referencia](#Recursos-de-referencia) siempre que sea necesario, leer TOSOS los ejemplos del atributo que calidad sobre el que se trabaja, NO leer ejemplos de atributos de calidad distintos.
6. Considerar COMPLETO solamente cuando:
las seis partes están identificadas;
ninguna de las partes esta poco especificada;
la respuesta describe qué hace el sistema;
existe una medida de respuesta verificable o suficientemente concreta;
el contenido es coherente con el escenario general del atributo identificado.
7. Genera una salida para el usuario con el siguiente formato:

[Nombre del atributo]

[Parte del escenario]
Resultado: COMPLETO / PARCIAL / INCOMPLETO
Para cada una de las 6 partes del escenario

Posible solucion: ...

--Fin de Chequeo de completitud de un escenario--



--Generacion del arbol de utilidad--

#Pasos para cuando se solicite trabajar con arbol de utilidad
1. Identificar los atributos de calidad a partir de "tipo escenario" de la seccion [Recursos de referencia](#Recursos-de-referencia).
2. Lee el archivo "informacion arbol utilidad" presente en [Recursos de referencia](#Recursos-de-referencia), y define las prioridades y la complejidad de desarrollo de cada atributo identificado siguiendo la forma en que se muestra en el pdf.
3. Lee el ejemplo de arbol de utilidad realizado en "ejemplo arbol" en la seccion [Recursos de referencia](#Recursos-de-referencia). Guiate por ese ejemplo para el formato en el que tenes que realizar el arbol.
4. Genera una imagen en base a los atributos definidos, sus prioridades y complejidad, y el ejemplo de arbol. 

--Fin generacion del arbol de utilidad--


--Recursos de referencia---

#Recursos-de-referencia

Tipo escenario: [tipo escenario](./descripcion-atributos-de-calidad.md)

Ejemplos Deplegabilidad: [ejemplos desplegabilidad](./ejemplo-desplegabilidad/)
Ejemplos Disponibilidad: [ejemplos disponibilidad](./ejemplo-disponibilidad/)
Ejemplos Eficiencia Energetica: [ejemplos eficiencia-energetica](./ejemplo-eficiencia-energetica/)
Ejemplos Integrabilidad: [ejemplos integrabilidad](./ejemplo-integrabilidad/) 
Ejemplos Modificabilidad: [ejemplos modificabilidad](./ejemplo-modificabilidad/)
Ejemplos Rendimiento: [ejemplos rendimiento](./ejemplo-rendimiento/)
Ejemplos Seguridad Fisica: [ejemplos seguridad-fisica](./ejemplo-seguridad-fisica/)
Ejemplos Seguridad Informatica: [ejemplos seguridad-informatica](./ejemplo-seguridad-informatica/) 
Ejemplos Testabilidad: [ejemplos testabilidad](./ejemplo-testabilidad/)
Ejemplos Usabilidad: [ejemplos usabilidad](./ejemplo-usabilidad/)

Informacion para el arbol de utilidad: [informacion arbol utilidad](./informacion-arbol-utilidad-libro.pdf)
Ejemplo arbol utilidad: [ejemplo arbol](./ejemplo-arbol-de-utilidad.pdf)

--Fin de Recursos de referencia--
