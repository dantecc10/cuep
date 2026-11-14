# 03 — API REST

Base URL: `https://<host>/api/v1`. Formato JSON. Auth: Bearer JWT (usuarios) y `X-Worker-Key` (worker).

## Autenticación

- `POST /auth/login` → `{ access_token, token_type }`
- `POST /auth/refresh`
- Roles: `admin`, `coordinador`, `subcoordinador`, `inscripcion`, `tutor`, `alumno`.

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

## Perfil completo del estudiante

- `POST /auth/register` acepta campos básicos y extendidos del aspirante.
- `GET /students/me` devuelve el perfil completo, incluyendo `matricula`.
- `PUT /students/me` permite actualizar campos del perfil, excepto `matricula` y `folio`.
- `GET /mi-credencial` (frontend) muestra la matrícula y su código QR.

## Sedes

- `POST /sedes` y `PUT /sedes/{id}` aceptan `codigo` (carácter único de la sede).

## Módulo de inscripción anual

Prefijo `/inscripciones`, `/pagos` y `/notificaciones`. Roles de staff:
`admin`, `coordinador`, `subcoordinador` y `inscripcion` (el rol `inscripcion`
opera su sede: check-in, efectivo y consulta; no exporta ni valida
transferencias).

### Configuración del ciclo

- `GET /inscripciones/config` (público) → `{ anio, registro_abierto, simulacro_activo, simulacro_monto, simulacro_moneda, pago_efectivo_habilitado, transferencia_habilitada, transferencia_banco, transferencia_titular, transferencia_clabe, transferencia_instrucciones, parcialidades_permitidas, parcialidades_max, donativo_obligatorio, donativo_descripcion }`
- `PUT /inscripciones/config` (admin) → actualiza los mismos campos.

### Alumno

- `GET /inscripciones/me` → perfil, matrícula, QR, estatus, cargos, pagos, eventos y saldo.
- `GET /inscripciones/me/pase` → PDF del pase con QR.
- `POST /pagos/simulacro` → activa el opt-in y crea el cargo del año (`{ cargo, creado }`).
- `GET /pagos/me` → historial de pagos del alumno.
- `POST /pagos` body: `{ cargo_id, monto, metodo: "transferencia", referencia?, fecha_pago? }` → registra pago del alumno (sólo transferencias).
- `POST /pagos/{pago_id}/comprobante` (multipart) → sube comprobante a storage privado.
- `GET /pagos/{pago_id}/comprobante` → URL firmada (TTL 15 min); 503 si no hay storage privado configurado.
- `GET /pagos/{pago_id}/recibo` → PDF del recibo (sólo pagos `validado`).

### Staff

- `GET /inscripciones?anio=&sede_id=&estatus=&nivel=&area=&search=&page=&page_size=&sort_by=&sort_dir=` → padrón paginado. Sin `anio` devuelve todos los años; el frontend filtra por el año activo.
- `GET /inscripciones/{student_id}` → detalle con cargos, pagos, eventos y saldo.
- `GET /inscripciones/{student_id}/eventos` → bitácora del alumno.
- `PATCH /inscripciones/{student_id}/estatus` body: `{ estatus }` → cambia el estatus y registra evento.
- `POST /inscripciones/checkin` body: `{ identificador, sede_id? }` → busca por matrícula, QR, correo o teléfono y confirma asistencia.
- `GET /inscripciones/{student_id}/pase` → PDF del pase.
- `GET /inscripciones/export.csv?anio=&sede_id=&estatus=&nivel=&area=&search=` → CSV con BOM UTF-8 (admin/coordinador/subcoordinador).
- `GET /pagos?estatus=&metodo=&sede_id=&search=` → listado de pagos con filtro de sede para roles no admin.
- `GET /pagos/{pago_id}` → detalle del pago.
- `POST /pagos` body: `{ cargo_id, monto, metodo: "efectivo", referencia? }` → cobro en sede (requiere `pago_efectivo_habilitado`).
- `POST /pagos/{pago_id}/validar` body: `{ aprobado, motivo? }` → valida o rechaza una transferencia (admin/coordinador/subcoordinador).

### Notificaciones

- `GET /notificaciones/plantillas` (admin) → catálogo de plantillas.
- `PUT /notificaciones/plantillas/{clave}` (admin) → actualiza asunto, cuerpo y variables.
- `GET /notificaciones/outbox?estado=&page=` (admin) → cola de envío.
- `POST /notificaciones/enviar` body: `{ student_id, clave, contexto?, dedupe_key? }` (admin/coordinador) → encola un aviso.
- `POST /notificaciones/outbox/{outbox_id}/reintentar` (admin) → reintenta un envío fallido.
- `POST /notificaciones/procesar?limit=` (admin) → procesa la cola en el proceso de la API.
- `POST /worker/notificaciones?limit=` (`X-Worker-Key`) → misma operación desde el worker.

### Errores frecuentes del módulo

- 403 `El registro está cerrado por el momento.` → `registro_abierto = false`.
- 409 `Email ya registrado.` / `Teléfono ya registrado.` → duplicados en el padrón.
- 409 `La inscripción está cancelada o de baja` → el alumno ya no admite check-in.
- 404 `La sede no tiene código de matrícula configurado.` → sede sin `codigo` de un carácter.
- 503 `Almacenamiento privado no configurado` → falta `R2_PRIVATE_BUCKET`.
