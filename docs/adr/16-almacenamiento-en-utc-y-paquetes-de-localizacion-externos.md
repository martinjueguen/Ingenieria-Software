# 0016. Almacenamiento en UTC y paquetes de localización externos

* Estado: aceptado
* Fecha: 2026-11-16
* Iteración ADD: 4
* Drivers: QA-U2, CON-3

## Contexto y problema

La operación internacional (CON-3) exige atender usuarios en distintos idiomas, monedas y husos horarios. Al cambiar de localización, la interfaz debe adaptar textos, horarios y moneda manteniendo la consistencia de los datos originales del proveedor; agregar una región o idioma debe llevar ≤ 1 semana, con 0 líneas del núcleo modificadas (QA-U2). Además, los vuelos cruzan zonas horarias, y almacenar horas locales genera discrepancias.

## Factores de decisión (drivers)

* **QA-U2:** nueva región o idioma sin tocar el núcleo.
* **CON-3:** operación en el mercado internacional.

## Opciones consideradas

1. Externalizar recursos de localización (*Resource Bundles*) y normalizar todas las fechas en UTC, delegando la presentación local a la interfaz.
2. No aplicar la táctica: textos, formatos y husos horarios embebidos en el código y fechas en hora local.

## Decisión

Opción elegida: "Almacenamiento temporal estándar en UTC y paquetes de localización externos", porque mantener los registros en UTC y externalizar traducciones y formatos en archivos de configuración permite adaptar la plataforma a nuevos mercados en menos de una semana sin modificar el código fuente del núcleo.

* La API normaliza y almacena todas las fechas en UTC.
* El cliente usa paquetes de recursos estáticos por idioma y convierte al huso horario local para presentar.
* Las conversiones de divisas se aíslan en utilitarios independientes.

### Tácticas aplicadas

* Parametrizar el sistema (*Parameterize / Resource Bundles*).
* Encapsular (*Encapsulate*): conversión de divisas en utilitarios independientes.

### Consecuencias

* Positivas: agregar un idioma o moneda no requiere alterar ni recompilar el backend; consistencia temporal en viajes que cruzan zonas horarias.
* Negativas: el ADD no registra contras para este concepto; como consecuencia implícita, cada cliente asume la responsabilidad de convertir y formatear para la presentación local.

## Pros y contras de las opciones

### Opción 1: UTC + Resource Bundles

* Bueno, porque facilita incorporar mercados sin tocar el núcleo.
* Bueno, porque UTC evita discrepancias horarias.

### Opción 2: Localización embebida y hora local

* Bueno, porque no requiere conversiones en el cliente.
* Malo, porque cada nuevo idioma o región implica modificar el código del núcleo, incumpliendo QA-U2.
* Malo, porque las horas locales generan inconsistencias en vuelos entre zonas horarias.

## Implementación en el prototipo

* Paquetes de localización: `trotamundos/web/i18n/*.json`; conversión a huso horario local y moneda en el cliente: `trotamundos/web/`.
* Fechas en UTC en el modelo de dominio: `trotamundos/dominio/modelo.py`; persistencia: `trotamundos/datos/base_datos.py`.
* Contrato de la API con fechas en UTC (ISO 8601): `specs/openapi.json`.
* Configuración regional por defecto: `trotamundos/config.py`.

En el prototipo la infraestructura (bus, caché, base de datos, regiones) corre en proceso o sobre SQLite, detrás de interfaces. La decisión de stack tecnológico está en el [ADR 0017](0017-stack-tecnologico-del-prototipo.md).

## Enlaces

* [ADD Iteración 4](../add/ADD-Iteración-4.md)
* Relacionados: [ADR 0002](0002-separar-clientes-web-movil-del-backend-detras-de-una-api.md), [ADR 0012](0012-despliegue-multirregion-activo-pasivo-caliente-con-geodns.md)
