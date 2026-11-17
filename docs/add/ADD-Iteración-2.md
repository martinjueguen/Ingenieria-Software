# Paso 2: Establecemos los objetivos de la iteración seleccionando los drivers

El objetivo de esta iteración es diseñar internamente el subsistema central de **Gestión de Viajes y Reservas** y optimizar la recuperación y presentación de datos para cumplir con los requerimientos interactivos de los usuarios.

**Drivers seleccionados:**
- **US-04:** Gestión manual de reservas
- **US-05:** Ciclo de vida del viaje (agrupación y archivado automático)
- **QA-R2:** Latencia web (H,M)
- **QA-R3:** Primer despliegue móvil (M, M)

# Paso 3: Elección de elemento/s a refinar

Refinaremos los elementos definidos en la Capa 2 y Capa 3 de la Iteración 1 involucrados en la interacción del usuario:
1. **Módulo "Gestión de viajes y reservas"** (Capa 2).
2. **Módulo "API / Acceso al sistema"** (Capa 2).
3. **Módulo "Comunicación con almacenamiento" y "Base de datos"** (Capa 3). 

# Paso 4: Elección de uno o más conceptos de diseño para satisfacer los drivers seleccionados

## Concepto 1: Descomposición modular interna de la gestión de viajes y reservas

Se divide el módulo general de "Gestión de viajes y reservas" en tres submódulos con responsabilidades bien delimitadas:
1. **Servicio de Reservas:** gestiona el alta, baja, modificación y consulta de reservas individuales (vuelos, hoteles, autos, etc.).
2. **Servicio de Itinerarios:** implementa las reglas para agrupar reservas dentro de un viaje en función de fechas, destinos y secuencias temporales.
3. **Gestor de Ciclo de Vida:** se encarga de gestionar los estados del viaje (planificado, en curso, finalizado, archivado).

### Pros:
- **Alta cohesión:** cada submódulo tiene una única responsabilidad clara dentro del dominio de viajes.
- **Bajo acoplamiento:** permite modificar las reglas de creación de reservas o agregar nuevos transportes sin alterar la forma en que los viajes se agrupan.
- **Mantenibilidad:** facilita realizar pruebas unitarias y de integración sobre cada parte de la lógica de negocio por separado.

### Contras:
- Requiere coordinar la comunicación interna entre el servicio de reservas y el de itinerarios cuando una acción afecta a ambos (por ejemplo, al eliminar una reserva que deja a un viaje sin tramos).

### Tácticas aplicadas:
- **Aumentar la coherencia semántica (*Increase semantic coherence*):** agrupa funciones que están estrechamente vinculadas por su propósito funcional dentro del dominio.
- **Encapsular (*Encapsulate*):** oculta la estructura interna de cómo se almacena o agrupa un itinerario detrás de interfaces bien definidas.

### Drivers afectados:
- **US-04 (Gestión manual de reservas):** Resuelve la creación, edición y eliminación de reservas individuales.
- **US-05 (Ciclo de vida del viaje):** Otorga un componente exclusivo para agrupar y manejar los estados del viaje.
- **QA-M1 (Nuevo medio de transporte):** Se ve favorecido, ya que al encapsular los tipos de reserva será más fácil agregar nuevos medios en el futuro.

---

## Concepto 2: Caché de lectura en memoria para itinerarios activos

Se introduce un componente de almacenamiento temporal en memoria (*in-memory cache*) intermedio entre la capa de aplicación y la base de datos. Dado que la lectura de un itinerario es mucho más frecuente que su modificación (los usuarios consultan repetidamente sus viajes durante el trayecto), las consultas se resuelven contra la memoria rápida. Cuando el usuario realiza una modificación manual o se recibe una actualización externa, la entrada correspondiente de la caché se invalida o actualiza.

### Pros:
- **Tiempos de respuesta mínimos:** permite devolver los datos en decenas de milisegundos, ya que evita accesos a disco y la ejecución repetitiva de consultas SQL complejas con múltiples uniones (*JOINs*).
- **Alivio a la base de datos:** disminuye drásticamente el tráfico de lectura concurrente sobre la base de datos transaccional.

### Contras:
- **Complejidad de consistencia:** exige implementar políticas de invalidación rigurosas (*cache invalidation*) para no mostrar datos viejos tras una modificación manual.
- **Costo de recursos:** requiere memoria RAM adicional en el servidor o en un servicio dedicado.

### Tácticas aplicadas:
- **Mantener múltiples copias de datos (*Maintain multiple copies of data / Caching*):** almacena copias de itinerarios de consulta frecuente en memoria volátil de acceso rápido.
- **Reducir la sobrecarga computacional (*Reduce computational overhead*):** evita procesar repetidamente las relaciones entre viajes y reservas para solicitudes de solo lectura.

### Drivers afectados:
- **QA-R2 (Latencia web):** Es la táctica principal para asegurar que el panel web cargue en menos de 800 ms.
- **QA-E1 (Pico por disrupción masiva):** Se ve favorecido porque la caché amortigua la avalancha de lecturas simultáneas ante cancelaciones o contingencias climáticas.

---

## Concepto 3: Optimización del contrato de datos móvil (Endpoint de resumen ligero)

Se diseña un recurso específico y ligero en la API para clientes móviles (*Trip Summary*). En lugar de transferir el historial completo o todos los detalles de cada reserva en la pantalla de bienvenida, este endpoint provee únicamente la información crítica del próximo tramo (ej. número de vuelo, horario, código de reserva y estado). Los detalles completos y los viajes pasados se descargan bajo demanda mediante carga diferida (*lazy loading* o paginación).

### Pros:
- **Transferencia eficiente:** minimiza el tamaño del paquete JSON enviado por la red celular (4G/móvil).
- **Renderizado rápido:** la aplicación móvil procesa y renderiza el contenido útil de forma inmediata, logrando pintar la pantalla sin demoras.

### Contras:
- Obliga al backend a mantener un contrato de datos específico o endpoints con proyecciones reducidas, sumando leve mantenimiento en la API.
- Si el usuario navega a ver el detalle de inmediato, se requiere una segunda solicitud de red.

### Tácticas aplicadas:
- **Limitar el tamaño de las respuestas / transferencias eficientes (*Bound execution times / Bound response sizes*):** acota la cantidad de bytes transferidos para garantizar que la respuesta arribe y se procese dentro del umbral temporal exigido.
- **Reducir la sobrecarga computacional (*Reduce computational overhead*):** elimina el cálculo y serialización de campos no visualizados en la pantalla inicial de la app móvil.

### Drivers afectados:
- **QA-R3 (Primer despliegue en móvil):** Es la clave para lograr el *First-contentful paint* en menos de 1.4 segundos en conexiones móviles.
- **QA-U1 (Interfaz móvil con GPS):** Se ve favorecido al tener rápidamente disponible en memoria del celular el próximo destino a geolocalizar.

---

## Concepto 4: Proceso programado en segundo plano para archivado automático

En lugar de evaluar si un viaje debe archivarse al momento exacto en que un usuario abre la aplicación (lo que agregaría escrituras y sobrecarga a una petición de lectura), la regla de archivado se delega a un proceso periódico en segundo plano (*scheduled background job*). Este proceso revisa en momentos de baja carga los viajes cuya fecha de finalización ya expiró y actualiza su estado a "Archivado".

### Pros:
- **No penaliza las consultas interactivas:** la consulta del usuario sigue siendo una lectura limpia y rápida, sin verse afectada por chequeos lógicos pesados.
- **Procesamiento ordenado por lotes:** permite archivar grandes volúmenes de viajes de forma controlada y en una única operación periódica.

### Contras:
- **Consistencia temporal leve:** puede existir una ventana de pocas horas entre que un viaje finaliza y el proceso lo archiva efectivamente de la vista principal.

### Tácticas aplicadas:
- **Programar recursos (*Schedule resources*):** asigna la ejecución de tareas de mantenimiento en momentos e intervalos controlados.
- **Diferir vinculación / procesamiento (*Defer binding / Asynchronous execution*):** pospone la actualización del estado del ciclo de vida separándola de las operaciones interactivas del usuario.

### Drivers afectados:
- **US-05 (Ciclo de vida del viaje):** Resuelve el archivado automático de viajes finalizados.
- **QA-R2 (Latencia web):** Protege el tiempo de respuesta al no mezclar tareas de mantenimiento con las lecturas interactivas del usuario.

# Paso 5: Registrar decisiones de diseño

| Decisión de diseño y ubicación | Justificación |
|---|---|
| **Descomponer el módulo de gestión de viajes y reservas en submódulos especializados de Reservas, Itinerarios y Ciclo de Vida.** | Permite separar la lógica encargada de validar y persistir reservas individuales de las reglas necesarias para agruparlas cronológica y geográficamente dentro de un viaje. Esta división evita el acoplamiento entre los distintos tipos de reservas y la estructura general del itinerario, lo que facilita incorporar nuevos medios de transporte en el futuro sin alterar la gestión del viaje y simplifica el mantenimiento y las pruebas de cada funcionalidad de forma aislada. |
| **Incorporar un componente de caché en memoria para los itinerarios activos.** | Los usuarios consultan sus itinerarios reiteradas veces durante sus viajes, mientras que las modificaciones ocurren con menor frecuencia. Servir estas consultas de lectura directamente desde la memoria evita el acceso al disco y la ejecución continua de consultas complejas con múltiples uniones (*JOINs*) en la base de datos relacional. Esto resulta fundamental para asegurar que el panel web devuelva la información por debajo de los 800 ms requeridos y protege a la base de datos transaccional de una sobrecarga innecesaria. |
| **Implementar una política de invalidación de caché ante modificaciones de reservas.** | Permite mantener la consistencia entre los datos cacheados y la base de datos persistente. Al invalidar o actualizar la entrada del viaje en la memoria caché inmediatamente después de que el usuario crea, edita o elimina una reserva manualmente, se garantiza que las siguientes solicitudes de consulta reflejen los cambios de forma fidedigna, impidiendo que el viajero visualice datos desactualizados en su panel. |
| **Definir un recurso o endpoint de resumen ligero (*Trip Summary*) en la API para clientes móviles.** | Las conexiones móviles presentan mayor latencia y variabilidad de ancho de banda que las redes cableadas. Limitar el paquete de datos inicial a la información estrictamente necesaria para la pantalla principal (como el próximo tramo y su estado) reduce notablemente el tamaño de la respuesta JSON y el tiempo de procesamiento en el celular. Esto permite alcanzar el objetivo de desplegar el primer contenido útil en menos de 1.4 segundos, dejando los detalles exhaustivos del viaje para solicitudes posteriores bajo demanda. |
| **Delegar el archivado automático de viajes a un proceso periódico en segundo plano.** | Evaluar si un viaje ha concluido y modificar su estado durante las peticiones interactivas del usuario agregaría procesamiento y bloqueos de escritura innecesarios en el camino crítico de lectura. Resolver esta tarea mediante un proceso programado que revisa los viajes expirados de forma periódica mantiene organizada la vista principal de los usuarios y asegura el cumplimiento del ciclo de vida sin perjudicar los tiempos de respuesta interactivos del sistema. |

# Paso 6: Vistas e instanciación de elementos y responsabilidades

## Asignación de responsabilidades

### Diagrama de modulos

[Diagrama de modulos](https://github.com/martinjueguen/Ingenieria-Software/wiki/ADD-%E2%80%90-Iteraci%C3%B3n-2-%E2%80%90-Digramas#diagrama-de-componentes-y-conectores)  
<img width="99" height="152" alt="image" src="https://github.com/user-attachments/assets/dcaa617f-cf44-4f1e-bcc4-90fd94164697" />  

### Capa 2: Servidor de aplicaciones

**API / Acceso al sistema**
- Exponer los endpoints REST de consulta y gestión de viajes.
- Ofrecer un endpoint de resumen optimizado para clientes móviles.
- Validar las solicitudes entrantes y derivarlas a los servicios correspondientes.

**Servicio de reservas**
- Implementar la lógica para crear, modificar y eliminar reservas manualmente (US-04).
- Validar los datos de las reservas antes de su almacenamiento.
- Notificar cambios al gestor de caché y al servicio de itinerarios.

**Servicio de itinerarios**
- Agrupar reservas en viajes según fechas y destinos (US-05).
- Construir el consolidado del itinerario para las vistas del usuario.

**Gestor de ciclo de vida**
- Revisar periódicamente las fechas de fin de viaje y archivarlos automáticamente (US-05).
- Ejecutar el archivado en segundo plano sin bloquear las consultas de los usuarios.

### Capa 3: Datos

**Gestor de caché**
- Resolver consultas de itinerarios desde la memoria rápida (*Cache Hit/Miss*).
- Invalidar o actualizar copias en memoria tras una modificación de reservas.

**Acceso a almacenamiento***
- Encapsular las consultas y transacciones con la base de datos relacional.
- Aislar a los servicios de negocio de los detalles de persistencia.

---

### Diagrama de componentes y conectores

[Diagrama de componentes y conectores](https://github.com/martinjueguen/Ingenieria-Software/wiki/ADD-%E2%80%90-Iteraci%C3%B3n-2-%E2%80%90-Digramas#diagrama-de-componentes-y-conectores)  
<img width="99" height="152" alt="image" src="https://github.com/user-attachments/assets/b51d88d5-bbbb-4e1d-9b57-66be2f0798c0" />  

**Web / Aplicación móvil**
- Consultar y gestionar sus viajes desde la web o la app móvil.
- Enviar peticiones REST y renderizar los datos recibidos.

**API Controller**
- Recibir solicitudes y derivarlas al gestor de caché o a los servicios de dominio.

**Gestor de caché**
- Interceptar lecturas para servirlas desde memoria cuando estén disponibles.

**Repositorio / ORM **
- Ejecutar operaciones de lectura y escritura en la base de datos relacional.

**Caché en memoria**
- Servir datos de lectura rápida con baja latencia.

**Base de datos**
- Almacenar los registros operativos de forma durable.

---

## Conectores y comunicación entre componentes

| Conector | Responsabilidad |
|---|---|
| **Solicitudes REST (HTTPS)** | Comunicar clientes con la API mediante intercambio síncrono de JSON. |
| **Acceso a caché** | Permitir lectura y escritura de bajísima latencia en memoria. |
| **Llamadas internas** | Comunicar el API Controller con los servicios dentro del servidor de aplicaciones. |
| **Lectura y escritura** | Conectar los servicios y el worker de archivado con la capa de persistencia. |
| **Acceso a base de datos** | Ejecutar consultas SQL transaccionales sobre la base de datos relacional. |
| **Invalidación de caché** | Purgar registros en memoria tras una modificación manual confirmada. |

# Paso 7: Revisión de los drivers atacados y del logro del objetivo de la iteración

### Estado de los Drivers:
- **US-04 (Gestión manual de reservas):** Completamente satisfecho. El Servicio de Reservas permite crear, modificar y dar de baja reservas de forma aislada.
- **US-05 (Ciclo de vida del viaje):** Completamente satisfecho. El Gestor de Ciclo de Vida archiva los viajes completados sin impacto en la vista principal ni bloqueo en la interacción.
- **QA-R2 (Latencia Web):** Completamente satisfecho. El uso de caché en memoria (*Maintain multiple copies of data*) y desacoplamiento de lecturas garantiza tiempos de respuesta del backend del orden de decenas de milisegundos bajo condiciones normales.
- **QA-R3 (Primer despliegue móvil):** Completamente satisfecho. El endpoint de resumen minimiza el tamaño transferido por la red celular (*Reduce computational overhead*), permitiendo que la interfaz móvil pinte de inmediato el contenido útil.
- **QA-E1 (Pico por disrupción masiva):** Parcialmente satisfecho. La capa de caché amortigua la avalancha de lecturas simultáneas de itinerarios durante contingencias, evitando el colapso de la base de datos transaccional (resta definir el autoescalado y despliegue para completarlo).
- **QA-M1 (Nuevo medio de transporte):** Parcialmente satisfecho. Al descomponer la lógica y encapsular el Servicio de Reservas (*Increase semantic coherence* / *Encapsulate*), se facilita extender el modelo a trenes o colectivos sin alterar la lógica de agrupación de itinerarios.
- **CON-2 (Soporte Web y Móvil):** Parcialmente satisfecho. Se adaptaron los contratos y la entrega de datos de la API para ajustarse a las limitaciones de ancho de banda y renderizado de los dispositivos móviles.
- **QA-U1 (Interfaz móvil con GPS):** Parcialmente satisfecho. Disponer del próximo tramo del itinerario en el resumen inicial del móvil facilita la integración directa con la ubicación GPS del dispositivo.
