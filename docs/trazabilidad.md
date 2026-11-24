# Matriz de trazabilidad: driver → ADR → spec → código → test

Cada driver del ADD se puede seguir hasta su verificación automática. Para correr los tests: `python -m pytest`.

## Requerimientos funcionales

| Driver | ADR | Spec / contrato | Código principal | Test |
|---|---|---|---|---|
| US-01 Procesamiento de correo | 0008, 0009 | `specs/eventos/correo.recibido.schema.json`, `POST /correo/sondear` | `integracion/correo/servicio_escaneo.py`, `motor_extraccion.py`, `asincrono/consumidores.py` | `test_iteracion3_integraciones.py::TestUS01US02Correo` |
| US-02 Filtros y whitelist | 0009 | `/correo/whitelist` | `servicio_escaneo.remitente_autorizado` | `TestUS01US02Correo::test_correo_personal_nunca_se_abre`, `test_whitelist_configurable` |
| US-03 Integración con terceros | 0007, 0008 | `POST /proveedores/{p}/webhook`, `specs/eventos/proveedor.*.schema.json` | `integracion/proveedores/`, `sincronizador_proveedores.py` | `TestUS03QAR1ActualizacionesDeProveedores` |
| US-04 Gestión manual | 0003 | `POST/GET/PATCH/DELETE /reservas` | `gestion_viajes/servicio_reservas.py` | `test_iteracion2_gestion_viajes.py::TestUS04GestionManual` |
| US-05 Ciclo de vida del viaje | 0003, 0006 | `GET /viajes?incluir_archivados` | `servicio_itinerarios.py`, `gestor_ciclo_vida.py`, `asincrono/planificador.py` | `TestUS05CicloDeVida` |
| US-06 Agencia preferida | 0011 | `POST /viajes/{id}/soporte` | `integracion/agencia.py`, `api/rutas_soporte.py` | `TestUS06AgenciaPreferida` |
| US-07 Analítica | 0014 | `GET /analitica/*`, `specs/eventos/reserva.cambiada.schema.json` | `datos/almacen_analitico.py`, `consumidores.exportar_analitica` | `test_iteracion4_infraestructura.py::TestUS07Analitica` |
| US-08 Recomendaciones human-in-the-loop (2da entrega) | 0019, 0020, 0021, 0022 | `GET/POST/PUT /recomendaciones*`, `specs/eventos/recomendacion.feedback.schema.json`, `recomendacion.solicitada.schema.json` | `recomendacion/` (`servicio.py`, `generador.py`, `estrategias.py`), `integracion/catalogo.py`, `api/rutas_recomendaciones.py`, `web/app.js` (pestaña Sugerencias) | `test_iteracion5_recomendaciones.py` (`TestPrecalculoDeSugerencias`, `TestAceptar`, `TestHumanInTheLoop`, `TestDisrupcion`) |

## Atributos de calidad

| Driver | Medida | ADR | Código | Test / evidencia |
|---|---|---|---|---|
| QA-R1 Propagación | ≤ 5 min | 0008, 0010 | bus + workers; `ServicioReservas.metricas_propagacion` | `TestUS03QAR1...` (verifica `max_s < 300`); `GET /operaciones/estado` |
| QA-R2 Latencia web | ≤ 800 ms | 0004, 0006 | `datos/cache.py`, `api/rutas_viajes.py` (`X-Cache`), `Server-Timing` | `TestQAR2LatenciaWeb` |
| QA-R3 Primer despliegue móvil | ≤ 1,4 s | 0005 | `api/rutas_movil.py`, `web/movil.html` (autocontenida) | `TestQAR3ResumenMovil` (respuesta < 1 KB) |
| QA-D1 Caída de región | 0 reservas perdidas, ≤ 5 min/mes | 0012 | `datos/replicacion.py`, `infraestructura/` | `TestQAD1Multirregion`; prueba manual de failover (README) |
| QA-D2 Falla de proveedor | 0 min de inactividad del panel, detección < 30 s, reconciliación < 5 min | 0010 | `sincronizador_proveedores.verificar_salud` (cada 10 s), `consumidores.consulta_proveedor` | `TestQAD2FallaDeProveedor` |
| QA-E1 Pico por disrupción | ≤ 800 ms y ≤ 5 min bajo 5x | 0013, 0008, 0004 | `api/proteccion_carga.py`, `asincrono/workers.py` (autoescalado) | `TestQAE1PicoDeCarga` |
| QA-I1 Nuevo proveedor de viajes | ≤ 2 semanas, 0 módulos modificados | 0007 | `integracion/registro.py`, `puertos.py` | `TestQAI1QAM1NuevoProveedorYMedio` (adaptador de micros agregado solo en el test) |
| QA-I2 Nuevo correo / red social | 0 cambios en el motor de extracción | 0007, 0009 | `puertos.AdaptadorCorreo`, `AdaptadorRedSocial` | `TestQAS1...::test_red_social_solo_recibe_un_enlace` |
| QA-S1 Itinerarios compartidos | 100 % de los accesos no autorizados bloqueados | 0015 | `seguridad/autorizacion.py`, `auditoria.py` | `TestQAS1ItinerariosCompartidos` |
| QA-S2 Acceso al correo | detección < 5 min, revocación < 1 min | 0009 | `seguridad/gestor_tokens.py`, `cifrado.py` | `TestQAS2AccesoAlCorreo` (detección y revocación inmediatas) |
| QA-M1 Nuevo medio de transporte | 0 defectos en los tipos existentes, trazable | 0003, 0007, 0018 | `dominio/modelo.TIPOS_RESERVA` (tren y autobús agregados por registro) | `TestQAI1QAM1...`; toda la suite |
| QA-U1 Interfaz móvil con GPS | ≤ 2 toques, ≤ 10 s | 0005 | `web/movil.html` (Geolocation API, distancia y ruta) | `TestQAR3ResumenMovil` (coordenadas en el contrato) |
| QA-U2 Nueva región / idioma | 0 líneas del núcleo modificadas | 0016 | `web/i18n/*.json`, `config.py`, fechas UTC | `TestQAU2Internacionalizacion`, `test_reservas_y_viajes_usan_utc` |
| QA-R4 Sugerencias sin penalizar la latencia | 0 cálculos en la solicitud, ≤ 800 ms, actualizadas ≤ 5 min | 0019 | consumidores `recomendador*` en `recomendacion/servicio.py`; la API solo lee | `TestPrecalculoDeSugerencias::test_la_consulta_no_calcula` |
| QA-D3 Falla del recomendador o de un catálogo | 0 min de inactividad del panel, 0 mensajes perdidos | 0023 | `ServicioRecomendaciones._buscar`, `api/proteccion_carga.py` (`RUTAS_NO_CRITICAS`) | `TestCalidad::test_catalogo_caido_no_impide_sugerir_con_los_demas`, `test_funcion_no_critica_bajo_sobrecarga`, `TestAceptar::test_catalogo_caido_al_aceptar_responde_503` |
| QA-M2 Nuevo algoritmo o catálogo | 0 cambios en servicio, API y contrato | 0020, 0022 | `recomendacion/estrategias.EstrategiaPuntuacion`, `puertos.AdaptadorCatalogo` | `TestCalidad::test_estrategia_de_puntuacion_reemplazable` |
| QA-S3 Privacidad del aprendizaje | 100 % de decisiones ajenas rechazadas, 0 identificadores en OLAP | 0024 | `almacen_analitico.registrar_feedback` (anonimizado), `ServicioRecomendaciones._pendiente` | `TestCalidad::test_feedback_anonimizado_en_olap`, `test_solo_el_dueno_decide_sobre_sus_sugerencias` |

## Restricciones

| Driver | ADR | Evidencia |
|---|---|---|
| CON-1 APIs estándar de terceros | 0007 | Adaptadores por proveedor con formato propio (`integracion/proveedores/`) |
| CON-2 Web y móvil con GPS | 0002, 0005 | `web/index.html`, `web/movil.html` |
| CON-3 Multirregión | 0012, 0016 | `infraestructura/`, cabecera `X-Region` |
| CRN-1 Estructura del sistema | 0001 | Paquetes por capa (`docs/arquitectura.md`) |

## Contratos (spec-driven, ADR-0018)

| Contrato | Verificación |
|---|---|
| `specs/openapi.json` | `tests/test_contratos.py::test_api_coincide_con_el_contrato_openapi` |
| `specs/eventos/*.schema.json` | Validación en `BusEventos.publicar` y `test_bus_rechaza_carga_que_viola_el_contrato` |
