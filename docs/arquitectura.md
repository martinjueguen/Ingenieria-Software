# Arquitectura implementada: del ADD al código

Este documento ubica en el código cada elemento de las vistas del ADD (`docs/add/`). Las decisiones están en los ADRs (`docs/adr/`) y los contratos en `specs/`.

Estilo (ADR-0001): **cliente-servidor con procesamiento asíncrono orientado a eventos**, organizado en tres capas.

## Vista de módulos

```mermaid
flowchart TB
  subgraph C1["Capa 1 · Cliente"]
    WEB["Interfaz web<br/>web/index.html · app.js"]
    MOV["App móvil (resumen + GPS)<br/>web/movil.html"]
  end
  subgraph C2["Capa 2 · Servidor de aplicaciones"]
    API["API / Acceso al sistema<br/>api/"]
    SEG["Seguridad y control de acceso<br/>seguridad/"]
    subgraph GV["Gestión de viajes y reservas · gestion_viajes/"]
      SR["Servicio de Reservas"]
      SI["Servicio de Itinerarios"]
      CV["Gestor de Ciclo de Vida"]
    end
    subgraph INT["Integración con servicios externos · integracion/"]
      ADP["Adaptadores de proveedores<br/>proveedores/"]
      ESC["Escaneo y filtrado de correo<br/>correo/servicio_escaneo.py"]
      EXT["Motor de extracción<br/>correo/motor_extraccion.py"]
      AGE["Conector de agencia<br/>agencia.py"]
      RS["Redes sociales<br/>redes_sociales.py"]
    end
    subgraph ASY["Procesamiento asíncrono · asincrono/"]
      BUS["Bus de eventos"]
      WRK["Workers + autoescalador"]
      PLA["Planificador"]
      CON["Consumidores / Exportador analítico"]
    end
  end
  subgraph C3["Capa 3 · Datos · datos/"]
    CACHE["Gestor de caché"]
    REPO["Acceso a almacenamiento"]
    OLTP[("BD operacional OLTP")]
    OLAP[("Almacén analítico OLAP")]
    AUD[("Auditoría · tokens · whitelist")]
  end
  WEB & MOV -->|REST /api/v1| API
  API --> SEG & CACHE & GV
  GV --> REPO --> OLTP
  SR -->|invalida| CACHE
  SR -->|reserva.cambiada| BUS
  ESC -->|correo.recibido| BUS
  ADP -->|proveedor.*| BUS
  BUS --> WRK --> CON
  CON --> EXT & ADP & SR
  CON --> OLAP
  PLA --> CV & ESC & ADP
  SEG --> AUD
```

| Elemento del ADD | Iteración | Código |
|---|---|---|
| Interfaz web / Aplicación móvil | 1, 2, 3, 4 | `trotamundos/web/` |
| API / Acceso al sistema (API Controller) | 1, 2 | `trotamundos/api/` (`aplicacion.py`, `rutas_*.py`, `esquemas.py`) |
| Seguridad y control de acceso | 1, 3, 4 | `trotamundos/seguridad/autenticacion.py`, `autorizacion.py` |
| Gestor de tokens y seguridad de ingesta | 3 | `trotamundos/seguridad/gestor_tokens.py`, `cifrado.py` |
| Controlador de autorización de itinerarios (ACL) | 4 | `trotamundos/seguridad/autorizacion.py` |
| Registro de auditoría de accesos | 4 | `trotamundos/seguridad/auditoria.py` |
| Servicio de Reservas | 2 | `trotamundos/gestion_viajes/servicio_reservas.py` |
| Servicio de Itinerarios | 2 | `trotamundos/gestion_viajes/servicio_itinerarios.py` |
| Gestor de Ciclo de Vida | 2 | `trotamundos/gestion_viajes/gestor_ciclo_vida.py` |
| Modelo Canónico de Reserva | 3 | `trotamundos/dominio/modelo.py` |
| Adaptadores de proveedores turísticos | 3 | `trotamundos/integracion/proveedores/`, `sincronizador_proveedores.py` |
| Servicio de escaneo y filtrado de correo | 3 | `trotamundos/integracion/correo/servicio_escaneo.py`, `gmail.py` |
| Motor de extracción y parsing | 3 | `trotamundos/integracion/correo/motor_extraccion.py` |
| Conector de agencia preferida | 3 | `trotamundos/integracion/agencia.py` |
| Integración con redes sociales | 1, 4 | `trotamundos/integracion/redes_sociales.py` |
| Bus de eventos (colas de ingesta) | 1, 3 | `trotamundos/asincrono/bus_eventos.py` |
| Procesamiento en segundo plano (workers) | 1, 3, 4 | `trotamundos/asincrono/workers.py`, `consumidores.py`, `planificador.py` |
| Exportador analítico asíncrono | 4 | `trotamundos/asincrono/consumidores.py` (`exportar_analitica`) |
| Gestor de caché / Caché en memoria | 2 | `trotamundos/datos/cache.py` |
| Acceso a almacenamiento (Repositorio) | 1, 2 | `trotamundos/datos/repositorios.py` |
| Base de datos operacional (OLTP) | 1, 4 | `trotamundos/datos/base_datos.py` |
| Almacén de tokens y listas blancas | 3 | tablas `cuentas_correo` y `whitelist` (`datos/base_datos.py`) |
| Almacén de datos analítico (OLAP) | 4 | `trotamundos/datos/almacen_analitico.py` |
| Sistemas externos (Gmail, aerolíneas, hoteles, autos, trenes, agencias, red social) | Contexto | `trotamundos/integracion/simuladores.py` (simulados) |

## Vista de componentes y conectores

| Conector del ADD | Implementación |
|---|---|
| Solicitudes REST (HTTPS) | FastAPI `/api/v1`, contrato `specs/openapi.json` |
| Llamadas internas | Invocaciones entre servicios inyectados en `app.py` |
| Acceso a caché / Invalidación de caché | `GestorCache.obtener_o_calcular` / `invalidar_usuario` |
| Lectura y escritura / Acceso a base de datos | Repositorios → `BaseDatos` (SQLite) |
| Publicación de eventos / Eventos hacia el bus | `BusEventos.publicar` validando `specs/eventos/*.schema.json` |
| Mensajes asíncronos | Colas persistentes `mensajes` (entrega al menos una vez, backoff, cola de muertos) |
| APIs externas | Adaptadores (`integracion/`) → simuladores |
| Pipeline ETL / Eventos analíticos | `reserva.cambiada` → `exportador-analitico` → OLAP |
| Enrutamiento GeoDNS / Heartbeat | `infraestructura/gestor_trafico.py` → `GET /api/v1/salud` |
| Replicación entre regiones | `datos/replicacion.py` (gancho post-commit) |

### Secuencia de ingesta de correo (ADD Iteración 3)

```mermaid
sequenceDiagram
  participant P as Planificador
  participant E as Servicio de Escaneo
  participant T as Gestor de tokens
  participant G as Gmail (externo)
  participant B as Bus (correo.recibido)
  participant W as Worker / Motor de extracción
  participant R as Servicio de Reservas
  participant C as Caché
  P->>E: sondear_todos()
  E->>T: token_para_escaneo() (descifra, solo lectura)
  E->>G: listar_encabezados()
  loop cada correo
    alt remitente fuera de la whitelist
      E-->>E: descartar (sin leer asunto ni cuerpo)
    else autorizado
      E->>G: obtener_correo()
      E->>B: publicar(correo.recibido)
    end
  end
  B->>W: entregar mensaje
  W->>W: extraer() → Modelo Canónico
  W->>R: aplicar_actualizacion_externa()
  R->>C: invalidar_usuario()
  R->>B: publicar(reserva.cambiada)
```

## Vista de despliegue (ADD Iteración 4)

```mermaid
flowchart LR
  U["Viajeros web / móvil"] --> GTM["Global Traffic Manager<br/>(GeoDNS + heartbeat)<br/>:8000/:8010"]
  subgraph R1["Región primaria (activa) :8001"]
    A1["API + workers + planificador"] --> D1[("OLTP primaria")]
    A1 --> Q1[("Bus")]
  end
  subgraph R2["Región secundaria (pasiva caliente) :8002"]
    A2["API (workers detenidos hasta promoción)"] --> D2[("OLTP réplica")]
  end
  GTM -->|tráfico| A1
  GTM -.->|heartbeat / failover| A2
  D1 -->|replicación síncrona post-commit| D2
  A1 --> DW[("Almacén analítico OLAP")]
```

En el prototipo cada región es un proceso (`python -m trotamundos.infraestructura.region`), el GTM es un proxy HTTP (`python -m trotamundos.infraestructura.gestor_trafico`) y la replicación usa la API de *backup* de SQLite (ADR-0017).
