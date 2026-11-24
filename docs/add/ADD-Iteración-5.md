# Paso 1: Revisión de los inputs

Esta iteración corresponde a la **2da entrega**. Se incorpora el requerimiento avanzado elegido por el grupo, la **Opción A: Sistema de Recomendación** con optimización *human-in-the-loop*. La Opción B (chatbot) queda fuera del alcance.

Los drivers de las iteraciones 1 a 4 se mantienen sin cambios. Se agregan:
- La historia de usuario **US-08** en [[Requerimientos Funcionales]].
- Los escenarios **QA-R4, QA-D3, QA-M2 y QA-S3** en [[Atributos de Calidad]] (sección 8), que refinan para el nuevo módulo los atributos ya priorizados de rendimiento, disponibilidad, modificabilidad y seguridad.

# Paso 2: Establecemos los objetivos de la iteración seleccionando los drivers

El objetivo de esta iteración es diseñar el **Sistema de Recomendación** e integrarlo a la arquitectura existente sin degradar los atributos de calidad ya satisfechos: el panel debe seguir respondiendo en 800 ms, tolerar fallas y picos, y el módulo debe poder evolucionar (otro algoritmo, otros catálogos) sin tocar el resto del sistema.

**Drivers seleccionados:**
- **US-08:** Recomendaciones proactivas con optimización *human-in-the-loop*.
- **QA-R4:** Sugerencias sin penalizar la latencia (H,M)
- **QA-D3:** Falla del recomendador o de un catálogo (H,M)
- **QA-M2:** Nuevo algoritmo de recomendación o nuevo catálogo (M,M)
- **QA-S3:** Privacidad del aprendizaje de preferencias (H,M)
- **QA-E1:** Pico por disrupción masiva (H,H), revisado: las disrupciones son justamente el momento en que más sugerencias se generan.

# Paso 3: Elección de elemento/s a refinar

1. **Capa 2: Servidor de aplicaciones:** se agrega un nuevo módulo **"Sistema de Recomendación"**.
2. **Módulo "Integración con servicios externos":** se agrega un puerto para consultar y reservar en los **catálogos de ofertas** de los proveedores.
3. **Módulo "Procesamiento asíncrono":** nuevos eventos y consumidores para el precálculo y el aprendizaje.
4. **Capa 3: Datos:** persistencia de sugerencias y preferencias en la base operacional, y hechos de feedback en el almacén analítico.

# Paso 4: Elección de uno o más conceptos de diseño para satisfacer los drivers seleccionados

## Concepto 1: Precálculo asíncrono de sugerencias dirigido por eventos

En lugar de calcular las sugerencias cuando el usuario las pide, el Servicio de Recomendaciones se suscribe al evento `reserva.cambiada` (ya existente desde la Iteración 3) y a un nuevo evento `recomendacion.solicitada`. Cada vez que cambia un viaje, un *worker* detecta qué le falta al viaje (una noche sin hotel, un tramo entre dos ciudades sin cubrir, una reserva cancelada sin reemplazo), consulta los catálogos, puntúa las ofertas y **guarda las sugerencias ya ordenadas**. La API solo lee lo precalculado. Un proceso programado pide además un recálculo periódico para todos los viajes activos (sugerencias proactivas).

**Alternativas evaluadas:**
- *Cálculo en línea en cada solicitud:* siempre actualizado, pero consultar varios catálogos externos y puntuar en el camino de la solicitud rompe los 800 ms (QA-R2) y hace que la caída de un catálogo afecte la respuesta.
- *Proceso batch nocturno:* barato, pero no reacciona a tiempo a una cancelación durante el viaje (justo cuando más se necesita la sugerencia).

### Pros:
- La consulta de sugerencias cuesta lo mismo que cualquier lectura del panel.
- Reutiliza el bus de eventos y los *workers* elásticos de las iteraciones 3 y 4.
- Reacciona a disrupciones: una cancelación genera alternativas y una notificación al viajero.

### Contras:
- Consistencia eventual: tras un cambio, las sugerencias tardan unos segundos (siempre menos de 5 minutos) en actualizarse.
- Se almacenan sugerencias que el usuario quizás nunca mire.

### Tácticas aplicadas:
- **Introducir concurrencia / procesamiento asíncrono:** el cálculo corre en *workers*, fuera del camino de la solicitud.
- **Mantener múltiples copias de los cómputos (*Maintain multiple copies of computations*):** se guarda el resultado precalculado.
- **Planificación (*Scheduling policy*):** recálculo periódico para sugerencias proactivas.

### Drivers afectados:
- **QA-R4:** 0 cálculos en el camino de la solicitud y sugerencias actualizadas en menos de 5 minutos.
- **US-08:** sugerencias proactivas y ante disrupciones.

---

## Concepto 2: Estrategia de puntuación intercambiable (patrón Strategy) con modelo híbrido

El servicio no conoce el algoritmo: depende de la interfaz `EstrategiaPuntuacion`. La estrategia inicial, **híbrida**, describe cada oferta con cinco características normalizadas de 0 a 1:
- **precio**, **comodidad** y **cercanía/rapidez** (basadas en el contenido de la oferta);
- **popularidad** (cuántos viajeros aceptaron ese producto, tomado del almacén analítico anonimizado);
- **afinidad** (proveedores y tipos de reserva que el propio viajero usa en su historial).

El puntaje es el promedio ponderado por **pesos propios de cada viajero**. Cada sugerencia incluye las características que más aportaron, para explicarle al usuario por qué se le sugiere.

**Alternativas evaluadas:**
- *Reglas fijas en el servicio:* simple, pero cambiar el criterio obliga a modificar el servicio.
- *Modelo de *machine learning* externo desde el inicio:* más potente, pero exige datos de entrenamiento que una plataforma nueva no tiene (arranque en frío) y agrega un sistema externo más.

### Pros:
- El algoritmo se puede reemplazar por uno entrenado cuando haya datos, sin tocar el servicio ni la API.
- El modelo híbrido funciona desde el primer día (contenido) y mejora con el uso (popularidad y afinidad).
- Las sugerencias son explicables.

### Contras:
- El modelo lineal es menos preciso que uno entrenado con muchos datos.

### Tácticas aplicadas:
- **Abstraer servicios comunes / Usar una interfaz (*Use an intermediary / Abstract common services*):** el servicio depende de la abstracción de la estrategia.
- **Diferir el enlace (*Defer binding*):** la estrategia concreta se inyecta al construir el sistema.

### Drivers afectados:
- **QA-M2:** un nuevo algoritmo sin cambios en el servicio, la API ni el contrato.
- **US-08:** análisis sobre el historial y las preferencias del usuario.

---

## Concepto 3: Ciclo *human-in-the-loop* con feedback como evento y aprendizaje online de pesos

El viajero puede **aceptar** una sugerencia (se reserva en el proveedor y se agrega al viaje), **rechazarla** indicando opcionalmente el motivo (precio, ubicación, comodidad, horario, otro) o **ajustar parámetros** explícitos (presupuesto máximo, distancia máxima al centro, categoría mínima, medio de transporte preferido). Cada decisión se publica como evento `recomendacion.feedback`. Un consumidor asíncrono **actualiza los pesos del viajero**: al aceptar, ganan peso las características en las que la elegida superaba a las demás del grupo; al rechazar, lo pierden; un motivo de rechazo explícito refuerza la característica indicada. Después recalcula sus sugerencias. Lo rechazado no se vuelve a sugerir.

**Alternativas evaluadas:**
- *Solo filtros explícitos:* el usuario configura todo a mano; no hay aprendizaje y no cumple el refinamiento continuo que pide la Opción A.
- *Reentrenamiento batch periódico:* aprende, pero el usuario no ve el efecto de su decisión hasta el día siguiente.

### Pros:
- El efecto del feedback se ve en segundos, sin bloquear la interacción.
- Combina preferencias explícitas (parámetros) e implícitas (decisiones).
- El mismo evento alimenta el almacén analítico, que mide la efectividad (tasa de aceptación) para el equipo de datos.

### Contras:
- Con pocas decisiones los pesos pueden oscilar; se acotan entre un mínimo y un máximo para evitarlo.

### Tácticas aplicadas:
- **Publicar-suscribir (*Publish-subscribe*):** el feedback es un evento con contrato JSON Schema; lo consumen el aprendizaje y la analítica sin conocerse entre sí.
- **Mantener el modelo del usuario (*Maintain user model*):** parámetros y pesos aprendidos por viajero.

### Drivers afectados:
- **US-08:** el usuario interactúa con las sugerencias y refina continuamente el modelo.
- **QA-R4:** el aprendizaje ocurre fuera del camino de la solicitud.

---

## Concepto 4: Puerto de catálogo separado y degradación controlada (función no crítica)

Para buscar alternativas y reservarlas, se agrega el puerto **`AdaptadorCatalogo`**, separado del adaptador de reservas de la Iteración 3: un proveedor puede ofrecer catálogo o no, sin modificar su adaptador de reservas. Cada adaptador traduce el formato del proveedor a una **`Oferta` canónica**, igual que el Modelo Canónico de Reserva.

El módulo se diseña como **función no crítica**:
- Si un catálogo no responde, se omite y se sugiere con los demás; el mensaje no falla ni se reintenta indefinidamente.
- Si el catálogo falla al aceptar, la API responde `503` con `Retry-After` y la sugerencia sigue disponible.
- Bajo sobrecarga, la protección de carga de la API (Iteración 4) rechaza primero las rutas no críticas (recomendaciones y analítica) para preservar el panel de viajes.

### Pros:
- La falla del recomendador o de un catálogo nunca afecta las funciones críticas.
- Incorporar un catálogo nuevo es registrar un adaptador (mismo mecanismo que QA-I1).

### Contras:
- Durante un pico extremo el usuario puede no ver sugerencias justo cuando hay disrupciones; se acepta porque el panel de viajes tiene prioridad.

### Tácticas aplicadas:
- **Patrón Adaptador / Modelo canónico:** desacopla los formatos de cada proveedor.
- **Detección de excepciones e ignorar el componente fallido (*Exception handling / Removal from service*).**
- **Degradación (*Degradation*) / Desprendimiento de carga (*Load shedding*):** se suspenden las funciones no críticas bajo sobrecarga.

### Drivers afectados:
- **QA-D3:** 0 minutos de inactividad del panel ante fallas del recomendador o de un catálogo.
- **QA-E1:** la nueva carga no compite con las funciones críticas durante un pico.
- **QA-M2:** un catálogo nuevo sin modificar el servicio.

---

## Concepto 5: Privacidad por diseño en el aprendizaje

El modelo usa solo el **historial propio** del viajero y **agregados anonimizados** de los demás (popularidad). El feedback se guarda en el almacén analítico con el identificador de usuario anonimizado (el mismo mecanismo de anonimización de la Iteración 4). Solo el dueño de una sugerencia puede decidir sobre ella.

### Tácticas aplicadas:
- **Autorizar actores (*Authorize actors*):** cada decisión verifica que la sugerencia pertenezca al usuario autenticado.
- **Limitar la exposición de datos (*Limit exposure* / anonimización).**

### Drivers afectados:
- **QA-S3:** 100 % de las decisiones ajenas rechazadas y 0 identificadores en el almacén analítico.

# Paso 5: Registrar decisiones de diseño

| Decisión de diseño y ubicación | Justificación | ADR |
|---|---|:---:|
| **Agregar un módulo "Sistema de Recomendación" en la Capa 2 que precalcula las sugerencias de forma asíncrona a partir de eventos.** | Calcular en la solicitud consultaría varios catálogos externos y rompería los 800 ms del panel. Precalcular a partir de `reserva.cambiada` reutiliza el bus y los *workers* elásticos, mantiene la consulta como una simple lectura y permite reaccionar a una cancelación en minutos. | [0019](../adr/19-modulo-de-recomendacion-con-precalculo-asincrono-dirigido-por-eventos.md) |
| **Definir la puntuación como una estrategia intercambiable (Strategy), con una estrategia inicial híbrida de contenido, popularidad y afinidad, ponderada por pesos de cada viajero.** | Una plataforma nueva no tiene datos para entrenar un modelo desde el día uno. El modelo híbrido funciona desde el inicio y es explicable, y la interfaz permite reemplazarlo por uno entrenado sin tocar el resto del módulo. | [0020](../adr/20-estrategia-de-puntuacion-intercambiable-con-modelo-hibrido.md) |
| **Implementar el ciclo human-in-the-loop publicando cada decisión como evento `recomendacion.feedback` y actualizando online los pesos del viajero.** | La Opción A exige que la interacción del usuario refine continuamente el modelo. Procesar el feedback como evento hace visible el efecto en segundos sin bloquear al usuario, y el mismo evento alimenta la medición de efectividad en el almacén analítico. | [0021](../adr/21-human-in-the-loop-con-feedback-como-evento-y-aprendizaje-online.md) |
| **Agregar el puerto `AdaptadorCatalogo` con un modelo canónico de `Oferta`, separado del adaptador de reservas.** | Separar la consulta de catálogo de la sincronización de reservas permite que cada proveedor ofrezca o no catálogo sin modificar su adaptador existente, y aplicar el mismo mecanismo de registro que facilita incorporar proveedores. | [0022](../adr/22-puerto-de-catalogo-de-ofertas-separado-con-modelo-canonico.md) |
| **Tratar las recomendaciones como función no crítica: omitir catálogos caídos y suspender el módulo bajo sobrecarga.** | Una sugerencia es un valor agregado; el panel de viajes no. Aislar las fallas del módulo y desprender su carga durante los picos garantiza que la nueva funcionalidad no degrade la disponibilidad ni la latencia ya comprometidas. | [0023](../adr/23-recomendaciones-como-funcion-no-critica-con-degradacion-controlada.md) |
| **Aprender solo del historial propio y de agregados anonimizados; guardar el feedback anonimizado en el almacén analítico.** | El historial de viajes es información personal. Limitar los datos que usa el modelo y anonimizar lo que llega a la analítica permite personalizar y medir la efectividad sin exponer a ningún viajero. | [0024](../adr/24-privacidad-en-el-aprendizaje-de-preferencias.md) |

---

# Paso 6: Vistas e instanciación de elementos y responsabilidades

Los diagramas de esta iteración (módulos, componentes y conectores, y secuencia del ciclo *human-in-the-loop*) están en [[ADD-Iteración-5-Diagramas]].

## Asignación de responsabilidades

### Capa 1: Cliente
- **Pestaña "Sugerencias" (web):** mostrar las sugerencias agrupadas por necesidad del viaje (disrupción, transporte, alojamiento), con la explicación de cada una; permitir aceptar, rechazar con motivo y ajustar parámetros.

### Capa 2: Servidor de aplicaciones
- **API de recomendaciones:** listar sugerencias precalculadas, aceptar, rechazar, consultar y ajustar preferencias y pedir un recálculo. Ruta marcada como no crítica en la protección de carga.
- **Servicio de Recomendaciones:** orquestar el precálculo, aplicar los filtros del usuario, diversificar (una sugerencia por producto), resolver las decisiones del usuario y publicar el feedback.
- **Detector de necesidades:** analizar el itinerario y detectar noches sin alojamiento, tramos sin cubrir y reservas canceladas sin reemplazo.
- **Estrategia de puntuación (híbrida):** calcular las características y el puntaje de cada oferta con los pesos del viajero.
- **Aprendizaje de preferencias:** actualizar los pesos del viajero con cada decisión.
- **Adaptadores de catálogo:** buscar ofertas y reservar en cada proveedor, traduciendo a la `Oferta` canónica.
- **Consumidores asíncronos:** `recomendador` (sobre `reserva.cambiada`), `recomendador-solicitudes` (sobre `recomendacion.solicitada`) y `aprendizaje-recomendaciones` (sobre `recomendacion.feedback`).
- **Planificador:** tarea periódica de recomendaciones proactivas para todos los viajes activos.

### Capa 3: Datos
- **Base operacional (OLTP):** tablas de sugerencias precalculadas (con su estado: pendiente, aceptada, rechazada, descartada) y de preferencias por viajero (parámetros y pesos).
- **Almacén analítico (OLAP):** hechos de feedback anonimizados, usados para la popularidad y para la efectividad de las recomendaciones.

---

## Conectores y comunicación entre componentes

| Conector | Responsabilidad |
|---|---|
| **REST `/api/v1/recomendaciones`** | Consultas y decisiones del viajero; contrato en `specs/openapi.json`. |
| **Evento `reserva.cambiada`** | Dispara el recálculo de las sugerencias del viajero cuando cambia su viaje. |
| **Evento `recomendacion.solicitada`** | Pedido de recálculo explícito (usuario) o proactivo (planificador). |
| **Evento `recomendacion.feedback`** | Lleva cada decisión al aprendizaje de preferencias y al almacén analítico. |
| **APIs de catálogo externas** | Búsqueda de ofertas y reserva en el proveedor, a través de los adaptadores. |
| **Notificaciones** | Aviso al viajero cuando una disrupción genera alternativas. |

---

# Paso 7: Revisión final de todos los drivers del sistema

Los drivers resueltos en las iteraciones 1 a 4 mantienen su estado (ver la revisión de la [[ADD-Iteración-4]]). Las decisiones de esta iteración no los afectan negativamente: el módulo no agrega trabajo al camino de las solicitudes críticas y se suspende primero bajo sobrecarga.

| Categoría | Identificador y Nombre | Iteración donde se resolvió | Estado Final |
|---|---|:---:|:---:|
| **Requerimientos Funcionales** | **US-01** a **US-07** | Iteraciones 2, 3 y 4 | **Completamente Satisfecho** |
| | **US-08:** Recomendaciones con *human-in-the-loop* | **Iteración 5** | **Completamente Satisfecho** |
| **Atributos de Calidad** | **QA-R1** a **QA-U2** (escenarios de la 1ra entrega) | Iteraciones 1 a 4 | **Completamente Satisfecho** |
| | **QA-R4:** Sugerencias sin penalizar la latencia | **Iteración 5** | **Completamente Satisfecho** |
| | **QA-D3:** Falla del recomendador o de un catálogo | **Iteración 5** | **Completamente Satisfecho** |
| | **QA-M2:** Nuevo algoritmo o nuevo catálogo | **Iteración 5** | **Completamente Satisfecho** |
| | **QA-S3:** Privacidad del aprendizaje de preferencias | **Iteración 5** | **Completamente Satisfecho** |
| | **QA-E1:** Pico por disrupción masiva (revisado) | Iteración 4 y 5 | **Completamente Satisfecho** |
| **Restricciones y Concerns** | **CON-1** a **CON-3**, **CRN-1** | Iteraciones 1 a 4 | **Completamente Satisfecho** |
