1. Efficiency — Eficiencia
¿En qué consiste?

La eficiencia indica qué tan bien utiliza el sistema los recursos disponibles para realizar sus tareas.

Los recursos pueden ser:

CPU.
Memoria RAM.
Batería.
Almacenamiento.
Ancho de banda.
Tiempo de procesamiento.

Un sistema eficiente consigue realizar una tarea sin desperdiciar recursos innecesariamente.

¿Cómo identificarla?

Busca escenarios donde aparezcan expresiones como:

"consume poca memoria".
"utiliza poca batería".
"reduce el consumo de datos".
"procesa una tarea utilizando pocos recursos".
"puede atender muchas operaciones sin consumir excesivamente los recursos".
Ejemplo

Escenario: Una aplicación de mapas se utiliza durante un viaje de 5 horas.

La aplicación deberá proporcionar navegación durante todo el viaje consumiendo una cantidad mínima de batería y datos móviles.

Aquí el atributo principal es Efficiency, porque estamos evaluando el consumo de recursos.

Pregunta clave

¿Cuántos recursos necesita el sistema para realizar su trabajo?

2. Functionality — Funcionalidad
¿En qué consiste?

La funcionalidad representa lo que el sistema debe hacer.

Se refiere a las funciones, operaciones y comportamientos que el sistema proporciona para satisfacer las necesidades del usuario.

Por ejemplo, en una aplicación bancaria:

Iniciar sesión.
Consultar saldo.
Transferir dinero.
Pagar servicios.
Descargar comprobantes.
¿Cómo identificarla?

Busca escenarios donde se describa:

Una función que el sistema debe realizar.
Una operación que el usuario necesita ejecutar.
Una validación.
Un cálculo.
Una regla de negocio.
Un resultado esperado.
Ejemplo

Escenario: Un cliente quiere transferir dinero.

El usuario introduce los datos del destinatario y el monto. El sistema debe validar la información, realizar la transferencia y mostrar un comprobante.

El atributo principal es Functionality, porque estamos preguntando:

¿El sistema hace correctamente lo que se supone que debe hacer?

Pregunta clave

¿Qué debe hacer el sistema?

3. Maintainability — Mantenibilidad
¿En qué consiste?

La mantenibilidad indica qué tan fácil es modificar, corregir, actualizar o mejorar un sistema después de que ha sido desarrollado.

Un sistema mantenible permite que los desarrolladores realicen cambios sin tener que modificar grandes cantidades de código o introducir nuevos errores.

Por ejemplo, una empresa quiere agregar una nueva forma de pago. Si el sistema está bien diseñado, debería poder incorporarse sin reconstruir toda la aplicación.

¿Cómo identificarla?

Busca escenarios relacionados con:

Corrección de errores.
Modificación del sistema.
Actualizaciones.
Incorporación de nuevas funcionalidades.
Cambios en reglas de negocio.
Tiempo necesario para realizar modificaciones.
Facilidad para comprender el código.
Ejemplo

Escenario: Una tienda online quiere agregar un nuevo método de pago.

Los desarrolladores deben poder incorporar el nuevo método de pago sin modificar los módulos de inventario, usuarios y pedidos.

El atributo es Maintainability, porque estamos evaluando qué tan fácil es modificar el sistema.

Pregunta clave

¿Qué tan fácil es cambiar o corregir el sistema?

4. Portability — Portabilidad
¿En qué consiste?

La portabilidad indica qué tan fácilmente un sistema puede funcionar en diferentes entornos.

El entorno puede cambiar en términos de:

Sistema operativo.
Hardware.
Dispositivo.
Navegador.
Plataforma.
Configuración.

Por ejemplo, una aplicación puede estar diseñada para funcionar tanto en Android como en iOS.

¿Cómo identificarla?

Busca escenarios donde aparezcan:

Android / iOS.
Windows / Linux / macOS.
Diferentes dispositivos.
Diferentes navegadores.
Migración de un servidor a otro.
Diferentes configuraciones de hardware.
Ejemplo

Escenario: Una aplicación de videollamadas debe utilizarse en diferentes dispositivos.

La aplicación deberá funcionar correctamente en teléfonos Android, iPhone, tablets y computadoras, manteniendo sus funcionalidades principales.

El atributo es Portability, porque estamos evaluando la capacidad de funcionar en diferentes entornos.

Pregunta clave

¿Puede el sistema funcionar en diferentes plataformas o entornos?

5. Reliability — Confiabilidad
¿En qué consiste?

La confiabilidad indica qué tan capaz es el sistema de funcionar correctamente durante un período determinado y ante determinadas condiciones, sin fallar.

No basta con que el sistema funcione una vez. Debe poder hacerlo de manera consistente.

Por ejemplo, en una aplicación bancaria, una transferencia no debería desaparecer, duplicarse o quedar en un estado incorrecto si se pierde la conexión.

¿Cómo identificarla?

Busca escenarios relacionados con:

Fallos.
Errores.
Caídas del sistema.
Pérdida de conexión.
Recuperación ante errores.
Disponibilidad.
Operaciones que deben completarse correctamente.
Funcionamiento continuo.
Ejemplo

Escenario: Un usuario realiza una transferencia bancaria y pierde la conexión a Internet.

Si la conexión se interrumpe durante una transferencia, el sistema deberá determinar correctamente el estado de la operación y evitar que la transferencia se realice dos veces.

El atributo es Reliability, porque estamos evaluando qué sucede cuando ocurre un fallo.

Pregunta clave

¿El sistema continúa funcionando correctamente y evita comportamientos incorrectos cuando algo falla?

6. Usability — Usabilidad
¿En qué consiste?

La usabilidad indica qué tan fácil es para una persona aprender, comprender y utilizar correctamente el sistema.

Un sistema puede tener muchas funcionalidades y funcionar técnicamente bien, pero ser difícil de utilizar.

Por ejemplo, una aplicación bancaria puede tener una función para realizar transferencias, pero si el usuario no puede encontrarla o no entiende qué información debe introducir, tiene un problema de usabilidad.

¿Cómo identificarla?

Busca escenarios relacionados con:

Facilidad de uso.
Interfaz intuitiva.
Facilidad de aprendizaje.
Claridad de los mensajes.
Navegación.
Accesibilidad.
Cantidad de pasos necesarios.
Errores cometidos por los usuarios.
Ejemplo

Escenario: Un usuario nuevo quiere realizar una transferencia.

Un usuario que nunca ha utilizado la aplicación debe poder realizar una transferencia sin recibir capacitación y siguiendo instrucciones claras en la interfaz.

El atributo es Usability, porque estamos evaluando qué tan fácil resulta utilizar el sistema.

Pregunta clave

¿Qué tan fácil es para el usuario aprender y utilizar el sistema?

¿Cómo identificar un atributo de calidad en un escenario?

Una técnica muy útil es buscar qué aspecto del sistema se está intentando evaluar.

Si el escenario habla de...	Probablemente es...
Consumo de CPU, memoria, batería, datos	Efficiency
Funciones que el sistema debe realizar	Functionality
Modificar, corregir o actualizar el sistema	Maintainability
Diferentes sistemas operativos o plataformas	Portability
Fallos, errores, recuperación o funcionamiento continuo	Reliability
Facilidad de uso, aprendizaje o navegación	Usability
Ejemplo para diferenciarlos

Imagina una aplicación bancaria. Una misma aplicación puede tener los seis atributos:

Efficiency: La aplicación consume poca batería mientras está en uso.
Functionality: La aplicación permite realizar transferencias.
Maintainability: Los desarrolladores pueden agregar nuevas funcionalidades fácilmente.
Portability: La aplicación funciona tanto en Android como en iOS.
Reliability: Una transferencia no se duplica si se pierde la conexión.
Usability: Un usuario puede realizar una transferencia sin necesitar ayuda.

La clave está en qué propiedad estás evaluando, no simplemente en qué aplicación estás hablando.

Una fórmula para construir escenarios

Para ejercicios académicos, puedes pensar en un escenario utilizando esta estructura:

Cuando [estímulo] ocurre en [entorno], el sistema deberá [respuesta], cumpliendo [métrica o condición].

Por ejemplo:

Cuando 10.000 usuarios accedan simultáneamente a una tienda online durante una promoción, el sistema deberá procesar las búsquedas de productos en menos de 2 segundos en el 95% de los casos.

Aquí puedes identificar:

Estímulo: 10.000 usuarios acceden simultáneamente.
Entorno: Promoción de la tienda online.
Respuesta: Procesar y mostrar las búsquedas.
Métrica: Menos de 2 segundos en el 95% de los casos.
Atributo: Performance/Rendimiento.

Esta estructura te sirve para convertir una descripción general como "el sistema debe ser confiable" en un escenario concreto, medible y comprobable.