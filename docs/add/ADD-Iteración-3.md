# Paso 2: Establecemos los objetivos de la iteración seleccionando los drivers

El objetivo de esta iteración es diseñar en detalle el subsistema de **Integración con servicios externos** y el **Procesamiento asíncrono**, resolviendo el escaneo automático de correos, la conexión con APIs de proveedores turísticos (aerolíneas, hoteles, agencias) y la protección de los datos de acceso del usuario.

**Drivers seleccionados:**
- **US-01:** Procesamiento de correo electrónico (sondeo y extracción automática de reservas)
- **US-02:** Filtros y lista blanca / *whitelist* (lectura exclusiva de remitentes autorizados)
- **US-03:** Integración de reservas con APIs de terceros (obtener cambios y cancelaciones de aerolíneas/hoteles)
- **US-06:** Resolución de problemas con agencia preferida (conectar con soporte enviando el contexto del viaje)
- **QA-R1:** Propagación de actualizaciones (H,H)
- **QA-I1:** Nuevo proveedor de viajes (H,M)
- **QA-I2:** Nuevo proveedor de correo y red social (M,M)
- **QA-S2:** Compromiso del acceso al correo (H,H)
- **QA-D2:** Falla de un proveedor externo (H,M)

# Paso 3: Elección de elemento/s a refinar

Refinaremos los siguientes componentes identificados en las iteraciones anteriores:
1. **Módulo "Integración con servicios externos"** (Capa 2).
2. **Módulo "Procesamiento asíncrono" y "Bus de eventos"** (Capa 2).
3. **Módulo "Seguridad y control de acceso"** (Capa 2).

# Paso 4: Elección de uno o más conceptos de diseño para satisfacer los drivers seleccionados

## Concepto 1: Capa de adaptadores con modelo canónico de datos

Se implementa el patrón Adaptador para desacoplar al sistema de las especificaciones propietarias de cada aerolínea, hotel o proveedor de correo. Cada servicio externo cuenta con un conector específico que traduce los formatos externos heterogéneos a un **Modelo Canónico de Reserva** interno. Para la integración con la agencia preferida del usuario (US-06), se añade un adaptador de salida que serializa el itinerario en un formato estándar de contingencia.

### Pros:
- **Aislamiento:** Si una aerolínea modifica su API o se agrega un nuevo proveedor, solo se crea o modifica su adaptador correspondiente sin tocar el núcleo del sistema.
- **Estandarización interna:** El motor de reservas y los itinerarios solo conocen el modelo de datos interno de Trotamundos.

### Contras:
- Requiere mantener módulos de traducción específicos y sincronizarlos ante cambios de versiones de APIs de terceros.

### Tácticas aplicadas:
- **Usar un intermediario (*Use an intermediary*):** El adaptador actúa como intermediario para evitar el acoplamiento directo entre sistemas externos y el dominio interno.
- **Encapsular (*Encapsulate*):** Oculta los detalles de comunicación de cada API externa detrás de una interfaz unificada.

### Drivers afectados:
- **US-03 (Integración con terceros):** Estandariza la ingesta de cambios desde aerolíneas y hoteles.
- **US-06 (Agencia preferida):** *Seleccionado.* Facilita enviar el contexto del viaje a la agencia mediante su propio adaptador.
- **QA-I1 y QA-I2 (Interoperabilidad):** Garantiza agregar proveedores en $\le 2\text{ semanas}$ sin modificar el resto de la aplicación.
- **CON-1 (APIs estándar de viajes):** Respeta el uso de interfaces estándares de la industria turística.

---

## Concepto 2: Pipeline de ingesta asíncrona mediante colas de mensajería y trabajadores concurrentes

La recepción de eventos externos (webhooks de aerolíneas o sondeo periódico de casillas) no procesa los datos en el acto. En su lugar, deposita los mensajes en colas de mensajería persistentes dentro del Bus de Eventos. Un grupo de procesos trabajadores (*Workers* de Ingesta) consume los mensajes en paralelo, ejecutando el análisis sintáctico (*parsing*) del correo o actualización, actualizando la base de datos e invalidando la caché correspondiente dentro de la ventana de 5 minutos.

### Pros:
- **Cumplimiento de latencia de propagación:** El procesamiento concurrente asegura procesar las actualizaciones dentro del umbral de 5 minutos (QA-R1).
- **Resiliencia ante picos:** Si una aerolínea envía miles de actualizaciones por mal clima, las colas amortiguan la carga protegiendo al backend.

### Contras:
- Introduce consistencia eventual: los cambios externos tardan algunos segundos o minutos en reflejarse en la base operativa.

### Tácticas aplicadas:
- **Encolar solicitudes (*Queue requests*):** Desacopla la recepción del evento del tiempo que toma su procesamiento y extracción.
- **Introducir concurrencia (*Introduce concurrency*):** Permite procesar múltiples correos y actualizaciones externas en paralelo mediante un grupo de trabajadores (*worker pool*).

### Drivers afectados:
- **US-01 (Procesamiento de correos):** Procesa de forma automatizada y en segundo plano los mensajes detectados.
- **QA-R1 (Propagación de actualizaciones):** Garantiza el tiempo de entrega y renderizado de la actualización externa.
- **QA-E1 (Picos masivos):** *No seleccionado para esta iteración.* Se ve favorecido porque las colas evitan el desbordamiento de la base de datos durante cancelaciones masivas.

---

## Concepto 3: Filtrado previo por Whitelist y gestión de credenciales con mínimo privilegio

Para garantizar la privacidad y la seguridad en el acceso a las casillas de correo, el sistema se conecta solicitando únicamente alcance de solo lectura (*read-only*). Las credenciales y tokens de acceso se almacenan cifrados en reposo. Durante el escaneo, el sistema evalúa en primer término una lista blanca (*whitelist*) configurable por el usuario (US-02); los correos cuyo remitente no coincida con un dominio autorizado se descartan de inmediato sin examinar su asunto ni su cuerpo.

### Pros:
- **Protección estricta de la privacidad:** Ningún correo personal fuera de los remitentes autorizados es analizado ni almacenado.
- **Seguridad ante robo de credenciales:** Si un token es interceptado, su impacto es nulo para acciones de escritura o borrado en la casilla del usuario.

### Contras:
- Dependencia del correcto consentimiento OAuth por parte del usuario y de la correcta configuración de los filtros de remitentes.

### Tácticas aplicadas:
- **Limitar acceso (*Limit access*):** Aplica el principio de mínimo privilegio restringiendo los alcances (*scopes*) de los tokens OAuth a lectura exclusiva.
- **Autorizar actores (*Authorize actors*):** Comprueba mediante la lista blanca si el remitente externo tiene autorización para suministrar datos de viaje.
- **Cifrar datos (*Encrypt data*):** Protege los tokens de acceso almacenados en la base de datos mediante cifrado fuerte en reposo.

### Drivers afectados:
- **US-02 (Filtros y Whitelist):** Otorga al usuario control sobre qué correos procesar.
- **QA-S2 (Compromiso del acceso al correo):** Limita el alcance a solo lectura y resguarda los tokens de acceso ante accesos no autorizados.

---

## Concepto 4: Tolerancia a fallas de proveedores externos mediante reintentos y almacenamiento del último estado conocido

Cuando un proveedor externo (API de aerolínea, hotel o correo) no responde o arroja un error de comunicación, el conector captura la excepción, mantiene intacta la última información confirmada del viaje en el panel y encola un evento de reintento controlado con retroceso exponencial (*exponential backoff*). Al recuperarse el proveedor externo, el sistema reconcilia la información sin haber provocado caídas en el servicio.

### Pros:
- **Continuidad operativa:** La indisponibilidad de un tercero no interrumpe el uso del panel ni bloquea al usuario.
- **Reconciliación transparente:** La actualización pendiente se aplica automáticamente al restablecerse el canal externo.

### Contras:
- El usuario puede ver datos que no reflejan el último cambio en tiempo real durante el lapso en que el proveedor externo esté caído.

### Tácticas aplicadas:
- **Detección de excepciones (*Exception detection*):** Captura fallas de conectividad y respuestas anómalas de las APIs externas.
- **Reintento (*Retry*):** Reprograma los intentos de consulta a la API externa espaciándolos en el tiempo para no sobrecargar el enlace.

### Drivers afectados:
- **QA-D2 (Falla de proveedor externo):** Asegura 0 minutos de inactividad en el panel ante caídas de proveedores turísticos.
- **QA-R1 (Propagación de actualizaciones):** Facilita la reconciliación rápida una vez recuperada la conexión externa.

---

# Paso 5: registrar decisiones de diseño

| Decisión de diseño y ubicación | Justificación |
|---|---|
| **Implementar adaptadores desacoplados con modelo canónico común para proveedores externos.** | Cada aerolínea, hotel o servicio de correo expone formatos y protocolos heterogéneos. Utilizar adaptadores específicos que traduzcan los mensajes a un modelo de reserva común aísla al resto del sistema de las particularidades externas. Esto permite dar de alta nuevos proveedores de viaje o nuevos servicios de correo en menos de dos semanas sin necesidad de modificar el motor de reservas ni los itinerarios existentes, dando cumplimiento directo a los atributos de interoperabilidad. |
| **Utilizar colas de mensajería persistentes y trabajadores concurrentes para la ingesta de eventos externos.** | Recibir las notificaciones en colas del bus de eventos y procesarlas con un grupo de trabajadores concurrentes asegura que el análisis sintáctico y la actualización de los viajes se ejecuten de forma controlada y en paralelo, permitiendo reflejar las actualizaciones en la aplicación en menos de 5 minutos sin comprometer la capacidad del servidor interactivo. |
| **Aplicar validación previa por Whitelist y autenticación con alcance de solo lectura.** | El sistema procesa correspondencia personal del usuario, lo que exige resguardar su privacidad. Descartar inmediatamente cualquier mensaje cuyo remitente no figure en la lista blanca definida por el viajero asegura que el motor de extracción jamás examine correos privados. Además, el almacenamiento cifrado de los tokens de acceso mitiga el riesgo de filtraciones y garantiza un perímetro seguro ante intentos de acceso no autorizado. |
| **Implementar mecanismos de captura de excepciones y reintento con retroceso exponencial para APIs externas.** | Los servicios de terceros suelen sufrir caídas temporales o demoras en sus respuestas. Capturar los errores de comunicación y reintentar la operación de forma espaciada evita que la falla de un proveedor externo bloquee las operaciones del sistema, manteniendo la última información conocida visible en el panel del usuario y reconciliando los datos pendientes de forma automática tan pronto como el proveedor se restablece. |
| **Crear un módulo adaptador de salida hacia agencias de viaje preferidas.** | Permite asistir al usuario ante cancelaciones o contingencias imprevistas transmitiendo de forma directa el contexto estructurado de su reserva al soporte de su agencia elegida. Encapsular esta conexión en un adaptador específico simplifica el enlace con distintas plataformas de agencias turísticas sin alterar la lógica de presentación del panel. |

# Paso 6: Vistas e instanciación de elementos y responsabilidades

## Vista de módulos

[Diagrama de modulos](https://github.com/martinjueguen/Ingenieria-Software/wiki/ADD-%E2%80%90-Iteraci%C3%B3n-3-%E2%80%90-Diagramas#diagrama-de-modulos)  
<img width="99" height="152" alt="image" src="https://github.com/user-attachments/assets/c1c52701-6728-437a-ac7f-49ba19aad0dc" />

### Capa 1: Cliente

**Interfaz web y aplicación móvil**
- Proveer la interfaz para que el usuario vincule su casilla de correo y configure su lista de remitentes seguros (*whitelist*).
- Permitir al viajero seleccionar su agencia de viajes preferida y disparar solicitudes de soporte adjuntando el contexto del itinerario afectado.
- Indicar visualmente la fecha y hora de la última actualización de cada reserva.

### Capa 2: Servidor de aplicaciones

**Adaptadores de proveedores turísticos**
- Consumir las APIs externas de aerolíneas, hoteles y rentadoras de vehículos.
- consultar cambios de estado en las reservas externas.
- Transformar las respuestas de proveedores al modelo canónico de reserva del sistema
- Notificar errores de comunicación y gestionar los reintentos automáticos.

**Servicio de escaneo y filtrado de correo**
- Conectarse periódicamente a los servidores de correo autorizados.
- Evaluar los encabezados de los correos recibidos contra la lista de remitentes seguros (*whitelist*).
- Descartar correos personales no autorizados y remitir únicamente los correos turísticos a la cola de extracción.

**Motor de extracción y parsing**
- Consumir los correos filtrados desde la cola de mensajería.
- Identificar y extraer datos relevantes de las reservas (códigos de reserva, fechas, números de vuelo, nombres de hotel).
- Convertir la información extraída al formato canónico y remitirla al Servicio de Reservas para su persistencia.

**Conector de agencia preferida**
- Recibir solicitudes de asistencia iniciadas por el usuario ante inconvenientes con su viaje.
- Empaquetar el itinerario, las reservas afectadas y sus códigos de confirmación en el formato requerido por la agencia.
- Transmitir la información al canal de soporte oficial de la agencia de viajes del usuario.

**Gestor de tokens y seguridad de ingesta**
- Custodiar los tokens de acceso vinculados a los correos de los usuarios.
- Asegurar que los tokens solicitados tengan alcance estricto de solo lectura (*read-only*).
- Gestionar la revocación inmediata de accesos ante detección de anomalías o solicitud del usuario.

### Capa 3: Datos

**Almacén de tokens y listas blancas**
- Almacenar de forma cifrada en reposo los tokens de autenticación de las cuentas de correo vinculadas.
- Persistir las reglas de filtrado y las listas de remitentes autorizados configuradas por cada usuario.

**Bus de eventos (Colas de ingesta)**
- Proveer colas persistentes dedicadas para mensajes de correo pendientes de análisis y actualizaciones recibidas de aerolíneas/hoteles.
- Garantizar la entrega confiable de mensajes a los trabajadores en segundo plano evitando pérdida de datos ante caídas.

### Sistemas externos

**Servidores de correo electrónico**
- Servidores externos (ej. Gmail, Outlook) que proveen acceso a la bandeja mediante APIs seguras bajo autorización del usuario.

**APIs de aerolíneas, hoteles y arrendadoras**
- Interfaces oficiales de proveedores turísticos que informan cancelaciones, reprogramaciones o emisiones de pasajes.

**Sistemas de agencias de viaje preferidas**
- Plataformas externas de soporte al viajero que reciben el contexto estructurado de los problemas notificados por el sistema.

---

## Diagrama de Secuencia

[Diagrama de secuencia](https://miro.com/app/board/uXjVHyXrEn0=/?moveToWidget=3458764688887086289&cot=14)  
<img width="152" height="99" alt="image" src="https://github.com/user-attachments/assets/14b21ed0-01b3-413f-99d9-49b14e393b40" />  

1. **Sondeo seguro y autorización mínima (Pasos 1 a 4):**  
   El *Servicio de Escaneo* consulta las credenciales del usuario almacenadas de forma cifrada en reposo (*Encrypt data*) y utiliza un token  con alcance restringido a solo lectura (*Limit access*).
2. **Filtrado previo por lista blanca (Pasos 5 a 7):**  
   Antes de leer el cuerpo del mensaje, se comprueba el remitente contra la lista blanca del usuario (*Authorize actors*). Si el correo no proviene de un proveedor habilitado, es descartado inmediatamente, asegurando que el sistema jamás examine correspondencia personal.
3. **Encolamiento y desacoplamiento (Pasos 8 y 9):**  
   Los correos válidos son publicados en la cola del bus de eventos (*Queue requests*), liberando al servicio de escaneo y evitando que el tiempo de extracción bloquee la ingesta.
4. **Extracción concurrente y normalización (Pasos 10 a 12):**  
   Un trabajador disponible del grupo de procesamiento concurrente (*Introduce concurrency*) toma el mensaje de la cola, extrae las fechas, destinos y códigos de confirmación, y los traduce al modelo canónico común (*Use an intermediary*).
5. **Persistencia e invalidación de caché (Pasos 13 a 17):**  
   El *Servicio de Reservas* guarda los datos de forma consistente en la base de datos e inmediatamente invalida la caché en memoria (*Maintain multiple copies of data*). De este modo, la próxima vez que el usuario abra la aplicación, la reserva ya estará visible, garantizando el cumplimiento de la propagación en menos de 5 minutos.

# Paso 7: Revisión de los drivers atacados y del logro del objetivo de la iteración

- **US-01 (Procesamiento de correos):** Completamente satisfecho. El pipeline asíncrono y los workers extraen reservas automáticamente.
- **US-02 (Filtros y Whitelist):** Completamente satisfecho. El servicio de filtrado descarta correos que no provengan de remitentes autorizados antes de procesar su contenido.
- **US-03 (Integración con terceros):** Completamente satisfecho. Los adaptadores específicos normalizan las actualizaciones de aerolíneas y hoteles al modelo canónico.
- **US-06 (Resolución con agencia preferida):** Completamente satisfecho. Se provee un conector de salida para enviar el contexto del itinerario a la agencia de viajes.
- **QA-R1 (Propagación de actualizaciones):** Completamente satisfecho. El uso de colas y trabajadores concurrentes (*Queue requests* / *Introduce concurrency*) permite procesar y reflejar las reservas en la app dentro de la ventana de 5 minutos.
- **QA-I1 y QA-I2 (Interoperabilidad):** Completamente satisfecho. El patrón adaptador (*Use an intermediary*) permite incorporar nuevos proveedores turísticos, medios de transporte o servicios de correo en menos de 2 semanas sin tocar el motor central.
- **QA-S2 (Compromiso del acceso al correo):** Completamente satisfecho. Se utiliza OAuth de solo lectura (*Limit access*), cifrado en reposo (*Encrypt data*) y descarte temprano por whitelist.
- **QA-D2 (Falla de proveedor externo):** Completamente satisfecho. Las excepciones se capturan y se aplican reintentos (*Retry*) manteniendo visible la última información conocida.
- **QA-E1 (Pico por disrupción masiva):** Parcialmente satisfecho. Las colas de mensajería absorben avalanchas de cancelaciones externas sin colapsar el sistema de persistencia.
- **QA-S1 (Acceso a itinerarios compartidos):** Parcialmente satisfecho. Se consolida el módulo de seguridad para el manejo seguro de identidades y permisos.
- **QA-M1 (Nuevo medio de transporte):** Parcialmente satisfecho. El modelo canónico de reserva y los adaptadores facilitan conectar proveedores de micros o trenes.