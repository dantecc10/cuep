# 09 — Seguridad

## Autenticación

- Usuarios: JWT (HS256) con `access` (15 min) + `refresh` (7 días) en httpOnly cookie.
- Worker: API key estática en header `X-Worker-Key`, comparación constant-time (`hmac.compare_digest`).

## Autorización

- RBAC por rol: `admin`, `coordinador`, `tutor`.
- Middleware FastAPI valida token y rol por endpoint.

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
