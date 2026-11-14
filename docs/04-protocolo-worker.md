# 04 — Protocolo Worker

## Ciclo de vida de una tarea

```
PENDIENTE → (worker polling) → PROCESANDO → COMPLETADO | ERROR
```

## Polling

- Intervalo: 5s (env `POLL_INTERVAL`).
- Worker consulta `GET /worker/tareas?estado=PENDIENTE&limit=1`.
- Si hay tarea, llama `POST /worker/tareas/{id}/iniciar` (locking optimista; 409 si ya tomada).
- Procesa y publica resultado.

## Hash (caché)

- Al crear corrida, backend serializa entrada inmutable (tutores, disponibilidades, materias, grupos, params) a JSON canónico (claves ordenadas, sin espacios).
- `config_hash = sha256(json_canonico).hexdigest()`.
- Antes de insertar, busca corrida con mismo hash y estado `COMPLETADO`; si existe, retorna `cache_hit=true` y resultado existente (no crea nueva).
- Si existe en `PENDIENTE`/`PROCESANDO`, retorna esa corrida (dedup).

## Reintentos y timeouts

- Tarea en `PROCESANDO` más de 30 min sin resultado → backend la revierte a `PENDIENTE` (cron/health check) e incrementa `intentos`.
- Máximo 3 intentos; luego `ERROR`.
- Worker debe ser idempotente: re-ejecutar misma tarea produce mismo resultado.

## Payload de entrada al solver (worker construye)

```json
{
  "corrida_id": 42,
  "tutores": [ { "id":5, "carga_max":12, "materias": [ { "materia_id":1, "pref":1 } ], "disponibilidad": [ { "dia":2, "inicio":"09:00","fin":"12:00" } ] } ],
  "grupos": [ { "id":1, "materia_id":1, "horas_totales":4, "bloque":2 } ],
  "parametros": { "max_horas_tutor": 12 }
}
```

## Payload de salida

Ver `03-api-rest.md` → `/worker/tareas/{id}/resultado`.

## Cola de notificaciones

El worker también envía los avisos del proceso de inscripción. El backend
escribe cada aviso en `notificacion_outbox` y el worker lo entrega:

- `POST /worker/notificaciones?limit=50` → procesa la cola y devuelve
  `{ "procesados": n, "enviados": n, "simulados": n, "fallidos": n }`.
- Estados de la cola: `pendiente` → `enviado` | `simulado` | `error` |
  `cancelado`. `simulado` significa que sólo se imprimió en consola
  (`EMAIL_DEV_MODE`, desarrollo local); `error` guarda el motivo en
  `ultimo_error`.
- El envío es real: sin SMTP configurado la notificación queda en `error`, no
  en `enviado`.
- `dedupe_key` evita avisos duplicados (por ejemplo, un mismo check-in
  notificado dos veces).
- Un envío fallido guarda `ultimo_error` y puede reintentarse desde
  `POST /notificaciones/outbox/{id}/reintentar` (admin).
- Alternativa sin worker: `POST /notificaciones/procesar` (admin) procesa la
  cola desde la API.

## Seguridad

- Header `X-Worker-Key` obligatorio; comparación constant-time.
- TLS obligatorio; rechazar HTTP.
- Worker valida certificado del VPS (no deshabilitar verificación).
