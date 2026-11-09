# 03 — API REST

Base URL: `https://<host>/api/v1`. Formato JSON. Auth: Bearer JWT (usuarios) y `X-Worker-Key` (worker).

## Autenticación

- `POST /auth/login` → `{ access_token, token_type }`
- `POST /auth/refresh`
- Roles: `admin`, `coordinador`, `tutor`.

## Perfil y archivos (R2)

- `GET /usuarios/me` → perfil completo del usuario autenticado.
- `PUT /usuarios/me` body: `{ nombre, apellido_paterno, apellido_materno, telefono, biografia_md, area_principal, carga_max_horas, es_tutor }`
- `POST /usuarios/me/foto` → multipart; backend genera presigned PUT a R2 y retorna `{ upload_url, key, public_url }` (o sube directo y retorna URL).
- `GET /usuarios/{id}` → perfil público (foto, nombre, biografía) para coordinadores/tutores.
- `GET /archivos/{id}/url` → URL firmada de descarga (TTL 15 min).

## Tutores

- `GET /tutores` (coord/admin)
- `POST /tutores` (admin)
- `GET /tutores/{id}`
- `PUT /tutores/{id}/disponibilidad` body: lista de `{ dia_semana, hora_inicio, hora_fin }`
- `PUT /tutores/{id}/materias` body: lista de `{ materia_id, nivel_preferencia }`

## Materias

- `GET /materias?nivel=&area=`
- `POST /materias` (admin)

## Sedes y Grupos

- `GET /sedes`
- `POST /sedes`
- `GET /sedes/{id}/grupos`
- `POST /sedes/{id}/grupos`

## Corridas

- `POST /corridas` body:
```json
{ "sede_id": 1, "grupo_ids": [1,2,3], "parametros": { "max_horas_tutor": 12 } }
```
  → `{ "id": 42, "config_hash": "...", "estado": "PENDIENTE", "cache_hit": false }`
- `GET /corridas/{id}` → estado + resultado + métricas
- `GET /corridas?sede_id=&estado=`
- `POST /corridas/{id}/reintentar` (coord)

## Worker (protegido por X-Worker-Key)

- `GET /worker/tareas?estado=PENDIENTE&limit=1` → lista de corridas
- `POST /worker/tareas/{id}/iniciar` → marca `PROCESANDO`
- `POST /worker/tareas/{id}/resultado` body:
```json
{
  "estado": "COMPLETADO",
  "resultado_json": { "asignaciones": [ { "grupo_id":1, "tutor_id":5, "dia":2, "hora_inicio":"09:00", "hora_fin":"11:00" } ] },
  "metricas_optimizacion": { "preferencia_1": 8, "horas_huecas": 2, "balance_std": 0.4, "tiempo_solver_s": 12.3 }
}
```
- `POST /worker/tareas/{id}/error` body: `{ "detalle": "..." }`

## Códigos de error

- 400 validación, 401 no auth, 403 rol, 404 no encontrado, 409 conflicto (hash en proceso), 422 schema, 500 interno.
- Errores: `{ "detail": "mensaje" }`.

## Estudiantes e inscripciones

### Auth
- `POST /auth/register` body: `{ email, password, nombre, apellido_paterno, apellido_materno, telefono, sede_id, nivel, area }` → crea usuario rol `alumno` y perfil.

### Estudiantes
- `GET /students/me`
- `PUT /students/me` body: `{ sede_id, nivel, area, estatus }`
- `GET /groups/available?sede_id=&nivel=&area=`
- `POST /enrollments` body: `{ grupo_id }`
- `GET /enrollments/me`
- `DELETE /enrollments/{id}`
- `GET /students/me/schedule`

### Admin/Coordinador
- `GET /enrollments?grupo_id=&estado=`
- `PATCH /enrollments/{id}` body: `{ estado, payment_status }`
- `PUT /sedes/{id}/enrollment-settings` body: `{ waitlist_enabled, payment_enabled, payment_amount, payment_currency }`
