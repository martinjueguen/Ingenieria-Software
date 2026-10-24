# Atributos de calidad

Las actualizaciones de viaje deben presentarse en la aplicación dentro de los 5 minutos posteriores a su generación por la fuente externa. El tiempo de respuesta desde la web debe ser de 800 ms. En plataformas móviles, el primer despliegue de contenido debe ocurrir en menos de 1.4 segundos.

## 1. Rendimiento y Latencia

Las actualizaciones de viaje deben presentarse en la aplicación dentro de los 5 minutos posteriores a su generación por la fuente externa. El tiempo de respuesta desde la web debe ser de 800 ms. En plataformas móviles, el primer despliegue de contenido debe ocurrir en menos de 1.4 segundos.

**Clasificación:** Rendimiento

### R1 · Propagación de actualizaciones

- **Fuente:** Sistema externo (aerolínea, hotel o arrendadora) que genera el cambio.
- **Estímulo:** Evento esporádico de actualización de una reserva (ej. cancelación o cambio de puerta).
- **Ambiente:** Operación normal.
- **Artefacto:** Pipeline de ingesta de actualizaciones y vista del viaje en la app.
- **Respuesta:** Recibe, normaliza, persiste y muestra la actualización en el viaje.
- **Medida:** ≤ 5 minutos desde que la fuente la genera hasta que se ve en la app.

### R2 · Latencia web

- **Fuente:** Viajero desde un navegador web.
- **Estímulo:** Solicitud para ver el panel con sus viajes y reservas.
- **Ambiente:** Operación normal, carga habitual de la semana.
- **Artefacto:** API del panel de viajes y base de datos de itinerarios.
- **Respuesta:** Devuelve el listado de viajes con sus reservas.
- **Medida:** Tiempo de respuesta ≤ 800 milisegundos.

### R3 · Primer despliegue en móvil

- **Fuente:** Viajero desde la app móvil.
- **Estímulo:** Apertura de la app (carga inicial).
- **Ambiente:** Operación normal, red móvil 4G.
- **Artefacto:** App móvil y API de resumen de viajes.
- **Respuesta:** Muestra el primer contenido útil (resumen del próximo viaje).
- **Medida:** Primer despliegue ≤ 1.4 segundos.

## 2. Disponibilidad

Sistema global, accesible en todo momento, con un máximo de 5 minutos por mes de inactividad no planificada.

**Clasificación:** Disponibilidad

### D1 · Caída de una región

- **Fuente:** Infraestructura interna (centro de datos / región cloud).
- **Estímulo:** Caída completa de una región.
- **Ambiente:** Operación normal bajo carga.
- **Artefacto:** Región de despliegue (aplicación y base de datos de itinerarios).
- **Respuesta:** Detecta la falla, redirige el tráfico a otra región activa, notifica a operaciones y registra el incidente.
- **Medida:** 0 reservas confirmadas perdidas e indisponibilidad no planificada acumulada ≤ 5 min/mes.

### D2 · Falla de un proveedor externo

- **Fuente:** Externa (API de una aerolínea).
- **Estímulo:** Omisión (la API no responde o devuelve error).
- **Ambiente:** Operación normal.
- **Artefacto:** Conector/integración con la API de la aerolínea.
- **Respuesta:** Detecta la falla, sigue mostrando la última información conocida marcada como "última actualización", reintenta y notifica a operaciones.
- **Medida:** 0 minutos de inactividad del panel, detección en < 30 segundos y reconciliación completa en < 5 minutos tras la recuperación del proveedor.

## 3. Escalabilidad

Dimensionar para 15 millones de cuentas y 2 millones de usuarios activos semanales, con picos dramáticos ante eventos disruptivos masivos.

**Clasificación:** Rendimiento

### R4 · Pico por disrupción masiva

- **Fuente:** Viajeros afectados por una disrupción climática y sistemas externos que emiten cambios masivos.
- **Estímulo:** Pico de consultas y actualizaciones simultáneas, 5 veces el pico semanal normal.
- **Ambiente:** Carga máxima / sobrecarga.
- **Artefacto:** Sistema completo (capa web/API, ingesta y base de datos).
- **Respuesta:** Escala automáticamente y prioriza consulta de viajes y actualizaciones sobre funciones no críticas.
- **Medida:** Se mantienen ≤ 800 ms en web y ≤ 5 min de propagación.

## 4. Interoperabilidad

Integración fluida con aerolíneas, hoteles y arrendadoras mediante APIs estándar, con proveedores de correo para escanear mensajes y con redes sociales para compartir itinerarios.

**Clasificación:** Interoperabilidad

### I1 · Nuevo proveedor de viajes

- **Fuente:** Proveedor (nueva aerolínea, hotel o arrendadora) / stakeholder del negocio.
- **Estímulo:** Petición de integrar un nuevo proveedor que expone una API estándar.
- **Ambiente:** Desarrollo e integración.
- **Artefacto:** Capa de integración con proveedores (conectores) y contrato de API.
- **Respuesta:** Se agrega un adaptador que traduce al modelo canónico de reserva, se prueba y se despliega sin tocar los demás conectores.
- **Medida:** ≤ 2 semanas y 0 módulos existentes modificados.

### I2 · Nuevo proveedor de correo o red social

- **Fuente:** Stakeholder del negocio.
- **Estímulo:** Petición de agregar un nuevo proveedor de correo (escaneo) o una nueva red social (compartir itinerarios).
- **Ambiente:** Desarrollo e integración.
- **Artefacto:** Módulo de escaneo de correo y módulo de compartición social.
- **Respuesta:** Se integra mediante un adaptador con autenticación estándar (OAuth) sin modificar el motor de extracción de reservas.
- **Medida:** ≤ 2 semanas y 0 cambios en el motor de extracción.

## 5. Seguridad y Privacidad

El sistema procesa información personal; debe garantizar acceso seguro y autorizado a los correos y permitir compartir itinerarios de modo que solo las personas designadas puedan verlos.

**Clasificación:** Seguridad informática

### S1 · Acceso indebido a itinerarios compartidos

- **Fuente:** Usuario autenticado no designado o atacante externo.
- **Estímulo:** Intento no autorizado de ver un itinerario compartido (ej. manipulando un identificador o enlace).
- **Ambiente:** Operación en línea, sistema plenamente operativo.
- **Artefacto:** Servicio de compartición y datos de itinerarios.
- **Respuesta:** Autentica al actor, valida su autorización contra las personas designadas por el dueño, deniega el acceso y lo registra en la auditoría.
- **Medida:** 100 % de los accesos no autorizados bloqueados, 0 itinerarios expuestos.

### S2 · Compromiso del acceso al correo

- **Fuente:** Atacante externo con tokens robados.
- **Estímulo:** Intento no autorizado de leer el correo de un usuario con credenciales o tokens comprometidos.
- **Ambiente:** Operación en línea, operación normal.
- **Artefacto:** Servicio de escaneo de correo y almacén de tokens de acceso.
- **Respuesta:** Accede con alcance mínimo (solo lectura de correos de viaje), mantiene los tokens cifrados, detecta el uso anómalo, revoca el acceso, notifica al usuario y audita.
- **Medida:** Detección en < 5 minutos, revocación en < 1 minuto y 0 correos expuestos.

## 6. Evolucionabilidad y Mantenibilidad

Prever la integración futura de otros medios de transporte (trenes, autobuses, etc.), apoyándose en ADRs y contratos (spec-driven), con alta trazabilidad y facilidad para evaluaciones futuras.

**Clasificación:** Mantenibilidad

### M1 · Nuevo medio de transporte

- **Fuente:** Propietario del producto / desarrollador.
- **Estímulo:** Directiva de agregar un nuevo medio de transporte (ej. trenes).
- **Ambiente:** Tiempo de diseño.
- **Artefacto:** Modelo de dominio de reservas, contratos (specs) y módulo de integración.
- **Respuesta:** Se extiende el modelo y el contrato, se registra el ADR, se prueba y se despliega sin modificar los tipos de reserva existentes.
- **Medida:** ≤ 3 semanas y 0 defectos en vuelos, hoteles y autos, y 100 % de los cambios trazables a un ADR y a una spec.

## 7. Usabilidad e Internacionalización

Interfaz rica que aproveche capacidades nativas como el GPS en móviles, y sistema preparado arquitectónicamente para operar en el mercado internacional (multirregión).

**Clasificación:** Usabilidad

### U1 · Interfaz móvil con GPS

- **Fuente:** Viajero (usuario final) en su celular durante el viaje.
- **Estímulo:** Quiere saber cómo llegar a su próximo tramo (aeropuerto, estación u hotel).
- **Ambiente:** Tiempo de ejecución, móvil con GPS activo.
- **Artefacto:** GUI de la app móvil.
- **Respuesta:** Usa el GPS para mostrar el próximo tramo con la distancia o ruta hasta el punto, anticipando lo que necesita.
- **Medida:** Información accesible en ≤ 2 toques y ≤ 10 segundos, y 90 % de los usuarios nuevos completa la tarea sin ayuda.

**Clasificación:** Modificabilidad

### M2 · Nueva región o idioma

- **Fuente:** Stakeholder del negocio.
- **Estímulo:** Directiva de agregar un nuevo idioma y mercado (moneda, formatos de fecha, normativa de datos).
- **Ambiente:** Tiempo de configuración y despliegue.
- **Artefacto:** Interfaz de usuario, recursos de localización y despliegue regional.
- **Respuesta:** Se incorporan recursos de localización externos y se despliega la nueva región sin cambiar el núcleo.
- **Medida:** ≤ 1 semana, 0 líneas del código del núcleo modificadas y 0 defectos introducidos.
