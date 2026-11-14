# Documentación de Planeación — CUEP

Sistema de generación de horarios de asesorías BUAP (prepa y licenciatura).

## Guía para la organización

La carpeta [`guia-organizacion/`](guia-organizacion/README.md) explica el proyecto
con un lenguaje no técnico y está dirigida a tutores, coordinadores, estudiantes y
militantes del CUEP. Ayuda a entender qué problema se quiere resolver, cómo
participa cada persona, qué beneficios se esperan y cuál es el estado actual del
desarrollo. Incluye además una guía del ciclo de inscripción anual, el proceso
por el que las personas entran al programa.

## Índice

| # | Documento | Descripción |
|---|-----------|-------------|
| 01 | [Arquitectura Detallada](01-arquitectura.md) | Componentes, flujos, desacoplamiento de cómputo |
| 02 | [Modelo de Datos](02-modelo-datos.md) | ERD, tablas, índices, migraciones |
| 03 | [API REST](03-api-rest.md) | Endpoints, payloads, códigos de error |
| 04 | [Protocolo Worker](04-protocolo-worker.md) | Polling, hash, estados, reintentos |
| 05 | [Solver CP-SAT](05-solver-cpsat.md) | Formulación, restricciones, objetivo |
| 06 | [Casos de Uso](06-casos-uso.md) | Actores, flujos, criterios de aceptación |
| 07 | [Frontend](07-frontend.md) | Páginas, componentes, estado |
| 08 | [Despliegue Manual](08-despliegue-manual.md) | Configuración sin Docker en servidor/local |
| 09 | [Seguridad](09-seguridad.md) | Auth, roles, HTTPS, auditoría |
| 10 | [Cierre y Apertura Anual](10-cierre-anual.md) | Cierre del ciclo, cambio de año y limpieza de datos demo |

## Fundamentos matemáticos

Ver [`math/README.md`](math/README.md) para la justificación teórica y fórmulas.

## Convenciones

- Diagramas en Mermaid.
- Tiempos en UTC; zona horaria de Puebla (`America/Mexico_City`) solo en presentación.
- JSON con `snake_case`.
- Códigos HTTP estándar; errores con `{ "detail": "..." }`.
- Versionado de API: prefijo `/api/v1`.

## Fuentes

- `cuep-planning.md` (SRS original).
- `guia-identidad-grafica-cuep-ap.md` (identidad visual y sistema de diseño).
- `docs/guia-organizacion/` (explicación no técnica del proyecto y del ciclo
  de inscripción anual).
- `docs/10-cierre-anual.md` (procedimiento de fin de ciclo).

> El módulo de inscripción anual (registro, matrícula, pase, mesa de
> inscripción, simulacro, pagos y cierre de ciclo) se desarrolló después del
> SRS original y lo amplía: la convocatoria anual es el punto de entrada de las
> personas que después reciben las asesorías.
