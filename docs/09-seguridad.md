# 09 — Seguridad

## Autenticación

- Usuarios: JWT (HS256) con `access` (15 min) + `refresh` (7 días) en httpOnly cookie.
- Worker: API key estática en header `X-Worker-Key`, comparación constant-time (`hmac.compare_digest`).

## Autorización

- RBAC por rol: `admin`, `coordinador`, `subcoordinador`, `tutor`, `inscripcion`, `alumno`.
- Middleware FastAPI valida token y rol por endpoint.
- Alcance por sede: `coordinador`, `subcoordinador` e `inscripcion` sólo ven y
  operan su sede; `admin` ve todas. El rol `inscripcion` opera el padrón de su
  sede, el check-in y el cobro en efectivo, pero **no** exporta el padrón ni
  valida transferencias.
- El módulo de inscripción expone:
  - sólo lectura para el alumno sobre sus propios datos (`/inscripciones/me`,
    `/pagos/me`);
  - escritura de estatus, check-in y cobros para staff con sede;
  - configuración del ciclo y plantillas de notificación sólo para `admin`.

## Transporte

- HTTPS obligatorio (TLS 1.2+), HSTS.
- CORS restringido al dominio frontend.

## Secretos

- Nunca en código ni en git. `.env` en `.gitignore`.
- Rotación de `JWT_SECRET` y `WORKER_API_KEY` documentada; revoca tokens existentes.

## Validación de entrada

- Pydantic v2 en todos los endpoints.
- Sanitización de SQL vía ORM (sin concatenación).
- Rate limiting (slowapi) en login y endpoints públicos.

## Auditoría

- Tabla `audit_log` (actor, acción, recurso, timestamp, ip).
- Logs de acceso y errores centralizados.

## Datos sensibles

- Contraseñas con bcrypt (cost ≥ 12).
- PII de tutores (email) no expuesta a roles inferiores.
- Backups cifrados en reposo (opcional, recomendado).

## Datos del proceso de inscripción

- El perfil del aspirante guarda PII: nombre, dirección, colonia, municipio,
  teléfono, contacto de emergencia y fotografía. Sólo el propio alumno y el
  staff de su sede acceden a esos campos.
- Correo y teléfono se normalizan antes de guardarse; el índice único impide
  dos registros con el mismo dato (correo en minúsculas, teléfono a 10 dígitos).
- La matrícula y el folio son inmutables: no se editan desde la API ni desde el
  frontend.
- El QR contiene un token aleatorio (`qr_token`) y no datos personales.
- Los comprobantes de transferencia se guardan en bucket privado
  (`R2_PRIVATE_BUCKET`) y se descargan con URL firmada de 15 minutos; nunca se
  sirven desde una URL pública.
- `sources/` y los archivos `.xlsx` están en `.gitignore`: el formulario real
  con datos personales no se versiona. El seed demo sustituye correos por
  dominios sintéticos `@cuep.example.com` y exige `SEED_STUDENT_PASSWORD`.
- El cierre anual (`scripts/reset_academic_year.py`) exige una frase de
  confirmación exacta (`RESET <anio>`), soporta `--dry-run` y ofrece
  `--backup` antes de escribir. La opción `--purge-demo` borra datos de
  prueba de forma irreversible: úsala sólo en staging/local.

## Almacenamiento (R2)

- Bucket privado; acceso solo vía credenciales del backend.
- Fotos de perfil: URL pública opcional con prefijo `public/`.
- Archivos privados: URLs firmadas con TTL ≤ 15 min.
- Validar tipo MIME y tamaño en backend antes de generar presigned URL.
- CORS del bucket restringido al dominio frontend.

## Hardening del servidor

- Usuario no-root para servicios.
- Solo puertos necesarios expuestos (80, 443, 22).
- Firewall (ufw) habilitado.
- Actualizaciones automáticas de seguridad.
