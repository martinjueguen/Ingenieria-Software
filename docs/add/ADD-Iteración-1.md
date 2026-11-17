# Paso 2: Establecemos los objetivos de la iteración seleccionando los drivers
En esta iteración vamos a definir la arquitecura inicial del sistema, por esto atacaremos el **driver CRN-1** (Definición de la estructura del sistema).
Para elegir la aquitectura de referencia o estructura general del sistema vamos a tener en cuenta principalmente los atributos de calidad con mayor prioridad:

- QA-R1: Propagación de actualizaciones (H,H)
- QA-D1: Caída de una región (H,H)
- QA-E1: Pico por disrupción masiva (H,H)
- QA-S2: Compromiso del acceso al correo (H,H)

*(Importancia para el negocio, Dificultad de implementacion)  
*H=High (alta)  
*M=Medium (media)  
*L=low (baja)  

# Paso 3: Elección de elemento/s a refinar

Dado que nos encontramos desarrollando un sistema greenfield, vamos a refinar el sistema completo
[[DiagramaDeContexto]]

# Paso 4: Elección de uno o mas conceptos de diseño para satisfacer los drivers seleccionados

## Alternativa 1: Arquitectura cliente-servidor monolítica

Los clientes web y móviles se comunicarían con un único backend que concentraría la lógica de negocio, el procesamiento de correos electrónicos y las integraciones con las APIs de terceros. Todos estos módulos formarían parte de una única unidad desplegable.

### Pros

- **Simplicidad:** es una arquitectura más sencilla de desarrollar, probar y desplegar, ya que los componentes forman parte de una misma aplicación.
- **Facilidad de comunicación:** los módulos pueden comunicarse directamente dentro del backend, sin necesidad de implementar un sistema de mensajería.
- **Consistencia de los datos:** es más sencillo coordinar las operaciones que modifican las reservas y los itinerarios dentro de una misma aplicación.

### Contras

- **Escalabilidad:** si aumenta el procesamiento de correos o las consultas a proveedores externos, puede ser necesario replicar la aplicación completa, aunque solo una parte necesite más recursos.
- **Disponibilidad:** al concentrar las funcionalidades en una misma unidad, un error puede afectar a gran parte del sistema. Aunque es posible utilizar varias instancias para reducir este riesgo, existe un mayor acoplamiento entre las funcionalidades.
- **Rendimiento:** las tareas pesadas, como el análisis de correos y las consultas analíticas, pueden competir por los mismos recursos que las operaciones que necesitan respuestas rápidas para los usuarios.
- **Mantenibilidad y evolucionabilidad:** las modificaciones en una integración externa pueden causar que haya que reconstruir y desplegar la aplicación completa, aunque el cambio afecte a una funcionalidad específica.
- **Interoperabilidad:** la incorporación de nuevos proveedores o medios de transporte puede aumentar el acoplamiento entre los módulos.

## Alternativa 2: Arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos

Los clientes web y móviles se comunicarían con un backend mediante un modelo cliente-servidor. Sin embargo, los procesos internos que no necesitan completarse durante la solicitud del usuario, como los correos electrónicos, el procesamiento de actualizaciones de vuelos y la generación de datos analíticos, se ejecutarían de forma asíncrona mediante eventos.

Los componentes publicarían y consumirían eventos a través de un sistema de mensajería, evitando que los procesos internos dependan de una comunicación síncrona bloqueante entre sí.

### Pros

- **Rendimiento y latencia:** las consultas de los usuarios se atenderían directamente desde el servidor, mientras que las tareas más lentas, como el análisis de correos y la consulta de proveedores externos, se procesarían en segundo plano. Esto ayuda a cumplir los tiempos de respuesta exigidos para la web y los dispositivos móviles.
- **Escalabilidad:** sería posible aumentar los recursos de los consumidores que procesan grandes volúmenes de correos, actualizaciones o datos analíticos sin tener que escalar todos los componentes del sistema.
- **Disponibilidad y tolerancia a fallos:** si un proveedor externo deja de responder, los procesos dependientes de él pueden reintentarse posteriormente. Para ello, el sistema de mensajería debe contar con almacenamiento persistente de eventos y mecanismos de reintento.
- **Interoperabilidad:** las integraciones con proveedores de viajes, servicios de correo y redes sociales pueden implementarse mediante componentes específicos que intercambien eventos con el resto del sistema.
- **Evolucionabilidad y mantenibilidad:** la incorporación de nuevos medios de transporte o proveedores puede realizarse agregando nuevos componentes consumidores o adaptadores, siempre que respeten los contratos de comunicación establecidos.
- **Aislamiento de responsabilidades:** el procesamiento de correos, la actualización de reservas y la analítica pueden ejecutarse de forma independiente, reduciendo la interferencia entre las operaciones principales y las tareas pesadas.

### Contras

- **Mayor complejidad inicial:** es necesario diseñar los eventos, definir sus contratos y configurar la infraestructura de mensajería, además de implementar los mecanismos de reintento y monitoreo.
- **Consistencia eventual:** las actualizaciones recibidas desde un proveedor no siempre estarán disponibles inmediatamente, ya que deben pasar por el procesamiento asíncrono. Es necesario controlar que se cumpla el límite de actualización de 5 minutos.
- **Dependencia de la infraestructura de mensajería:** si el sistema de mensajería falla o se satura, el procesamiento puede retrasarse.
- **Mayor esfuerzo de monitoreo:** es necesario supervisar las colas, los retrasos, los errores de procesamiento y los reintentos para detectar problemas y asegurar que los eventos se procesen dentro de los plazos establecidos.

## Elección: Alternativa 2

Elegimos la **arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos**, ya que se adapta mejor a los atributos de calidad más prioritarios del sistema Trotamundos.

La arquitectura se divide en dos partes principales. Por un lado, el modelo cliente-servidor permite separar la interfaz de usuario de la lógica del backend y atender rápidamente las consultas y operaciones que necesitan una respuesta inmediata. Por otro lado, la arquitectura orientada a eventos permite ejecutar en segundo plano los procesos que pueden resultar lentos o consumir muchos recursos, sin bloquear las solicitudes de los usuarios.

Esta elección favorece el cumplimiento de los principales atributos de calidad:

- **Rendimiento:** las consultas se atienden directamente desde el servidor, mientras que el procesamiento de correos, las actualizaciones externas y las tareas analíticas se realizan de forma asíncrona.
- **Disponibilidad:** los mecanismos de mensajería persistente y reintento permiten recuperarse de fallos temporales de los proveedores externos sin perder los eventos pendientes de procesamiento.
- **Escalabilidad:** los componentes que reciben más carga pueden escalarse de manera independiente para responder a los picos de actividad, como los que se producen ante interrupciones importantes de viajes.
- **Interoperabilidad:** las integraciones con correos electrónicos, aerolíneas, hoteles y redes sociales pueden organizarse en componentes específicos que se comuniquen mediante contratos definidos.
- **Evolucionabilidad y mantenibilidad:** los contratos de los eventos permiten incorporar nuevos proveedores y medios de transporte reduciendo el impacto sobre los componentes existentes.


# Paso 5: Registrar decisiones de diseño
Las decisiones de diseño consideradas y adoptadas durante esta iteración se resumen en la siguiente tabla:  
| Decisión de diseño y ubicación | Justificación |
|---|---|
| **Separar los clientes web y móvil del backend.** | Permite separar las interfaces de usuario de la lógica de negocio y evolucionar cada cliente de manera independiente. Además, facilita optimizar los tiempos de respuesta requeridos para las plataformas web y móvil. |
| **Crear un módulo de gestión de viajes y reservas.**| Centraliza las operaciones de creación, modificación, eliminación y consulta de viajes y reservas, evitando duplicar lógica. También facilita incorporar nuevos medios de transporte, favoreciendo la mantenibilidad y la evolucionabilidad. |
| **Incorporar un sistema de mensajería con procesamiento asíncrono.**| Permite ejecutar en segundo plano tareas como el procesamiento de correos y las actualizaciones de reservas, evitando que bloqueen las solicitudes de los usuarios. La persistencia de eventos y los mecanismos de reintento contribuyen a la disponibilidad y al cumplimiento del límite de actualización. |
| **Crear un módulo de integración con proveedores externos.**| Encapsula la comunicación con proveedores de correo, aerolíneas, hoteles y otros servicios mediante adaptadores específicos. Esto reduce el acoplamiento con las APIs externas y facilita incorporar nuevos proveedores, favoreciendo la interoperabilidad y la evolucionabilidad. |
| **Separar el procesamiento analítico de la persistencia operativa.**| Las consultas analíticas pueden consumir muchos recursos y perjudicar las operaciones habituales. Separar ambos tipos de procesamiento permite ejecutar análisis de tendencias, destinos y cancelaciones sin interferir directamente con la gestión de los viajes, favoreciendo el rendimiento y la escalabilidad. |
| **Incorporar mecanismos de autenticación y autorización.**| Permite controlar el acceso a la información personal, proteger las cuentas de correo conectadas y garantizar que únicamente las personas autorizadas puedan consultar itinerarios compartidos. Esta decisión responde a los requerimientos de seguridad y privacidad. |

# Paso 6: Vistas e instanciación de elementos y responsabilidades

## Asignación de responsabilidades

### Diagrama de modulos

[Diagrama de modulos](https://github.com/martinjueguen/Ingenieria-Software/wiki/ADD-%E2%80%90-Iteraci%C3%B3n-1-%E2%80%90-Digramas#diagrama-de-modulos)  
<img width="99" height="152" alt="image" src="https://github.com/user-attachments/assets/d4997be6-3421-4f16-b5d3-0b430b01e7e0" />  

### Capa 1: Cliente

**Interfaz web**
- Proporcionar la interfaz para que los usuarios consulten y administren sus viajes y reservas.
- Permitir la consulta del itinerario y la gestión manual de las reservas.
- Enviar solicitudes al backend y presentar las respuestas recibidas.
- Mostrar las actualizaciones de los viajes disponibles en el sistema.

**Aplicación móvil**
- Proporcionar acceso a las funcionalidades principales de Trotamundos desde dispositivos móviles.
- Permitir consultar y administrar los viajes y sus reservas.
- Comunicarse con el backend mediante la API.
- Adaptar la presentación y la interacción a las capacidades y características de los dispositivos móviles.

### Capa 2: Servidor de aplicaciones

**Seguridad y control de acceso**
- Verificar la identidad del usuario antes de permitirle acceder a las funcionalidades protegidas.
- Controlar los permisos necesarios para consultar y modificar la información de cada usuario.
- Proteger la información personal y el acceso a los correos electrónicos vinculados.
- Garantizar que los itinerarios compartidos solo puedan ser consultados por las personas autorizadas.

**API / Acceso al sistema**
- Actuar como punto de entrada para las solicitudes provenientes de la interfaz web y la aplicación móvil.
- Recibir las solicitudes, validar su estructura y derivarlas a los módulos correspondientes.
- Coordinar el acceso a las funcionalidades de gestión de viajes y reservas.
- Devolver las respuestas al cliente y evitar que las interfaces dependan directamente de la implementación interna del backend.

**Gestión de viajes y reservas**
- Implementar la lógica de negocio relacionada con los viajes y las reservas.
- Permitir crear, consultar, actualizar y eliminar reservas manualmente.
- Organizar los distintos elementos de viaje dentro de itinerarios.
- Incorporar las actualizaciones de reservas recibidas desde los proveedores externos.
- Gestionar el ciclo de vida de los viajes, archivando o retirando de la vista principal aquellos que hayan finalizado.
- Mantener la información necesaria para que los usuarios consulten sus itinerarios actualizados.

**Integración con servicios externos**
- Encapsular la comunicación con proveedores de correo electrónico, aerolíneas, hoteles, empresas de alquiler de vehículos y otros servicios turísticos.
- Consumir las APIs externas para obtener información sobre reservas, modificaciones y cancelaciones.
- Facilitar la integración con la agencia de viajes preferida del usuario para resolver problemas relacionados con sus viajes.
- Permitir la integración con redes sociales para compartir itinerarios, respetando los permisos establecidos.
- Transformar las respuestas de los proveedores a formatos internos que puedan ser utilizados por el resto del sistema.
- Reducir el acoplamiento con las particularidades de cada proveedor, facilitando la incorporación futura de nuevos servicios y medios de transporte.

**Procesamiento asíncrono**
- Ejecutar en segundo plano las tareas que no necesitan completarse durante una solicitud del usuario.
- Procesar los correos electrónicos recibidos para identificar información relacionada con viajes y reservas.
- Coordinar el procesamiento de actualizaciones provenientes de fuentes externas.
- Aplicar las modificaciones correspondientes a los viajes y las reservas almacenados.
- Ejecutar tareas periódicas, como la revisión del ciclo de vida de los viajes y el archivado de aquellos que hayan finalizado.
- Realizar trabajos de procesamiento intensivo y analítica sin bloquear directamente las solicitudes interactivas.
- Gestionar los fallos temporales mediante mecanismos de reintento y colaborar con la infraestructura de mensajería para procesar los eventos pendientes.

### Capa 3: Datos

**Comunicación con almacenamiento**
- Proporcionar un punto de acceso a los datos persistidos del sistema.
- Ejecutar las operaciones de lectura y escritura solicitadas por los módulos de negocio y los procesos en segundo plano.
- Encapsular los detalles de acceso a la base de datos, evitando que los módulos dependan directamente de su implementación.
- Facilitar que la gestión de viajes y el procesamiento asíncrono compartan el acceso controlado a la información persistida.

**Base de datos**
- Persistir la información operativa necesaria para el funcionamiento de Trotamundos, incluyendo usuarios, viajes y reservas.
- Mantener la información utilizada para reconstruir y consultar los itinerarios.
- Conservar los datos necesarios para aplicar las modificaciones realizadas por los usuarios y las actualizaciones recibidas desde los proveedores.
- Servir como fuente de información persistente para las consultas realizadas desde las interfaces y para los procesos internos.

### Sistemas externos

**Proveedores externos de correo, servicios turísticos y redes sociales**
- Proporcionar información externa relacionada con los viajes de los usuarios.
- Permitir consultar actualizaciones, modificaciones y cancelaciones mediante las APIs disponibles.
- Facilitar la obtención de información sobre reservas a partir de los correos electrónicos.
- Permitir las interacciones previstas con las agencias de viajes y las redes sociales.

### Diagrama de componentes y conectores

[Diagrama de componentes y conectores](https://github.com/martinjueguen/Ingenieria-Software/wiki/ADD-%E2%80%90-Iteraci%C3%B3n-1-%E2%80%90-Digramas#diagrama-de-componentes-y-conectores)  
<img width="99" height="152" alt="image" src="https://github.com/user-attachments/assets/d0bafa80-2d2f-4447-bb4c-edd1911d5eed" />  

**Usuario**
- Interactuar con Trotamundos a través de la interfaz web o la aplicación móvil.
- Iniciar consultas y operaciones sobre sus viajes y reservas.

**Web / Aplicación móvil**
- Presentar las funcionalidades del sistema al usuario.
- Enviar solicitudes al servidor de aplicaciones y mostrar las respuestas recibidas.

**Servidor de aplicaciones**
- Recibir y atender las solicitudes de los clientes.
- Coordinar la validación de acceso y la ejecución de la lógica de negocio.
- Realizar operaciones de lectura y escritura a través del componente de comunicación con almacenamiento.
- Publicar eventos cuando determinadas operaciones requieren procesamiento adicional en segundo plano.

**Integraciones externas**
- Comunicarse con los proveedores externos mediante sus APIs.
- Obtener información sobre reservas y sus actualizaciones.
- Adaptar los datos recibidos y publicar eventos para que puedan ser procesados por otros componentes.

**Proveedores externos**
- Proporcionar las APIs y los servicios de terceros utilizados por Trotamundos, como proveedores turísticos y servicios de correo electrónico.
- Responder a las consultas e integraciones realizadas por el sistema.

**Bus de eventos**
- Recibir los eventos publicados por el servidor de aplicaciones y los componentes de integración.
- Desacoplar a los componentes que generan eventos de aquellos que deben procesarlos.
- Entregar los mensajes a los consumidores correspondientes sin requerir una comunicación síncrona entre ellos.
- Proporcionar persistencia de mensajes y mecanismos de reintento para contribuir a la tolerancia a fallos y evitar la pérdida de trabajo pendiente.

**Procesamiento en segundo plano**
- Consumir los mensajes recibidos desde el bus de eventos.
- Ejecutar las tareas asíncronas derivadas de las operaciones del sistema y de las actualizaciones externas.
- Procesar la información para actualizar las reservas y los itinerarios.
- Realizar trabajos que requieren más tiempo o recursos sin bloquear al servidor de aplicaciones.
- Acceder a la información persistida para consultar o aplicar las modificaciones correspondientes.

**Comunicación con almacenamiento**
- Actuar como intermediario entre los componentes de la aplicación y la base de datos.
- Ejecutar las operaciones de lectura y escritura necesarias para la gestión y actualización de los datos.

**Base de datos**
- Almacenar de forma persistente los datos operativos.
- Proporcionar los datos solicitados a través del componente de comunicación con almacenamiento.  

## Conectores y comunicación entre componentes

Los principales mecanismos de comunicación representados en la vista son los siguientes:

| Conector | Responsabilidad |
|---|---|
| **Solicitudes y respuestas** | Comunicar la interfaz web o móvil con el servidor de aplicaciones mediante un intercambio directo de solicitudes y respuestas. |
| **APIs externas** | Permitir la comunicación entre el componente de integraciones externas y los proveedores de terceros. |
| **Publicación de eventos** | Permitir que el servidor de aplicaciones comunique operaciones que requieren procesamiento posterior. |
| **Eventos hacia el bus** | Permitir que las integraciones externas publiquen información que debe ser procesada por otros componentes. |
| **Mensajes asíncronos** | Transportar los eventos desde el bus hasta el componente de procesamiento en segundo plano, sin bloquear al productor mientras se ejecuta el trabajo. |
| **Lectura y escritura** | Permitir que el servidor de aplicaciones y el procesamiento en segundo plano accedan a los datos mediante el componente de comunicación con almacenamiento. |
| **Acceso a la base de datos** | Conectar el componente de comunicación con almacenamiento con la base de datos para persistir y recuperar la información. |


# Paso 7: Revisión de los drivers atacados y del logro del objetivo de la iteración

Dado que conseguimos una estructura inicial del sistema (se eligió una arquitectura cliente-servidor con procesamiento asíncrono orientado a eventos), el CRN-1 se considera **completamente cumplido**, por lo que el objetivo de la iteración lo fue también. 

### Estado de los Drivers:
- **CRN-1 (Estructura general del sistema):** Totalmente satisfecho. Se definieron las capas principales (Cliente, Servidor de Aplicaciones, Datos) y el bus de eventos desacoplado.
- **QA-R1 (Propagación de actualizaciones):** Parcialmente satisfecho. El desacoplamiento mediante bus de eventos sienta las bases para procesar actualizaciones externas sin trabar al sistema, pero resta diseñar en detalle los conectores y consumidores.
- **QA-D1 (Caída de una región):** Parcialmente satisfecho. La separación en componentes desacoplados y stateless facilitará su replicación en fases posteriores.
- **QA-E1 (Pico por disrupción masiva):** Parcialmente satisfecho. El bus de eventos absorbe ráfagas de trabajo pesado, protegiendo a las bases transaccionales.
- **QA-S2 (Compromiso de acceso al correo):** Parcialmente satisfecho. Se identificó el módulo de seguridad y control de acceso como barrera transversal.