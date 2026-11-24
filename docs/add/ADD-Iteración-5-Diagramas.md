# Diagrama de módulos

```mermaid
flowchart TB
  subgraph C1["Capa 1 · Cliente"]
    WEB["Interfaz web<br/>pestaña Sugerencias"]
  end
  subgraph C2["Capa 2 · Servidor de aplicaciones"]
    API["API / Acceso al sistema<br/>(ruta no crítica: /recomendaciones)"]
    subgraph REC["Sistema de Recomendación (nuevo)"]
      SRV["Servicio de Recomendaciones"]
      DET["Detector de necesidades"]
      EST["«interfaz» Estrategia de puntuación"]
      HIB["Estrategia híbrida"]
      APR["Aprendizaje de preferencias"]
    end
    GV["Gestión de viajes y reservas"]
    subgraph INT["Integración con servicios externos"]
      CAT["«puerto» Adaptador de catálogo<br/>(nuevo)"]
      PRO["Adaptadores de proveedores"]
    end
    ASY["Procesamiento asíncrono<br/>bus · workers · planificador"]
  end
  subgraph C3["Capa 3 · Datos"]
    OLTP[("OLTP<br/>sugerencias y preferencias")]
    OLAP[("OLAP<br/>feedback anonimizado")]
  end
  WEB --> API --> SRV
  SRV --> DET & EST & APR
  HIB -. implementa .-> EST
  SRV --> CAT & GV
  SRV --> OLTP
  SRV --> OLAP
  ASY --> SRV
  CAT --> PRO
```

El Sistema de Recomendación es un módulo nuevo de la Capa 2. Depende de la gestión de viajes (para leer el itinerario y agregar la reserva aceptada), de la integración con servicios externos (a través del nuevo puerto de catálogo) y del procesamiento asíncrono (que le entrega los eventos). El algoritmo de puntuación queda detrás de una interfaz, de modo que la estrategia híbrida se puede reemplazar sin tocar el servicio.

---

# Diagrama de componentes y conectores

```mermaid
flowchart LR
  U["Viajero"] -->|"REST /recomendaciones<br/>(solo lectura de lo precalculado)"| API["API"]
  API -->|aceptar / rechazar / ajustar| SRV["Servicio de Recomendaciones"]
  API -->|leer| OLTP[("OLTP")]
  SR["Servicio de Reservas"] -->|reserva.cambiada| BUS[["Bus de eventos"]]
  PLA["Planificador"] -->|recomendacion.solicitada| BUS
  SRV -->|recomendacion.feedback| BUS
  BUS -->|recomendador| SRV
  BUS -->|aprendizaje-recomendaciones| SRV
  SRV -->|buscar / reservar| CAT["Adaptadores de catálogo"]
  CAT -->|API del proveedor| EXT["Catálogos externos<br/>(hoteles, autos, trenes, vuelos)"]
  SRV -->|guardar sugerencias y pesos| OLTP
  SRV -->|hechos anonimizados| OLAP[("OLAP")]
  SRV -->|aviso de disrupción| NOT["Notificaciones"]
```

Las flechas hacia y desde el bus son asíncronas; las solicitudes del viajero son síncronas pero solo leen sugerencias ya calculadas, o registran una decisión y devuelven el control de inmediato. El cálculo, la consulta a catálogos externos y el aprendizaje ocurren en los consumidores.

---

# Diagrama de secuencia: ciclo *human-in-the-loop*

```mermaid
sequenceDiagram
  participant V as Viajero (web)
  participant A as API /recomendaciones
  participant S as Servicio de Recomendaciones
  participant C as Adaptador de catálogo
  participant R as Servicio de Reservas
  participant B as Bus de eventos
  participant W as Worker (aprendizaje)
  participant O as OLAP

  Note over R,B: Cambio en el viaje (alta, cancelación...)
  R->>B: publicar(reserva.cambiada)
  B->>S: recomendador: recalcular_usuario()
  S->>S: detectar necesidades del viaje
  S->>C: buscar ofertas
  S->>S: filtrar por parámetros, puntuar (estrategia), diversificar
  S->>S: guardar sugerencias pendientes (OLTP)

  V->>A: GET /recomendaciones
  A-->>V: sugerencias precalculadas + explicación

  alt Acepta
    V->>A: POST /recomendaciones/{id}/aceptar
    A->>S: aceptar()
    S->>C: reservar(oferta)
    S->>R: agregar la reserva confirmada al viaje
    S->>B: publicar(recomendacion.feedback: aceptada)
    A-->>V: 201 reserva creada
  else Rechaza (con motivo)
    V->>A: POST /recomendaciones/{id}/rechazar {motivo}
    S->>B: publicar(recomendacion.feedback: rechazada)
    A-->>V: 204
  else Ajusta parámetros
    V->>A: PUT /recomendaciones/preferencias
    S->>B: publicar(recomendacion.feedback: ajuste)
    A-->>V: 200 preferencias
  end

  B->>W: aprendizaje-recomendaciones
  W->>W: actualizar pesos del viajero
  W->>O: registrar feedback anonimizado
  W->>S: recalcular_usuario()
  Note over V,S: La próxima consulta ya refleja la decisión
```

El diagrama muestra el ciclo completo: el cambio en el viaje dispara el precálculo, el viajero decide y su decisión vuelve como evento para ajustar el modelo y recalcular, siempre fuera del camino de la solicitud.
