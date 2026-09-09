# Referencia de los 10 escenarios generales del libro

## 1. Availability — Disponibilidad

Descripcion general: La disponibilidad se refiere a que el sistema sea capaz de continuar proporcionando un servicio que sea consistente con su especificación, incluso cuando ocurren fallos. Existe una distincion entre un fault (falla interna que tiene el potencial de provocar un fallo observable) y un failure (cuando el sistema deja de proporcionar el servicio especificado y esto es observable por los actores). El objetivo de la disponibilidad es evitar que los faults se conviertan en failures, o limitar sus efectos y permitir la reparación.

- Origen del estimulo: Especifica de dónde proviene la falla. Posibles valores: Interna/externa: personas, hardware, software, infraestructura física, entorno físico.
- Estimulo: El estímulo de un escenario de disponibilidad es una falla. Posibles valores: Omisión, crash, tiempo incorrecto, respuesta incorrecta.
- Artefacto: Especifica qué partes del sistema son responsables de la falla y cuáles se ven afectadas por ella. Posibles valores: Procesadores, canales de comunicación, almacenamiento, procesos, artefactos afectados del entorno del sistema.
- Ambiente: No interesa solamente cómo se comporta el sistema en condiciones normales, sino también cómo se comporta en situaciones como cuando ya está recuperándose de una falla. Posibles valores: Operación normal, inicio, apagado, modo de reparación, operación degradada, operación sobrecargada.
- Respuesta: La respuesta más habitual es evitar que la falla se convierta en un fallo, aunque también pueden ser importantes notificar a personas o registrar la falla para analizarla posteriormente. Posibles valores: Evitar el fallo; detectar la falla; registrarla; notificar; recuperarse; deshabilitar la fuente; estar temporalmente no disponible durante una reparación; corregir/ocultar/contener la falla; operar degradadamente.
- Medida de respuesta: Se pueden utilizar diferentes medidas dependiendo de la criticidad del servicio proporcionado. Posibles valores: Tiempo/intervalo durante el que debe estar disponible, porcentaje de disponibilidad, tiempo de detección, tiempo de reparación, tiempo en modo degradado, proporción o tasa de fallas que se previenen o manejan sin fallo.

Ejemplo de escenario: Un servidor de una granja de servidores falla durante la operación normal. El sistema informa al operador y continúa funcionando sin tiempo de inactividad.

## 2. Deployability — Desplegabilidad

Descripcion general: La desplegabilidad se refiere a la capacidad de incorporar y desplegar nuevas versiones o elementos del sistema de manera rápida, controlable y eficiente, incluyendo la posibilidad de realizar un rollback cuando sea necesario.

- Origen del estimulo: Es el disparador del despliegue. Posibles valores: Usuario final, desarrollador, administrador del sistema, personal de operaciones, marketplace de componentes, propietario del producto.
- Estimulo: Es lo que provoca el disparador. Normalmente es la disponibilidad de un nuevo elemento que debe desplegarse. Posibles valores: Nuevo elemento disponible; reemplazo por una nueva versión; nuevo elemento aprobado para incorporarse; necesidad de hacer rollback de uno o varios elementos.
- Artefacto: Especifica qué se va a modificar. Posibles valores: Componentes o módulos, plataforma, interfaz de usuario, entorno, otro sistema con el que interactúa; puede ser un elemento, varios o todo el sistema.
- Ambiente: Indica dónde se realiza el despliegue. Posibles valores: Staging, producción o un subconjunto específico de cualquiera de ellos; despliegue completo o sobre un subconjunto de usuarios, VMs, contenedores, servidores o plataformas.
- Respuesta: Es lo que debería ocurrir como consecuencia del estímulo. Posibles valores: Incorporar componentes, desplegarlos, monitorearlos, hacer rollback de un despliegue anterior.
- Medida de respuesta: Es una medida del costo, tiempo o efectividad del proceso de despliegue, tanto de un despliegue individual como de una serie de ellos. Posibles valores: Cantidad/tamaño/complejidad afectados, esfuerzo promedio o peor caso, tiempo transcurrido, dinero, defectos introducidos, efectos sobre otras cualidades, cantidad de despliegues fallidos, repetibilidad, trazabilidad y tiempo de ciclo.

Ejemplo de escenario: Una nueva versión de un servicio de autenticación/autorización está disponible. El propietario del producto decide incorporarla, se prueba y se despliega a producción en menos de 40 horas y con no más de 120 horas-persona, sin introducir defectos ni violar el SLA.

## 3. Energy Efficiency — Eficiencia energética

Descripcion general: La eficiencia energética consiste en conservar o administrar la energía mientras se mantiene la funcionalidad requerida, aunque esta no necesariamente tenga que ser completa. Debe analizarse junto con otros atributos, especialmente performance y disponibilidad, porque existen intercambios entre ellos.

- Origen del estimulo: Especifica quién o qué solicita o inicia una petición para conservar o administrar energía. Posibles valores: Usuario final, administrador, administrador del sistema, agente automatizado.
- Estimulo: Es una petición para conservar energía. Posibles valores: Uso total, uso instantáneo máximo, uso promedio, etc.
- Artefacto: Especifica qué se debe administrar. Posibles valores: Dispositivos específicos, servidores, VMs, clusters, etc.
- Ambiente: La energía normalmente se administra durante la ejecución, aunque existen casos especiales dependiendo de las características del sistema. Posibles valores: Runtime, conectado, alimentado por batería, batería baja, modo de conservación de energía.
- Respuesta: Son las acciones que toma el sistema para conservar o administrar el uso de energía. Posibles valores: Deshabilitar servicios, desasignar servicios, cambiar la asignación a servidores, ejecutar en un modo de menor consumo, asignar/desasignar servidores, cambiar niveles de servicio, cambiar la planificación.
- Medida de respuesta: Las medidas giran alrededor de cuánta energía se ahorra o consume y los efectos sobre otras funciones o atributos de calidad. Posibles valores: Carga máxima/promedio en kW, energía promedio/total ahorrada, kWh totales utilizados, tiempo durante el cual el sistema debe permanecer encendido, manteniendo un nivel requerido de funcionalidad y niveles aceptables de otros atributos.

Ejemplo de escenario: Un administrador quiere ahorrar energía durante el runtime desasignando recursos que no se utilizan en períodos no pico. El sistema desasigna esos recursos manteniendo una latencia máxima de 2 segundos en consultas a la base de datos y ahorrando en promedio el 50 % de la energía requerida.

## 4. Integrability — Integrabilidad

Descripcion general: La integrabilidad consiste en identificar y reducir la distancia entre los elementos que forman posibles dependencias. Integrar componentes no solamente implica que sus interfaces tengan la misma forma: también pueden existir diferencias en datos, comportamiento, recursos y otros supuestos implícitos. En esencia, integrar consiste en discernir y tender puentes sobre las diferencias entre los elementos que necesitan interactuar.

- Origen del estimulo: Indica de dónde proviene el estímulo. Posibles valores: Stakeholder del sistema/misión, marketplace de componentes, proveedor de componentes.
- Estimulo: Indica qué tipo de integración se está describiendo. Posibles valores: Agregar un componente nuevo; integrar una nueva versión de un componente existente; integrar componentes existentes de una nueva manera.
- Artefacto: Indica qué partes del sistema están involucradas en la integración. Posibles valores: Sistema completo, conjunto específico de componentes, metadatos de componentes, configuración de componentes.
- Ambiente: Indica en qué estado se encuentra el sistema cuando ocurre el estímulo. Posibles valores: Desarrollo, integración, despliegue, runtime.
- Respuesta: Indica cómo debería responder un sistema “integrable”. Posibles valores: Los cambios son completados, integrados, probados y desplegados; los componentes intercambian información correcta y exitosamente; colaboran correctamente; no violan límites de recursos.
- Medida de respuesta: Indica cómo se mide la respuesta. Posibles valores: Costo según cantidad de componentes modificados, porcentaje de código modificado, líneas de código modificadas, esfuerzo, dinero, tiempo calendario y efectos sobre medidas de otros atributos de calidad.

Ejemplo de escenario: Un nuevo componente de filtrado de datos está disponible en el marketplace. El componente se integra y despliega durante el desarrollo en un mes, utilizando no más de un mes-persona de esfuerzo.

## 5. Modifiability — Modificabilidad

Descripcion general: La modificabilidad trata de la capacidad de realizar cambios en el sistema e incorporarlos al sistema. Hay que preguntarse qué puede cambiar, qué tan probable es ese cambio, cuándo ocurrirá y quién lo realizará.

- Origen del estimulo: Es el agente que provoca que se realice un cambio. Generalmente es una persona, aunque el propio sistema puede ser la fuente si aprende o se modifica a sí mismo. Posibles valores: Usuario final, desarrollador, administrador del sistema, propietario de una línea de productos, el propio sistema.
- Estimulo: Es el cambio que el sistema debe poder acomodar. Se considera también corregir un defecto como un cambio. Posibles valores: Agregar/eliminar/modificar funcionalidad; cambiar un atributo de calidad, capacidad, plataforma o tecnología; agregar un producto a una línea; cambiar la ubicación de un servicio.
- Artefacto: Son los artefactos que serán modificados. Posibles valores: Código, datos, interfaces, componentes, recursos, casos de prueba, configuraciones, documentación, plataforma, interfaz de usuario, entorno u otro sistema interoperante.
- Ambiente: Es el momento o etapa en que se realiza el cambio. Posibles valores: Runtime, tiempo de compilación, tiempo de construcción, tiempo de inicialización, tiempo de diseño.
- Respuesta: Consiste en realizar el cambio e incorporarlo al sistema. Posibles valores: Realizar la modificación, probarla, desplegarla, modificar el sistema automáticamente.
- Medida de respuesta: Representa los recursos utilizados para realizar el cambio. Posibles valores: Cantidad/tamaño/complejidad de artefactos afectados, esfuerzo, tiempo transcurrido, dinero, impacto sobre otras funciones o atributos, nuevos defectos, tiempo que tardó el sistema en adaptarse.

Ejemplo de escenario: Un desarrollador desea modificar la interfaz de usuario. El escenario especificaría qué artefactos se modifican, en qué momento se realiza el cambio y cuánto esfuerzo/tiempo requiere.

## 6. Performance — Rendimiento

Descripcion general: El rendimiento se refiere al tiempo y a la capacidad del sistema para cumplir requisitos temporales. Cuando ocurre un evento —una solicitud de usuario, mensaje, interrupción, solicitud de otro sistema o evento de reloj— el sistema debe responder dentro del tiempo requerido.

- Origen del estimulo: El estímulo puede provenir de un usuario, un sistema externo o una parte del propio sistema. Posibles valores: Solicitud de usuario, solicitud de sistema externo, datos de un sensor u otro sistema, solicitud de un componente a otro, notificación generada por un temporizador.
- Estimulo: Es la llegada de un evento, que puede ser una solicitud de servicio o una notificación sobre algún estado del sistema o de un sistema externo. Posibles valores: Evento periódico, esporádico o estocástico.
- Artefacto: Es la parte del sistema que recibe el estímulo. Puede ser todo el sistema o una parte. Posibles valores: Sistema completo, componente del sistema.
- Ambiente: Es el estado del sistema o componente cuando llega el estímulo. Los modos inusuales pueden modificar la respuesta. Posibles valores: Runtime: modo normal, emergencia, corrección de errores, carga máxima, sobrecarga, operación degradada u otro modo definido.
- Respuesta: El sistema procesa el estímulo. Ese procesamiento requiere tiempo, ya sea por cálculo o por espera debido a recursos compartidos. Posibles valores: Responder, devolver un error, no responder, ignorar una solicitud durante sobrecarga, cambiar el modo/nivel de servicio, atender un evento de mayor prioridad, consumir recursos.
- Medida de respuesta: Las medidas pueden representar el tiempo o la cantidad de trabajo procesado y también el uso de recursos. Posibles valores: Latencia, throughput, jitter, cumplimiento de deadlines, cantidad de solicitudes no satisfechas, utilización de CPU, memoria, thread pool, buffers, etc.

Ejemplo de escenario: 500 usuarios generan 2.000 solicitudes durante un intervalo de 30 segundos. El sistema está funcionando normalmente, procesa todas las solicitudes y obtiene una latencia promedio de 2 segundos.

## 7. Safety — Seguridad física

Descripcion general: Safety se refiere a la capacidad del sistema de evitar entrar en estados que provoquen o puedan provocar daño, lesiones o pérdida de vidas a los actores de su entorno. También se ocupa de detectar y recuperarse de estados inseguros para prevenir o minimizar el daño. 

- Origen del estimulo: Es una fuente de datos, una fuente de tiempo o una acción de usuario. Posibles valores: 
- Estimulo: Es una omisión, comisión o aparición de datos o tiempos incorrectos. Posibles valores: Un valor nunca llega; una función nunca se ejecuta; una función se ejecuta incorrectamente; evento espurio; datos incorrectos; sensor incorrecto; resultados incorrectos; datos/eventos demasiado tarde o demasiado temprano; frecuencia incorrecta; orden incorrecto.
- Ambiente: Es el modo de funcionamiento del sistema cuando ocurre el estímulo. Posibles valores: Operación normal, operación degradada, operación manual, modo de recuperación.
- Artefacto: Es alguna parte del sistema. Posibles valores: Partes críticas para la seguridad (safety-critical portions).
- Respuesta: El sistema no debe abandonar un espacio de estados seguro, debe regresar a él o continuar operando degradadamente para evitar o minimizar lesiones o daños. También debe informar al usuario y registrar el evento. Posibles valores: 
- Medida de respuesta: Mide qué tan rápidamente y eficazmente el sistema vuelve a un estado seguro o evita el daño. Posibles valores: Tiempo para volver al estado seguro, cantidad/proporción de estados inseguros evitados, porcentaje recuperado, cambio en exposición al riesgo, tiempo durante el que puede recuperarse, tiempo en modo seguro/degradado, tiempo de apagado, etc.

Ejemplo de escenario: Un sensor de un sistema de monitoreo de pacientes deja de informar un valor crítico después de 100 ms. El fallo se registra, se genera una advertencia y se activa un sensor de respaldo. El sistema continúa monitoreando al paciente y debe hacerlo dentro de los 300 ms.

## 8. Security — Seguridad informática

Descripcion general: Security busca proteger principalmente confidencialidad, integridad y disponibilidad (CIA) frente a ataques. Un ataque es un intento de comprometer alguno de estos aspectos.

- Origen del estimulo: El ataque puede provenir del exterior o interior de la organización. Puede provenir de una persona o de otro sistema, y la fuente puede estar identificada o ser desconocida. Posibles valores: Humano; otro sistema; dentro/fuera de la organización; previamente identificado/desconocido.
- Estimulo: El estímulo es un ataque. Posibles valores: Intento no autorizado de mostrar datos, capturarlos, modificarlos/eliminarlos, acceder a servicios, cambiar el comportamiento del sistema o reducir la disponibilidad.
- Ambiente: Es el estado del sistema cuando ocurre el ataque. Posibles valores: Online/offline, conectado/desconectado de una red, detrás de un firewall/abierto a la red, completamente operativo/parcialmente operativo/no operativo.
- Artefacto: Es el objetivo del ataque. Posibles valores: Servicios del sistema, datos del sistema, componentes/recursos, datos producidos o consumidos por el sistema.
- Respuesta: El sistema debe mantener confidencialidad, integridad y disponibilidad. También debe registrar las actividades y notificar cuando detecta un posible ataque. Posibles valores: Proteger datos/servicios, impedir modificaciones no autorizadas, identificar las partes de una transacción, impedir repudio, mantener disponibilidad, registrar accesos/modificaciones, registrar intentos y notificar.
- Medida de respuesta: Las medidas están relacionadas con la frecuencia de ataques exitosos, el tiempo y costo para resistir/reparar ataques y el daño producido. Posibles valores: Recursos comprometidos/protegidos, precisión de detección, tiempo hasta detectar un ataque, ataques resistidos, tiempo de recuperación, cantidad de datos vulnerables. 

Ejemplo de escenario: Un empleado descontento intenta modificar de manera indebida una tabla de salarios. El acceso no autorizado es detectado y queda registrado en una auditoría; los datos correctos son restaurados dentro de un día.

## 9. Testability — Testabilidad

Descripcion general: La testabilidad se refiere a qué tan fácil es realizar pruebas sobre el sistema, controlar el estado que se quiere probar, observar los resultados y descubrir fallos.

- Origen del estimulo: Los casos de prueba pueden ser ejecutados por una persona o una herramienta automática de pruebas. Posibles valores: Testers unitarios, de integración, de sistema, de aceptación, usuarios finales; pruebas manuales o automatizadas.
- Estimulo: Se inicia una prueba o conjunto de pruebas. Estas sirven para validar funciones, validar cualidades o descubrir nuevas amenazas a la calidad. Posibles valores: Validar funciones, validar atributos de calidad, descubrir amenazas emergentes.
- Ambiente: Las pruebas ocurren en diferentes eventos o hitos del ciclo de vida. Posibles valores: Finalización de un incremento de código, integración de un subsistema, implementación completa del sistema, despliegue en producción, entrega al cliente, calendario de pruebas.
- Artefacto: Es la parte del sistema que se prueba y cualquier infraestructura necesaria para realizar la prueba. Posibles valores: Unidad de código, componentes, servicios, subsistemas, sistema completo, infraestructura de pruebas.
- Respuesta: El sistema y la infraestructura de pruebas deben poder controlarse para realizar las pruebas deseadas y observar sus resultados. Posibles valores: Ejecutar la suite y capturar resultados, capturar la actividad que produjo el fallo, controlar y monitorear el estado del sistema.
- Medida de respuesta: Busca representar qué tan fácilmente el sistema bajo prueba revela sus fallos o defectos. Posibles valores: Esfuerzo para encontrar un fallo, esfuerzo para alcanzar determinado porcentaje de cobertura de estados, probabilidad de que la próxima prueba revele un fallo, tiempo de pruebas, esfuerzo de detección, tiempo de preparación de infraestructura, esfuerzo para llevar el sistema a un estado específico, reducción de exposición al riesgo.

Ejemplo de escenario: Un desarrollador termina una unidad de código y realiza una secuencia de pruebas cuyos resultados son capturados, obteniendo un 85 % de cobertura de caminos en 30 minutos.

## 10. Usability — Usabilidad

Descripcion general: La usabilidad se ocupa de qué tan fácil es para el usuario realizar una tarea deseada y del tipo de soporte que proporciona el sistema.

- Origen del estimulo: El usuario final, posiblemente desempeñando un rol especializado, es la fuente principal del estímulo. También puede serlo un evento externo al sistema al que el usuario reacciona. Posibles valores: 
- Estimulo: Es lo que el usuario final quiere conseguir. Posibles valores: Utilizar el sistema eficientemente, aprender a utilizarlo, minimizar el impacto de errores, adaptar el sistema, configurar el sistema.
- Ambiente: Las acciones del usuario relacionadas con la usabilidad ocurren durante la ejecución o configuración del sistema. Posibles valores: Runtime, configuración del sistema.
- Artefacto: Es la parte del sistema que recibe la interacción del usuario. Posibles valores: GUI, interfaz de línea de comandos, interfaz de voz, pantalla táctil.
- Respuesta: El sistema debe responder proporcionando las funcionalidades necesarias, anticipándose a las necesidades del usuario y proporcionando retroalimentación apropiada. Posibles valores: Proporcionar funcionalidades, anticipar necesidades, proporcionar feedback apropiado.
- Medida de respuesta: Mide cómo responde el sistema desde la perspectiva de la interacción del usuario. Posibles valores: Tiempo de tarea, cantidad de errores, tiempo de aprendizaje, relación entre tiempo de aprendizaje y tiempo de tarea, cantidad de tareas realizadas, satisfacción, conocimiento adquirido, proporción de operaciones exitosas, tiempo/datos perdidos por errores.

Ejemplo de escenario: Un usuario descarga una nueva aplicación y consigue utilizarla productivamente después de solamente 2 minutos de experimentación.


Fuente: *Software Architecture in Practice*, Fourth Edition, capítulos 4–13.
