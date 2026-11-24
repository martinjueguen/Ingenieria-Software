## 1. Rendimiento y Latencia

Las actualizaciones de viaje deben presentarse en la aplicación dentro de los 5 minutos posteriores a su generación por la fuente externa. El tiempo de respuesta desde la web debe ser de 800 ms. En plataformas móviles, el primer despliegue de contenido debe ocurrir en menos de 1.4 segundos.

**Atributo de Calidad:** Rendimiento

### QA-R1 · Propagación de actualizaciones

- **Fuente:** Sistema externo (aerolínea, hotel o arrendadora) que genera el cambio.
- **Estímulo:** Evento de actualización de una reserva (ej. cancelación o cambio de puerta).
- **Ambiente:** Operación normal.
- **Artefacto:** Pipeline de ingesta de actualizaciones y vista del viaje en la app.
- **Respuesta:** Recibe, normaliza, persiste y muestra la actualización en el viaje.
- **Medida:** ≤ 5 minutos desde que la fuente la genera hasta que se ve en la app.

### QA-R2 · Latencia web

- **Fuente:** Viajero desde un navegador web.
- **Estímulo:** Solicitud para ver el panel con sus viajes y reservas.
- **Ambiente:** Operación normal, carga habitual de la semana.
- **Artefacto:** API del panel de viajes y base de datos de itinerarios.
- **Respuesta:** Devuelve el listado de viajes con sus reservas.
- **Medida:** Tiempo de respuesta ≤ 800 milisegundos.

### QA-R3 · Primer despliegue en móvil

- **Fuente:** Viajero desde la app móvil.
- **Estímulo:** Apertura de la app.
- **Ambiente:** Operación normal, red móvil 4G.
- **Artefacto:** App móvil y API de resumen de viajes.
- **Respuesta:** Muestra el primer contenido útil (resumen del próximo viaje).
- **Medida:** Primer despliegue ≤ 1.4 segundos.

## 2. Disponibilidad

Sistema global, accesible en todo momento, con un máximo de 5 minutos por mes de inactividad no planificada.

**Atributo de Calidad:** Disponibilidad

### QA-D1 · Caída de una región

- **Fuente:** Infraestructura interna (centro de datos / región cloud).
- **Estímulo:** Caída completa de una región.
- **Ambiente:** Operación normal bajo carga.
- **Artefacto:** Región de despliegue (aplicación y base de datos de itinerarios).
- **Respuesta:** Detecta la falla, redirige el tráfico a otra región activa, notifica a operaciones y registra el incidente.
- **Medida:** 0 reservas confirmadas perdidas e indisponibilidad no planificada acumulada ≤ 5 min/mes.

### QA-D2 · Falla de un proveedor externo

- **Fuente:** Externa (API de una aerolínea).
- **Estímulo:** Omisión (la API no responde o devuelve error).
- **Ambiente:** Operación normal.
- **Artefacto:** Conector/integración con la API de la aerolínea.
- **Respuesta:** Detecta la falla, sigue mostrando la última información conocida marcada como "última actualización", reintenta y notifica a operaciones.
- **Medida:** 0 minutos de inactividad del panel, detección en < 30 segundos y reconciliación completa en < 5 minutos tras la recuperación del proveedor.

## 3. Escalabilidad

Dimensionar para 15 millones de cuentas y 2 millones de usuarios activos semanales, con picos dramáticos ante eventos disruptivos masivos.

**Atributo de Calidad:** Escalabilidad

### QA-E1 · Pico por disrupción masiva

- **Fuente:** Usuarios finales concurrentes (2 millones de usuarios activos semanales con picos concentrados entre domingo-lunes y jueves-viernes, o alertas masivas por cancelaciones climáticas).
- **Estímulo:** Aumento abrupto del tráfico de consultas concurrentes y peticiones de actualización (ej. un incremento del 300% sobre la tasa base de peticiones por segundo).
- **Ambiente:** Picos estacionales de alta demanda o disrupciones climáticas masivas imprevistas.
- **Artefacto:** Sistema completo (capa web/API, ingesta y base de datos).
- **Respuesta:** El sistema escala horizontalmente de forma elástica. Se distribuye la carga mediante balanceadores y políticas de encolamiento/caching.
- **Medida:** El sistema sostiene el servicio para la base de 15 millones de cuentas registradas y los picos de 2 millones de usuarios activos semanales, manteniendo la tasa de error por debajo del 0.1% y sin degradar la latencia de respuesta web más allá de 1.5 segundos durante el pico.

## 4. Interoperabilidad

Integración fluida con aerolíneas, hoteles y arrendadoras mediante APIs estándar, con proveedores de correo para escanear mensajes y con redes sociales para compartir itinerarios.

**Atributo de Calidad:** Interoperabilidad

### QA-I1 · Nuevo proveedor de viajes

- **Fuente:** Proveedor (nueva aerolínea, hotel o arrendadora) / stakeholder del negocio.
- **Estímulo:** Petición de integrar un nuevo proveedor que expone una API estándar.
- **Ambiente:** Desarrollo e integración.
- **Artefacto:** Capa de integración con proveedores (conectores) y contrato de API.
- **Respuesta:** Se agrega un adaptador que traduce al modelo canónico de reserva, se prueba y se despliega sin tocar los demás conectores.
- **Medida:** ≤ 2 semanas y 0 módulos existentes modificados.

### QA-I2 · Nuevo proveedor de correo o red social

- **Fuente:** Stakeholder del negocio.
- **Estímulo:** Petición de agregar un nuevo proveedor de correo (escaneo) o una nueva red social (compartir itinerarios).
- **Ambiente:** Desarrollo e integración.
- **Artefacto:** Módulo de escaneo de correo y módulo de compartición social.
- **Respuesta:** Se integra mediante un adaptador con autenticación estándar (OAuth) sin modificar el motor de extracción de reservas.
- **Medida:** ≤ 2 semanas y 0 cambios en el motor de extracción.

## 5. Seguridad y Privacidad

**Atributo de Calidad:** Seguridad

El sistema procesa información personal; debe garantizar acceso seguro y autorizado a los correos y permitir compartir itinerarios de modo que solo las personas designadas puedan verlos.

### QA-S1 · Acceso indebido a itinerarios compartidos

- **Fuente:** Usuario autenticado no designado o atacante externo.
- **Estímulo:** Intento no autorizado de ver un itinerario compartido.
- **Ambiente:** Operación en línea, sistema plenamente operativo.
- **Artefacto:** Servicio de compartición y datos de itinerarios.
- **Respuesta:** Autentica al actor, valida su autorización contra las personas designadas por el dueño, deniega el acceso y lo registra en la auditoría.
- **Medida:** 100 % de los accesos no autorizados bloqueados, 0 itinerarios expuestos.

### QA-S2 · Compromiso del acceso al correo

- **Fuente:** Atacante externo con tokens robados.
- **Estímulo:** Intento no autorizado de leer el correo de un usuario con credenciales o tokens comprometidos.
- **Ambiente:** Operación en línea, operación normal.
- **Artefacto:** Servicio de escaneo de correo y almacén de tokens de acceso.
- **Respuesta:** Accede con alcance mínimo (solo lectura de correos de viaje), mantiene los tokens cifrados, detecta el uso anómalo, revoca el acceso, notifica al usuario y audita.
- **Medida:** Detección en < 5 minutos, revocación en < 1 minuto y 0 correos expuestos.

## 6. Evolucionabilidad y Mantenibilidad

Prever la integración futura de otros medios de transporte (trenes, autobuses, etc.), apoyándose en ADRs y contratos (spec-driven), con alta trazabilidad y facilidad para evaluaciones futuras.

**Atributo de Calidad:** Modificabilidad

### QA-M1 · Nuevo medio de transporte

- **Fuente:** Propietario del producto / desarrollador.
- **Estímulo:** Directiva de agregar un nuevo medio de transporte (ej. trenes).
- **Ambiente:** Tiempo de diseño.
- **Artefacto:** Modelo de dominio de reservas, contratos (specs) y módulo de integración.
- **Respuesta:** Se extiende el modelo y el contrato, se registra el ADR, se prueba y se despliega sin modificar los tipos de reserva existentes.
- **Medida:** ≤ 3 semanas y 0 defectos en vuelos, hoteles y autos, y 100 % de los cambios trazables a un ADR y a una spec.

## 7. Usabilidad e Internacionalización

Interfaz rica que aproveche capacidades nativas como el GPS en móviles, y sistema preparado arquitectónicamente para operar en el mercado internacional (multiregión).

**Atributo de Calidad:** Usabilidad

### QA-U1 · Interfaz móvil con GPS

- **Fuente:** Viajero (usuario final) en su celular durante el viaje.
- **Estímulo:** Quiere saber cómo llegar a su próximo tramo (aeropuerto, estación u hotel).
- **Ambiente:** Tiempo de ejecución, móvil con GPS activo.
- **Artefacto:** GUI de la app móvil.
- **Respuesta:** Usa el GPS para mostrar el próximo tramo con la distancia o ruta hasta el punto, anticipando lo que necesita.
- **Medida:** Información accesible en ≤ 2 toques y ≤ 10 segundos, y 90 % de los usuarios nuevos completa la tarea sin ayuda.

### QA-U2 · Nueva región o idioma

- **Fuente:** Usuario final operando desde una región internacional con idioma, moneda y formatos horarios locales.
- **Estímulo:** El usuario cambia la configuración de localización o accede desde una nueva región geográfica.
- **Ambiente:** Tiempo de ejecución.
- **Artefacto:** Interfaz de usuario, recursos de localización y despliegue regional.
- **Respuesta:** La interfaz adapta instantáneamente todos los textos, conversiones de husos horarios locales y representación de costos en la moneda seleccionada, manteniendo la consistencia de los datos originales del proveedor.
- **Medida:** ≤ 1 semana, 0 líneas del código del núcleo modificadas y 0 defectos introducidos.

## 8. Escenarios del Sistema de Recomendación (2da entrega)

Escenarios agregados al incorporar el requerimiento avanzado **US-08** (Opción A). Refinan los atributos ya definidos para el nuevo módulo y son los drivers de la [Iteración 5](ADD-Iteración-5.md).

### QA-R4 · Sugerencias sin penalizar la latencia

**Atributo de Calidad:** Rendimiento

- **Fuente:** Viajero desde la web o la app móvil.
- **Estímulo:** Abre la pestaña de sugerencias de su viaje, o modifica una reserva del viaje.
- **Ambiente:** Operación normal.
- **Artefacto:** API de recomendaciones y Servicio de Recomendaciones.
- **Respuesta:** Devuelve las sugerencias ya calculadas sin ejecutar el algoritmo durante la solicitud; ante un cambio en el viaje, las sugerencias se recalculan en segundo plano.
- **Medida:** Consulta de sugerencias ≤ 800 ms (igual que QA-R2), 0 cálculos en el camino de la solicitud y sugerencias actualizadas ≤ 5 minutos después del cambio (igual que QA-R1).

### QA-D3 · Falla del recomendador o de un catálogo

**Atributo de Calidad:** Disponibilidad

- **Fuente:** Externa (catálogo de ofertas de un proveedor) o interna (sobrecarga del sistema).
- **Estímulo:** Un catálogo no responde, o el sistema supera su umbral de carga durante un pico.
- **Ambiente:** Operación normal o pico por disrupción masiva (QA-E1).
- **Artefacto:** Servicio de Recomendaciones, adaptadores de catálogo y protección de carga de la API.
- **Respuesta:** Omite el catálogo caído y sugiere con los demás; bajo sobrecarga suspende primero las funciones no críticas (recomendaciones) para preservar las críticas (panel de viajes).
- **Medida:** 0 minutos de inactividad del panel de viajes, 0 mensajes perdidos en la cola por la falla de un catálogo, y respuesta inmediata `503 + Retry-After` en recomendaciones mientras dura la sobrecarga.

### QA-M2 · Nuevo algoritmo de recomendación o nuevo catálogo

**Atributo de Calidad:** Modificabilidad

- **Fuente:** Equipo de datos / desarrollador.
- **Estímulo:** Reemplazar el algoritmo de puntuación (p. ej. por un modelo entrenado) o incorporar el catálogo de un nuevo proveedor.
- **Ambiente:** Tiempo de diseño.
- **Artefacto:** Módulo de recomendación (estrategia de puntuación) y puertos de catálogo.
- **Respuesta:** Se implementa una nueva estrategia o un nuevo adaptador de catálogo y se registra, sin modificar el servicio, la API ni el contrato.
- **Medida:** ≤ 1 semana, 0 cambios en el Servicio de Recomendaciones, en la API y en `specs/openapi.json`.

### QA-S3 · Privacidad del aprendizaje de preferencias

**Atributo de Calidad:** Seguridad

- **Fuente:** Usuario autenticado distinto del dueño, o miembro del equipo de datos.
- **Estímulo:** Intenta decidir sobre sugerencias ajenas, o consulta los datos de efectividad de las recomendaciones.
- **Ambiente:** Operación en línea.
- **Artefacto:** API de recomendaciones y almacén analítico.
- **Respuesta:** Solo el dueño puede aceptar, rechazar o ajustar sus sugerencias; el modelo usa el historial propio del viajero y agregados anonimizados de otros; el almacén analítico guarda el feedback con identificador anonimizado.
- **Medida:** 100 % de las decisiones sobre sugerencias ajenas rechazadas y 0 identificadores de usuario en el almacén analítico.

