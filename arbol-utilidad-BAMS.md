# Árbol de utilidad — Building Automation Management System (BAMS)

```
Utility
│
├── Seguridad informática (Security)
│   ├── Protección de comandos hacia dispositivos ── (H, H)
│   │     Un atacante externo intenta interceptar/modificar un comando de
│   │     apertura de puerta; el sistema lo detecta y bloquea en < 2 s,
│   │     registrando el 100% de los intentos.
│   └── Control de acceso a tableros por rol ── (M, M)
│         Un usuario interno sin permisos intenta ver eventos de otro
│         sector; el acceso se bloquea y registra en el 100% de los casos.
│
├── Seguridad física (Safety)
│   ├── Detección y respuesta a incendio ── (H, H)
│   │     Un sensor de humo detecta niveles anómalos; el sistema activa
│   │     la alarma y desbloquea las puertas de evacuación en < 3 s.
│   └── Detección de falla de sensores de intrusión ── (H, M)
│         Un sensor de intrusión deja de reportar en un sector armado;
│         la falla se detecta y notifica dentro de los 30 s.
│
├── Disponibilidad (Availability)
│   └── Continuidad de funciones críticas ── (H, H)
│         El servidor central falla; un nodo de respaldo asume el control
│         con failover < 10 s y disponibilidad 99.99% anual.
│
├── Rendimiento (Performance)
│   └── Tiempo de respuesta a comandos bajo carga ── (M, M)
│         200 comandos concurrentes en 10 s; latencia promedio < 1 s.
│
├── Usabilidad (Usability)
│   └── Curva de aprendizaje de operadores ── (M, L)
│         Un nuevo operador responde correctamente a un evento crítico
│         tras 2 horas de entrenamiento.
│
├── Integrabilidad (Integrability)
│   └── Incorporación de nuevos fabricantes/protocolos ── (H, H)
│         Se integra un controlador de otro fabricante (protocolo propio)
│         en < 3 semanas-persona, modificando < 5% del núcleo.
│
├── Modificabilidad (Modifiability)
│   └── Alta de nuevos sectores/dispositivos ── (M, L)
│         Se configura un nuevo sector en < 4 horas-persona sin afectar
│         sectores existentes.
│
└── Eficiencia energética (Energy Efficiency)
    └── Gestión de HVAC/iluminación por ocupación ── (M, L)
          Se reduce climatización/luces en sectores desocupados fuera de
          horario, ahorrando ~30% de energía sin afectar sectores ocupados.
```

(Valor de negocio, Riesgo técnico) — H: alto, M: medio, L: bajo

## Forma tabular

| Atributo de calidad | Refinamiento | Escenario ASR | (Valor, Riesgo) |
|---|---|---|---|
| Seguridad informática | Protección de comandos | Ataque intercepta/modifica comando de apertura; bloqueado < 2 s, 100% registrado | (H, H) |
| Seguridad informática | Control de acceso a tableros | Usuario sin permisos accede a otro sector; bloqueado y registrado 100% | (M, M) |
| Seguridad física | Incendio | Sensor de humo detecta anomalía; alarma y desbloqueo < 3 s | (H, H) |
| Seguridad física | Falla de sensores | Sensor de intrusión deja de reportar; detectado en < 30 s | (H, M) |
| Disponibilidad | Continuidad de funciones críticas | Falla el servidor central; failover < 10 s, disponibilidad 99.99% | (H, H) |
| Rendimiento | Tiempo de respuesta | 200 comandos concurrentes; latencia promedio < 1 s | (M, M) |
| Usabilidad | Curva de aprendizaje | Nuevo operador productivo tras 2 h de entrenamiento | (M, L) |
| Integrabilidad | Nuevos fabricantes/protocolos | Integración de controlador ajeno en < 3 semanas-persona | (H, H) |
| Modificabilidad | Alta de sectores/dispositivos | Nuevo sector configurado en < 4 h-persona sin defectos | (M, L) |
| Eficiencia energética | Gestión por ocupación | Ahorro ~30% de energía HVAC/iluminación fuera de horario | (M, L) |

## Lectura de prioridades

- **(H, H) — atención prioritaria:** protección de comandos a dispositivos, detección/respuesta a incendio, continuidad ante falla del servidor central e integración de nuevos fabricantes/protocolos. Son los requisitos que más condicionan la arquitectura (uso de gateways de protocolo, redundancia activa/pasiva, cifrado y autenticación fuerte en el canal de comandos).
- **(H, M):** detección de falla de sensores de seguridad — alto valor de negocio pero riesgo técnico moderado (mecanismos de heartbeat/redundancia ya conocidos).
- **(M, M) y (M, L):** rendimiento bajo carga, control de acceso a tableros, usabilidad, modificabilidad y eficiencia energética — importantes pero no ponen en riesgo el proyecto si se logran con algo menos de esfuerzo inicial.
