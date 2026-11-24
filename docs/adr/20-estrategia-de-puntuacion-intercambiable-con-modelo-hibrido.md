# 0020. Estrategia de puntuación intercambiable (patrón Strategy) con un modelo híbrido inicial

* Estado: aceptado
* Fecha: 2026-11-24
* Iteración ADD: 5
* Drivers: QA-M2, US-08

## Contexto y problema

El recomendador tiene que ordenar las ofertas según el historial y las preferencias de cada viajero (US-08). Una plataforma nueva no tiene datos suficientes para entrenar un modelo de *machine learning*, pero el equipo de datos querrá reemplazar el algoritmo más adelante. Ese reemplazo no debería obligar a modificar el servicio, la API ni los contratos (QA-M2).

## Factores de decisión (drivers)

* **QA-M2:** nuevo algoritmo con 0 cambios en el servicio, la API y `specs/openapi.json`.
* **US-08:** análisis sobre el historial y las preferencias del usuario.
* Arranque en frío: las sugerencias tienen que ser útiles desde el primer día.

## Opciones consideradas

1. Reglas fijas dentro del Servicio de Recomendaciones.
2. Un modelo de *machine learning* externo desde el inicio.
3. Interfaz `EstrategiaPuntuacion` (patrón Strategy) con una estrategia inicial híbrida y lineal.

## Decisión

Opción elegida: "Strategy con estrategia híbrida", porque funciona sin datos de entrenamiento, es explicable y deja el algoritmo detrás de una interfaz reemplazable.

La estrategia híbrida describe cada oferta con cinco características normalizadas entre 0 y 1: **precio**, **comodidad**, **cercanía/rapidez** (contenido), **popularidad** (aceptaciones anonimizadas de otros viajeros, ADR 0024) y **afinidad** (proveedores y tipos del historial propio). El puntaje es el promedio ponderado por los pesos del viajero, que se aprenden con su feedback (ADR 0021). Cada sugerencia lleva las características que más aportaron, como explicación.

### Tácticas aplicadas

* Usar una interfaz / abstraer servicios comunes.
* Diferir el enlace (*Defer binding*): la estrategia concreta se inyecta al construir el sistema.

### Consecuencias

* Positivas: el algoritmo se reemplaza sin tocar el resto; las sugerencias son explicables; útil desde el inicio.
* Negativas: un modelo lineal es menos preciso que uno entrenado con muchos datos.

## Pros y contras de las opciones

### Opción 1: Reglas fijas

* Bueno, porque es lo más simple.
* Malo, porque cada cambio de criterio modifica el servicio, incumpliendo QA-M2.

### Opción 2: Modelo de ML externo

* Bueno, porque puede ser más preciso a largo plazo.
* Malo, porque no hay datos para entrenarlo al lanzar el producto y agrega una dependencia externa más.

### Opción 3: Strategy + modelo híbrido

* Bueno, porque permite evolucionar hacia un modelo entrenado sin cambiar el servicio.
* Bueno, porque combina contenido (arranque en frío) con señales que mejoran con el uso.
* Malo, porque la precisión inicial es limitada.

## Implementación en el prototipo

* Interfaz `EstrategiaPuntuacion` y `EstrategiaHibrida`: `trotamundos/recomendacion/estrategias.py`.
* Inyección de la estrategia: `trotamundos/app.py` (construcción de `ServicioRecomendaciones`).
* Características y pesos iniciales: `trotamundos/recomendacion/modelo.py`.
* Tests: `tests/test_iteracion5_recomendaciones.py::TestCalidad::test_estrategia_de_puntuacion_reemplazable` (otra estrategia se enchufa sin cambios) y `TestPrecalculoDeSugerencias::test_detecta_alojamiento_y_ruta_faltantes` (características y explicación).

En el prototipo la infraestructura corre en proceso o sobre SQLite, detrás de interfaces ([ADR 0017](17-stack-tecnologico-del-prototipo.md)).

## Enlaces

* [ADD Iteración 5](../add/ADD-Iteración-5.md)
* Relacionados: [ADR 0019](19-modulo-de-recomendacion-con-precalculo-asincrono-dirigido-por-eventos.md), [ADR 0021](21-human-in-the-loop-con-feedback-como-evento-y-aprendizaje-online.md), [ADR 0024](24-privacidad-en-el-aprendizaje-de-preferencias.md)
