# Paso 2: Establecemos los objetivos de la iteración seleccionando los drivers

El objetivo de esta iteración es definir la arquitectura de infraestructura, el despliegue multirregión para alta disponibilidad y los mecanismos de escalabilidad ante eventos masivos.

- **US-07:** Analítica de datos y monetización (consultas pesadas sin degradar la operación).
- **QA-D1:** Caída de una región (H,H)
- **QA-E1:** Pico por disrupción masiva (H,H)
- **QA-S1:** Acceso indebido a itinerarios compartidos (H,M)
- **QA-U2:** Nueva región o idioma (M,M)
- **CON-3:** Sistema preparado arquitectónicamente para operar en el mercado internacional (multirregión).

# Paso 3: Elección de elemento/s a refinar

En esta iteración se refina la infraestructura global y la persistencia del sistema:
1. **Estructura física de despliegue** (incorporación de la Vista de Despliegue con múltiples regiones geográficas).
2. **Capa 3: Datos** (segregación entre base de datos transaccional y almacén analítico).
3. **Módulo "Seguridad y control de acceso"** (reglas de autorización para la compartición social de itinerarios).
4. **Clientes y API** (estrategia de internacionalización y localización).

# Paso 4: Elección de uno o más conceptos de diseño para satisfacer los drivers seleccionados

## Concepto 1: Despliegue multirregión con redundancia activa y conmutación por DNS geográfico

Para tolerar la caída total de un centro de datos o región en la nube (QA-D1), el sistema se despliega en dos regiones geográficas independientes (Región Primaria y Región Secundaria). Un servicio de enrutamiento global (*Global Traffic Manager / GeoDNS*) monitorea la salud del sistema mediante chequeos continuos (*heartbeats*). Si la región activa deja de responder, el tráfico se redirige automáticamente a la región secundaria en menos de 1 minuto, cumpliendo el límite estricto de 5 minutos de inactividad mensual.

### Pros:
- **Tolerancia a desastres:** Garantiza la continuidad total del servicio ante fallas catastróficas regionales de infraestructura.
- **Acceso global eficiente:** Permite dirigir a los usuarios a la región más cercana para reducir la latencia de red (CON-3).

### Contras:
- Incrementa significativamente los costos de infraestructura al duplicar componentes.
- Requiere sincronización continua entre las bases de datos de ambas regiones.

### Tácticas aplicadas:
- **Redundancia activa (*Active redundancy*):** Mantiene instancias operativas en múltiples ubicaciones físicas listas para procesar tráfico.
- **Monitoreo y chequeo de salud (*Heartbeat* / *Ping/Echo*):** Monitorea periódicamente la disponibilidad de cada región para detectar fallos de inmediato.
- **Retiro de servicio / Reconfiguración (*Removal from service*):** Aísla la región dañada redirigiendo las peticiones a la región sana.

### Drivers afectados:
- **QA-D1 (Caída de una región):** Garantiza menos de 5 min/mes de indisponibilidad.
- **CON-3 (Operación multirregión):** Da cumplimiento formal al soporte de infraestructura global.

---

## Concepto 2: Escalado horizontal y balanceo de carga

Para absorber los picos abruptos del domingo-lunes y las disrupciones por tormentas climáticas (+300% de peticiones concurrentes, QA-E1), los componentes del Servidor de Aplicaciones y los *Workers* de ingesta se configuran como servicios sin estado (*stateless*). Se implementan políticas de autoescalado horizontal basadas en umbrales de uso de CPU, memoria y longitud de colas en el bus de eventos, distribuyendo la carga mediante balanceadores (*Load Balancers*).

### Pros:
- **Flexibilidad financiera y técnica:** El sistema escala dinámicamente durante los picos y reduce recursos en horarios de baja demanda.
- **Estabilidad bajo estrés:** Mantiene la tasa de fallos por debajo del 0.1% y la latencia web en menos de 1.5 s durante la crisis.

### Contras:
- Pequeño retardo (1 a 2 minutos) mientras las nuevas instancias virtuales se inicializan y entran al grupo de balanceo.

### Tácticas aplicadas:
- **Aumentar los recursos (*Increase resources*):** Escala automáticamente el número de servidores y contenedores ante incrementos de demanda.
- **Introducir concurrencia (*Introduce concurrency*):** Multiplica los hilos y procesos en ejecución distribuidos a través de balanceadores.

### Drivers afectados:
- **QA-E1 (Pico por disrupción masiva):** Sostiene los picos de 2 millones de usuarios activos sin degradar el servicio.

---

## Concepto 3: Separación del almacén analítico usando replicación asíncrona

Para resolver la monetización y análisis de datos (US-07) sin degradar las operaciones en tiempo real de los viajeros, se separa la base de datos transaccional de un **Almacén de Datos Analítico**. Los eventos de cambios de itinerarios y reservas se replican de forma asíncrona hacia el almacén analítico. El equipo de datos ejecuta sus consultas pesadas de tendencias y cancelaciones exclusivamente contra este almacén.

### Pros:
- **Aislamiento de rendimiento:** Las consultas analíticas de larga duración no bloquean las tablas de los usuarios activos.
- **Modelado especializado:** Permite optimizar los datos analíticos para agregaciones y reportes históricos.

### Contras:
- Consistencia eventual en los datos de reportería (los viajes tardan minutos en estar disponibles para analítica).

### Tácticas aplicadas:
- **Mantener múltiples copias de datos (*Maintain multiple copies of data*):** Separa las copias para lectura analítica de la base de datos operativa principal.
- **Gestionar el tamaño de las tareas (*Manage work sizes / Resource allocation*):** Evita la contención de recursos de CPU y disco entre transacciones web y reportería pesada.

### Drivers afectados:
- **US-07 (Analítica de datos y monetización):** Permite consultas masivas sin perjudicar a los usuarios.
- **QA-R2 (Latencia Web):** Evita que la analítica degrade los 800 ms de respuesta.

---

## Concepto 4: Control de acceso basado en listas de compartición autorizadas

Para satisfacer el requerimiento de privacidad al compartir itinerarios (QA-S1), se refina el módulo de seguridad incorporando una **Lista de Control de Acceso por Itinerario**. El propietario del viaje puede invitar explícitamente a personas designadas por correo o identificador de usuario con permisos específicos (solo lectura del viaje). El sistema valida la identidad del actor y sus permisos antes de renderizar los detalles compartidos, bloqueando y auditando cualquier intento no autorizado.

### Pros:
- **Seguridad granular:** Cada viaje tiene su propio control de acceso sin depender de enlaces públicos expuestos.
- **Trazabilidad:** Se auditan todos los intentos denegados y visualizaciones registradas.

### Contras:
- Obliga a los invitados a poseer una cuenta autenticada para validar su designación.

### Tácticas aplicadas:
- **Autorizar actores (*Authorize actors*):** Valida que el usuario solicitante figure en la lista de personas designadas del viaje.
- **Limitar acceso (*Limit access*):** Restringe la visibilidad exclusivamente a los itinerarios para los cuales se otorgó acceso explícito.

### Drivers afectados:
- **QA-S1 (Acceso indebido a itinerarios compartidos):** Garantiza 100% de accesos no autorizados bloqueados.

---

## Concepto 5: Externalización de recursos de localización y husos horarios

Para cumplir con la operación internacional en múltiples idiomas, monedas y formatos horarios (QA-U2), se separan las cadenas de texto, conversiones monetarias y cálculos horarios de la lógica del núcleo del sistema. Se utilizan paquetes de recursos estáticos (*Resource Bundles*) en el cliente y la API normaliza todas las fechas en tiempo universal UTC, delegando la presentación en huso horario local a la interfaz de usuario.

### Pros:
- **Fácil incorporación de mercados:** Agregar un nuevo idioma o moneda no requiere alterar ni recompilar el código fuente del backend.
- **Consistencia temporal:** Almacenar en UTC evita discrepancias horarias en vuelos que cruzan zonas horarias.

### Tácticas aplicadas:
- **Parametrizar el sistema (*Parameterize / Resource Bundles*):** Separa las variables idiomáticas y de formato de la lógica de negocio.
- **Encapsular (*Encapsulate*):** Aísla las funciones de conversión de divisas en utilitarios independientes.

### Drivers afectados:
- **QA-U2 (Nueva región o idioma):** Incorporación de idiomas sin tocar el núcleo.

# Paso 5: Registrar decisiones de diseño

| Decisión de diseño y ubicación | Justificación |
|---|---|
| **Implementar un despliegue multirregión en esquema Activo-Pasivo Caliente con balanceador DNS geográfico.** | Una interrupción masiva del centro de datos principal dejaría a millones de viajeros sin acceso a sus itinerarios en momentos críticos de viaje. Desplegar una réplica completa en una segunda región geográfica y conmutar el tráfico de forma automática mediante GeoDNS ante la detección de anomalías asegura que la indisponibilidad no planificada acumulada no supere los 5 minutos mensuales, satisfaciendo el requerimiento de alta disponibilidad global. |
| **Configurar autoescalado horizontal basado en métricas para la capa de API y los trabajadores de eventos.** | El tráfico del sistema sufre picos estacionales previsibles (jueves a lunes) y ráfagas impredecibles del 300% por disrupciones climáticas. Hacer que las instancias de la API y los workers de ingesta sean elásticos permite multiplicar dinámicamente los recursos de procesamiento en minutos, garantizando que el sistema absorba la concurrencia masiva sin exceder los 1.5 segundos de latencia ni degradar el servicio. |
| **Crear un Almacén Analítico (Data Warehouse) segregado de la base transaccional con sincronización asíncrona.** | Las consultas de tendencias comerciales y cancelaciones que requiere el equipo de monetización demandan escaneos masivos sobre millones de registros históricos. Ejecutar estas cargas de trabajo en un almacén analítico dedicado evita la saturación de conexiones y contención de CPU en la base transaccional, garantizando que la monetización de datos no degrade las operaciones interactivas de los 2 millones de usuarios activos. |
| **Implementar listas de control de acceso explícitas para la compartición de itinerarios en el módulo de seguridad.** | Los datos de viaje constituyen información personal altamente sensible. Restringir la visualización de los viajes compartidos a personas designadas mediante una verificación de identidad y autorización a nivel de registro impide que atacantes o terceros no autorizados puedan acceder a ubicaciones o fechas de traslado, garantizando un bloqueo total de visualizaciones indebidas. |
| **Adoptar almacenamiento temporal estándar en UTC y paquetes de localización externos.** | La internacionalización del sistema exige atender a usuarios en diferentes idiomas, monedas y husos horarios. Mantener los registros temporales internamente en UTC y externalizar las traducciones y formatos en archivos de configuración permite adaptar la plataforma a nuevos mercados internacionales en menos de una semana sin modificar el código fuente del núcleo. |

---

# Paso 6: Vistas e instanciación de elementos y responsabilidades

## Asignación de responsabilidades

### Diagrama de despliegue
[Diagrama de despliegue](https://github.com/martinjueguen/Ingenieria-Software/wiki/ADD-%E2%80%90-Iteraci%C3%B3n-4-%E2%80%90-Diagramas#diagrama-de-componentes)  
<img width="99" height="152" alt="image" src="https://github.com/user-attachments/assets/6959a18d-c613-43c4-8c56-0fceddabc779" />  

### Capa 1: Cliente
- **Interfaz web y móvil internacionalizada:** Detectar la configuración regional del viajero, renderizar textos en su idioma nativo, mostrar conversiones de moneda y calcular horas en el huso horario local.
- **Módulo de compartición segura:** Proveer la interfaz para que el propietario del viaje ingrese los correos de las personas designadas con permiso para ver su itinerario.

### Capa 2: Servidor de aplicaciones
- **Controlador de autorización de itinerarios:** Verificar si el usuario que solicita un viaje es el propietario o un invitado autorizado en la lista de compartición antes de entregar los datos.
- **Exportador analítico asíncrono:** Proceso desacoplado que extrae periódicamente eventos de viajes y cambios de reservas para consolidarlos en el almacén analítico.
- **Servicios elásticos (API y Workers):** Componentes sin estado preparados para escalar horizontalmente de forma automática según la demanda de tráfico.

### Capa 3: Datos
- **Base de datos operacional (OLTP):** Base de datos relacional replicada entre regiones que gestiona las transacciones de los usuarios en tiempo real.
- **Almacén de datos analítico (OLAP):** Base de datos columnar optimizada para consultas pesadas de agregación, reportes históricos y analítica de monetización.
- **Registro de auditoría de accesos:** Almacén seguro donde se asientan todos los accesos e intentos denegados a itinerarios compartidos.

---


### Responsabilidades de los nodos de infraestructura:
- **Global Traffic Manager (GeoDNS):** Punto de entrada global. Realiza chequeos de salud periódicos a las regiones y conmuta las peticiones a la región secundaria si la primaria falla.
- **Balanceador de carga regional (ALB):** Distribuye el tráfico entrante de forma uniforme entre los múltiples nodos de la API disponibles.
- **Grupo de autoescalado de APIs:** Conjunto elástico de servidores web/API que añade o quita instancias según la carga de CPU y tráfico.
- **Grupo de autoescalado de Workers:** Conjunto elástico de consumidores que procesa colas de mensajes escalando según la cantidad de tareas pendientes.
- **Clúster de Base de Datos Transaccional:** Motor primario en la región activa que replica continuamente los cambios hacia la réplica en la región secundaria.
- **Almacén Analítico (Data Warehouse):** Infraestructura de datos aislada para soportar consultas de negocio y algoritmos de monetización.

---

## Conectores y comunicación entre componentes

| Conector | Responsabilidad |
|---|---|
| **Enrutamiento GeoDNS / Heartbeat** | Dirigir el tráfico del cliente a la región saludable más cercana y detectar caídas regionales mediante pings continuos. |
| **Balanceo HTTP/HTTPS** | Conectar los clientes con las instancias operativas de la API distribuyendo la carga de conexiones concurrentes. |
| **Replicación entre regiones** | Sincronizar de forma continua las transacciones de la base de datos primaria hacia la región secundaria para garantizar failover con 0 pérdidas de reservas confirmadas. |
| **Pipeline ETL / Eventos analíticos** | Transportar datos de reservas consolidados desde el entorno transaccional hacia el almacén analítico de forma asíncrona. |
| **Consultas SQL Analíticas** | Canal dedicado para que los analistas ejecuten reportes pesados sobre el Data Warehouse sin interferir con la base operativa. |

---

# Paso 7: Revisión final de todos los drivers del sistema

| Categoría | Identificador y Nombre | Iteración donde se resolvió | Estado Final |
|---|---|:---:|:---:|
| **Requerimientos Funcionales** | **US-01:** Procesamiento de Correo | Iteración 3 | **Completamente Satisfecho** |
| | **US-02:** Filtros y Whitelist de Correo | Iteración 3 | **Completamente Satisfecho** |
| | **US-03:** Integración con APIs de Terceros | Iteración 3 | **Completamente Satisfecho** |
| | **US-04:** Gestión Manual de Reservas | Iteración 2 | **Completamente Satisfecho** |
| | **US-05:** Ciclo de Vida del Viaje (Archivado) | Iteración 2 | **Completamente Satisfecho** |
| | **US-06:** Soporte con Agencia Preferida | Iteración 3 | **Completamente Satisfecho** |
| | **US-07:** Analítica de Datos y Monetización | **Iteración 4** | **Completamente Satisfecho** |
| **Atributos de Calidad** | **QA-R1:** Propagación de actualizaciones | Iteración 3 | **Completamente Satisfecho** |
| | **QA-R2:** Latencia Web | Iteración 2 | **Completamente Satisfecho** |
| | **QA-R3:** Primer despliegue móvil | Iteración 2 | **Completamente Satisfecho** |
| | **QA-D1:** Caída de una región | **Iteración 4** | **Completamente Satisfecho** |
| | **QA-D2:** Falla de un proveedor externo | Iteración 3 | **Completamente Satisfecho** |
| | **QA-E1:** Pico por disrupción masiva (+300% carga) | **Iteración 4** | **Completamente Satisfecho** |
| | **QA-I1:** Nuevo proveedor de viajes | Iteración 3 | **Completamente Satisfecho** |
| | **QA-I2:** Nuevo correo o red social | Iteración 3 | **Completamente Satisfecho** |
| | **QA-S1:** Acceso a itinerarios compartidos | **Iteración 4** | **Completamente Satisfecho** |
| | **QA-S2:** Compromiso de acceso a correo (OAuth) | Iteración 3 | **Completamente Satisfecho** |
| | **QA-M1:** Nuevo medio de transporte (trenes/micros) | Iteración 2 y 3 | **Completamente Satisfecho** |
| | **QA-U1:** Interfaz móvil con GPS | Iteración 2 | **Completamente Satisfecho** |
| | **QA-U2:** Nueva región o idioma | **Iteración 4** | **Completamente Satisfecho** |
| **Restricciones y Concerns** | **CON-1:** Uso de APIs estándar de turismo | Iteración 3 | **Completamente Satisfecho** |
| | **CON-2:** Acceso Web y Móvil con GPS | Iteración 1 y 2 | **Completamente Satisfecho** |
| | **CON-3:** Operación multirregión internacional | **Iteración 4** | **Completamente Satisfecho** |
| | **CRN-1:** Estructura general del sistema | Iteración 1 | **Completamente Satisfecho** |