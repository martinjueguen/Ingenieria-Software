Atributos de calidad:  

Las actualizaciones de viaje deben presentarse en la aplicación
dentro de los 5 minutos posteriores a su generación por la fuente externa. El tiempo de respuesta desde la web debe ser de 800ms. En plataformas móviles, el primer despliegue de contenido debe ocurrir en menos de 1.4 segundos.  

1. Rendimiento y Latencia  

Las actualizaciones de viaje deben presentarse en la aplicación
dentro de los 5 minutos posteriores a su generación por la fuente externa. El tiempo de respuesta desde la web debe ser de 800ms. En plataformas móviles, el primer despliegue de contenido debe ocurrir en menos de 1.4 segundos.  

Clasificación: Rendimiento  

R1 · Propagación de actualizaciones  

Fuente: sistema externo (aerolínea, hotel o arrendadora) que genera el cambio  
Estímulo: evento esporádico de actualización de una reserva (ej. cancelación o cambio de puerta)  
Ambiente: operación normal  
Artefacto: pipeline de ingesta de actualizaciones y vista del viaje en la app  
Respuesta: recibe, normaliza, persiste y muestra la actualización en el viaje  
Medida: ≤ 5 minutos desde que la fuente la genera hasta que se ve en la app  

R2 · Latencia web  

Fuente: viajero desde un navegador web  
Estímulo: solicitud para ver el panel con sus viajes y reservas  
Ambiente: operación normal, carga habitual de la semana  
Artefacto: API del panel de viajes y base de datos de itinerarios  
Respuesta: devuelve el listado de viajes con sus reservas  
Medida: tiempo de respuesta ≤ 800 milisegundos  

R3 · Primer despliegue en móvil  

Fuente: viajero desde la app móvil  
Estímulo: apertura de la app (carga inicial)  
Ambiente: operación normal, red móvil 4G  
Artefacto: app móvil y API de resumen de viajes  
Respuesta: muestra el primer contenido útil (resumen del próximo viaje)  
Medida: primer despliegue ≤ 1.4 segundos  

2. Disponibilidad  

sistema global, accesible en todo momento, con un máximo de 5 minutos por mes de inactividad no planificada.  

Clasificación: Disponibilidad  

D1 · Caída de una región  

Fuente: infraestructura interna (centro de datos / región cloud)  
Estímulo: caída completa de una región  
Ambiente: operación normal bajo carga  
Artefacto: región de despliegue (aplicación y base de datos de itinerarios)  
Respuesta: detecta la falla, redirige el tráfico a otra región activa, notifica a operaciones y registra el incidente  
Medida: 0 reservas confirmadas perdidas e indisponibilidad no planificada acumulada ≤ 5 min/mes  

D2 · Falla de un proveedor externo  

Fuente: externa (API de una aerolínea)  
Estímulo: omisión (la API no responde o devuelve error)  
Ambiente: operación normal  
Artefacto: conector/integración con la API de la aerolínea  
Respuesta: detecta la falla, sigue mostrando la última información conocida marcada como “última actualización”, reintenta y notifica a operaciones  
Medida: 0 minutos de inactividad del panel, detección en < 30 segundos () y reconciliación completa en < 5 minutos () tras la recuperación del proveedor  

3. Escalabilidad  

dimensionar para 15 millones de cuentas y 2 millones de usuarios activos semanales, con picos dramáticos ante eventos disruptivos masivos.  

Clasificación: Rendimiento  

R4 · Pico por disrupción masiva  

Fuente: viajeros afectados por una disrupción climática y sistemas externos que emiten cambios masivos  
Estímulo: pico de consultas y actualizaciones simultáneas, 5 veces el pico semanal normal  
Ambiente: carga máxima / sobrecarga  
Artefacto: sistema completo (capa web/API, ingesta y base de datos)  
Respuesta: escala automáticamente y prioriza consulta de viajes y actualizaciones sobre funciones no críticas  
Medida: se mantienen ≤ 800 ms en web y ≤ 5 min de propagación  

4. Interoperabilidad  

integración fluida con aerolíneas, hoteles y arrendadoras mediante APIs estándar, con proveedores de correo para escanear mensajes y con redes sociales para compartir itinerarios.  

Clasificación: Interoperabilidad  

I1 · Nuevo proveedor de viajes  

Fuente: proveedor (nueva aerolínea, hotel o arrendadora) / stakeholder del negocio  
Estímulo: petición de integrar un nuevo proveedor que expone una API estándar  
Ambiente: desarrollo e integración  
Artefacto: capa de integración con proveedores (conectores) y contrato de API  
Respuesta: se agrega un adaptador que traduce al modelo canónico de reserva, se prueba y se despliega sin tocar los demás conectores  
Medida: ≤ 2 semanas y 0 módulos existentes modificados  

I2 · Nuevo proveedor de correo o red social  

Fuente: stakeholder del negocio  
Estímulo: petición de agregar un nuevo proveedor de correo (escaneo) o una nueva red social (compartir itinerarios)  
Ambiente: desarrollo e integración  
Artefacto: módulo de escaneo de correo y módulo de compartición social  
Respuesta: se integra mediante un adaptador con autenticación estándar (OAuth) sin modificar el motor de extracción de reservas  
Medida: ≤ 2 semanas y 0 cambios en el motor de extracción  

5. Seguridad y Privacidad  

el sistema procesa información personal; debe garantizar acceso seguro y autorizado a los correos y permitir compartir itinerarios de modo que solo las personas designadas puedan verlos.  

Clasificación: Seguridad informática.  

S1 · Acceso indebido a itinerarios compartidos  

Fuente: usuario autenticado no designado o atacante externo  
Estímulo: intento no autorizado de ver un itinerario compartido (ej. manipulando un identificador o enlace)  
Ambiente: operación en línea, sistema plenamente operativo  
Artefacto: servicio de compartición y datos de itinerarios  
Respuesta: autentica al actor, valida su autorización contra las personas designadas por el dueño, deniega el acceso y lo registra en la auditoría  
Medida: 100 % de los accesos no autorizados bloqueados, 0 itinerarios expuestos  

S2 · Compromiso del acceso al correo  

Fuente: atacante externo con tokens robados  
Estímulo: intento no autorizado de leer el correo de un usuario con credenciales o tokens comprometidos  
Ambiente: operación en línea, operación normal  
Artefacto: servicio de escaneo de correo y almacén de tokens de acceso  
Respuesta: accede con alcance mínimo (solo lectura de correos de viaje), mantiene los tokens cifrados, detecta el uso anómalo, revoca el acceso, notifica al usuario y audita  
Medida: detección en < 5 minutos (), revocación en < 1 minuto () y 0 correos expuestos  

6. Evolucionabilidad y Mantenibilidad  

prever la integración futura de otros medios de transporte (trenes, autobuses, etc.), apoyándose en ADRs y contratos (spec-driven), con alta trazabilidad y facilidad para evaluaciones futuras.  

Clasificación: Mantenibilidad.  

M1 · Nuevo medio de transporte  

Fuente: propietario del producto / desarrollador  
Estímulo: directiva de agregar un nuevo medio de transporte (ej. trenes)  
Ambiente: tiempo de diseño  
Artefacto: modelo de dominio de reservas, contratos (specs) y módulo de integración  
Respuesta: se extiende el modelo y el contrato, se registra el ADR, se prueba y se despliega sin modificar los tipos de reserva existentes
Medida: ≤ 3 semanas y 0 defectos en vuelos, hoteles y autos, y 100 % de los cambios trazables a un ADR y a una spec  

7. Usabilidad e Internacionalización  

interfaz rica que aproveche capacidades nativas como el GPS en móviles, y sistema preparado arquitectónicamente para operar en el mercado internaciona(multirregión).  

Clasificación: usabilidad  

U1 · Interfaz móvil con GPS  

Fuente: viajero (usuario final) en su celular durante el viaje  
Estímulo: quiere saber cómo llegar a su próximo tramo (aeropuerto, estación u hotel)  
Ambiente: tiempo de ejecución, móvil con GPS activo  
Artefacto: GUI de la app móvil  
Respuesta: usa el GPS para mostrar el próximo tramo con la distancia o ruta hasta el punto, anticipando lo que necesita  
Medida: información accesible en ≤ 2 toques y ≤ 10 segundos, y 90 % de los usuarios nuevos completa la tarea sin ayuda  

Clasificación: modificabilidad  

M2 · Nueva región o idioma  

Fuente: stakeholder del negocio  
Estímulo: directiva de agregar un nuevo idioma y mercado (moneda, formatos de fecha, normativa de datos)  
Ambiente: tiempo de configuración y despliegue  
Artefacto: interfaz de usuario, recursos de localización y despliegue regional  
Respuesta: se incorporan recursos de localización externos y se despliega la nueva región sin cambiar el núcleo
Medida: ≤ 1 semana, 0 líneas del código del núcleo modificadas y 0 defectos introducidos  

