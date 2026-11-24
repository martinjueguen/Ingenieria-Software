# Trotamundos

TPE de Diseño de Sistemas de Software (UNICEN). En la primera entrega se hizo el proceso ADD sobre el sistema "Trotamundos". Ahora el repositorio tiene además el **prototipo** que implementa esa arquitectura.

| Qué | Dónde |
|---|---|
| Proceso ADD (copia de la wiki: drivers, 5 iteraciones, diagramas) | [`docs/add/`](docs/add/Home.md) |
| ADRs en formato MADR | [`docs/adr/`](docs/adr/README.md) |
| Del ADD al código (vistas de módulos, C&C, secuencia y despliegue) | [`docs/arquitectura.md`](docs/arquitectura.md) |
| Matriz driver → ADR → spec → código → test | [`docs/trazabilidad.md`](docs/trazabilidad.md) |
| Contratos (spec-driven): OpenAPI y JSON Schema de eventos | [`specs/`](specs/) |
| Código del prototipo | [`trotamundos/`](trotamundos/) |
| Tests por iteración y driver | [`tests/`](tests/) |

Requerimiento avanzado de la 2da entrega: se implementó la **Opción A, Sistema de Recomendación** con optimización human-in-the-loop (pestaña **Sugerencias**). El diseño está en la [Iteración 5 del ADD](docs/add/ADD-Iteración-5.md) y en los ADRs [0019](docs/adr/19-modulo-de-recomendacion-con-precalculo-asincrono-dirigido-por-eventos.md) a [0024](docs/adr/24-privacidad-en-el-aprendizaje-de-preferencias.md); código en [`trotamundos/recomendacion/`](trotamundos/recomendacion/), tests en `tests/test_iteracion5_recomendaciones.py`. El chatbot (Opción B) queda fuera de alcance.

## Requisitos

Python 3.12 o superior. No hace falta Docker ni servicios externos: la infraestructura (bus, caché, OLTP/OLAP, regiones) y los sistemas externos (Gmail, aerolíneas, hoteles, agencias) se simulan detrás de interfaces ([ADR 0017](docs/adr/17-stack-tecnologico-del-prototipo.md)).

Funciona en **Windows y Linux** (y macOS). Lo único que cambia es la ruta al Python del entorno virtual:

| Sistema | Crear el entorno | Python del entorno |
|---|---|---|
| Windows | `python -m venv .venv` | `.venv\Scripts\python` |
| Linux / macOS | `python3 -m venv .venv` | `.venv/bin/python` |

En Debian/Ubuntu, si `venv` no está disponible: `sudo apt install python3-venv`.

Windows:

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```

Linux / macOS:

```bash
python3 -m venv .venv
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

En los comandos siguientes se muestra la forma de Windows; en Linux reemplazá `.venv\Scripts\python` por `.venv/bin/python` (o activá el entorno con `source .venv/bin/activate` y usá `python`).

## Ejecutar (una región)

```bash
.venv\Scripts\python -m trotamundos --puerto 8000
```

- Panel web: http://127.0.0.1:8000
- Vista móvil (resumen del próximo tramo + GPS): http://127.0.0.1:8000/movil
- Documentación interactiva de la API: http://127.0.0.1:8000/docs

Usuarios de demo (clave `demo1234`):

| Usuario | Rol | Para probar |
|---|---|---|
| `ana@trotamundos.demo` | viajera | panel, reservas, correo, compartir, soporte |
| `bruno@trotamundos.demo` | viajero | ve el viaje que Ana le compartió |
| `carla@trotamundos.demo` | viajera | intento de acceso no autorizado (QA-S1) |
| `datos@trotamundos.demo` | analista | analítica OLAP (US-07) |
| `ops@trotamundos.demo` | operaciones | métricas de calidad, notificaciones, auditoría |

La pestaña **Simulación** del panel provoca los estímulos de los escenarios de calidad: un proveedor cambia la puerta de un vuelo (QA-R1), un proveedor se cae (QA-D2), llega un correo (US-01/US-02), alguien usa un token de correo robado (QA-S2).

Los datos se guardan en `var/`. Para empezar de cero, borrá esa carpeta.

## Ejecutar multirregión (QA-D1)

En tres terminales, desde la raíz del repositorio:

```bash
.venv\Scripts\python -m trotamundos.infraestructura.region --region secundaria --puerto 8002
```

```bash
.venv\Scripts\python -m trotamundos.infraestructura.region --region primaria --puerto 8001
```

```bash
.venv\Scripts\python -m trotamundos.infraestructura.gestor_trafico --region primaria=http://127.0.0.1:8001 --region secundaria=http://127.0.0.1:8002 --puerto 8010
```

Usá http://127.0.0.1:8010. Cada respuesta trae la cabecera `X-Region`. Si cortás la región primaria (Ctrl+C), el gestor de tráfico detecta la caída en 3 heartbeats y pasa a la secundaria, que ya tiene todas las reservas replicadas. El estado y los incidentes se ven en http://127.0.0.1:8010/gtm/estado.

## Tests

```bash
.venv\Scripts\python -m pytest
```

Si se cambia la API a propósito, hay que regenerar el contrato y revisar el diff de `specs/openapi.json`:

```bash
.venv\Scripts\python -m scripts.exportar_contrato
```

## Integrantes

Martin Jueguen · Ignacio Scaminaci · Valentin Saffarano
