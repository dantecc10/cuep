# 08 — Despliegue Manual (sin Docker)

Guía detallada para desplegar CUEP en un servidor Linux (producción) y en un equipo local (pruebas). No utiliza contenedores.

## 1. Requisitos

- Ubuntu 22.04/24.04 LTS (servidor) o cualquier Linux/macOS/Windows (local).
- Python 3.11+ (probado con 3.12).
- Node 20+.
- PostgreSQL 16.
- Nginx.
- Git.
- Cuenta Cloudflare con bucket R2 (opcional en desarrollo).
- Clave Fernet para 2FA (`TOTP_ENCRYPTION_KEY`).

## 2. PostgreSQL

### Servidor

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE USER cuep WITH PASSWORD 'CAMBIAR';"
sudo -u postgres psql -c "CREATE DATABASE cuep OWNER cuep;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cuep TO cuep;"
```

Configura `pg_hba.conf` para acceso local y reinicia:

```bash
sudo systemctl restart postgresql
```

### Equipo local

Puedes usar PostgreSQL del sistema o una instancia local en un puerto alternativo. La URL de conexión debe usar el driver `asyncpg`:

```text
DATABASE_URL=postgresql+asyncpg://cuep:cuep_dev@127.0.0.1:5432/cuep
```

## 3. Backend (FastAPI)

```bash
cd /opt/cuep
git clone <repo> .
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# editar .env
alembic upgrade head
python seeds/load.py
```

### Datos demo para staging

El seed demo es idempotente: reutiliza sedes, planes, materias y tutores existentes y solo crea lo que falta. Antes de ejecutarlo en un servidor compartido, genera un respaldo de la base:

```bash
sudo -u postgres pg_dump -Fc cuep > /opt/cuep/backups/cuep-pre-seed-$(date +%F-%H%M%S).dump
```

Después valida y ejecuta:

```bash
cd /opt/cuep/backend
source .venv/bin/activate
python seeds/seed_demo.py --dry-run
SEED_TUTOR_PASSWORD='CAMBIAR' python seeds/seed_demo.py
```

El seed crea 30 tutores por sede para las 6 sedes objetivo, completa los 5 planes existentes a 12 materias cada uno, asigna disponibilidad y crea un grupo demo por plan y sede. Los emails usan `tutor-<codigo>-01..30@cuep.example.com`, porque los dominios `.local` son rechazados por la validación de email. Todos los tutores comparten la contraseña definida en `SEED_TUTOR_PASSWORD`.

### Aspirantes demo (formulario real)

El archivo `sources/Copia de Lic CUEP 2026.xlsx` contiene 99 respuestas reales del
formulario de inscripción. El seed `seeds/seed_aspirantes_demo.py` toma 50
registros (estratificados por sede) y los carga como aspirantes con matrícula,
folio, QR, estatus y eventos. **Sólo úsalo en staging o en la máquina local**:
los datos reales no deben salir del servidor y los correos se sustituyen por
direcciones sintéticas `@cuep.example.com`.

```bash
cd /opt/cuep/backend
source .venv/bin/activate
pip install -r requirements.txt          # incluye openpyxl
python seeds/seed_aspirantes_demo.py --dry-run
SEED_STUDENT_PASSWORD='CAMBIAR' python seeds/seed_aspirantes_demo.py
```

El seed es idempotente: si lo vuelves a ejecutar reutiliza a los aspirantes
existentes y no duplica cargos ni pagos. Requiere `registro_abierto = true` en
la configuración del ciclo. Para limpiar esos datos después del cierre anual,
usa `scripts/reset_academic_year.py --purge-demo` (ver
[10 — Cierre y Apertura Anual](10-cierre-anual.md)).

### Cierre y apertura anual

Al cambiar de ciclo se ejecuta el script de mantenimiento, que exporta el
padrón, opcionalmente respalda la base y adelanta el año activo:

```bash
cd /opt/cuep/backend
source .venv/bin/activate
python scripts/reset_academic_year.py --year 2027 --dry-run
python scripts/reset_academic_year.py --year 2027 --confirm "RESET 2027" \
  --backup /opt/cuep/backups/cuep-pre-cierre-2026.sql \
  --export-csv /opt/cuep/backups/inscripciones-2026.csv
```

El procedimiento completo está en [10 — Cierre y Apertura Anual](10-cierre-anual.md).

### Variables de entorno (backend/.env)

La plantilla completa está en `backend/.env.example`; cópiala y ajusta cada
valor. Todas las variables del backend están ahí, incluidas las nuevas del
módulo de inscripción.

```text
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://cuep:CAMBIAR@localhost:5432/cuep
PUBLIC_APP_URL=https://app.example.com
JWT_SECRET=<hex 64>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
REFRESH_COOKIE_NAME=cuep_refresh
REFRESH_COOKIE_PATH=/api/v1/auth
COOKIE_SECURE=True
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=
APP_TIMEZONE=America/Mexico_City
WORKER_API_KEY=<hex 32>
CORS_ORIGINS=["https://app.example.com"]
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=cuep-files
R2_PRIVATE_BUCKET=cuep-private
R2_PUBLIC_BASE=https://files.example.com
PAYMENT_PROOF_MAX_BYTES=10485760
SMTP_HOST=smtp.tu-dominio.mx
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=...
SMTP_FROM_NAME=CUEP
EMAIL_DEV_MODE=False
SOLVER_TIMEOUT=300
TOTP_ENCRYPTION_KEY=<fernet key>
```

Genera la clave Fernet con:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Bucket privado de comprobantes (R2)

Los comprobantes de transferencia **nunca** se guardan en el bucket público.
Hace falta un bucket propio, sin URL pública:

1. En Cloudflare R2, crea un bucket (por ejemplo `cuep-private`) **sin**dominio
   público ni `r2.dev` habilitado.
2. Crea un token de API con permiso de **lectura y escritura** sólo sobre ese
   bucket y anota `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID` y `R2_SECRET_ACCESS_KEY`.
3. Define `R2_PRIVATE_BUCKET=cuep-private` en `backend/.env` y reinicia
   `cuep-api`.

Puedes reutilizar el mismo token si tiene permisos sobre los dos buckets, pero
es más seguro crear uno sólo para el privado: en Cloudflare R2, *API Tokens →
Create Account API Token*, con el permiso **Object Read & Write** limitado al
bucket privado. El token da el `Access Key ID` y el `Secret Access Key`; el
`R2_ACCOUNT_ID` es el identificador de la cuenta (aparece en el panel de R2).

Si `R2_PRIVATE_BUCKET` está vacío, la subida de comprobantes responde **503**
con el mensaje "Falta R2_PRIVATE_BUCKET…": es intencional, para que un
comprobante nunca acabe en el bucket público. `PAYMENT_PROOF_MAX_BYTES` limita
el tamaño del archivo (10 MB por defecto); nginx debe permitir al menos ese
tamaño (`client_max_body_size 10M`).

Para comprobar el token sin desplegar:

```bash
cd /opt/cuep/backend && source .venv/bin/activate
python ../scripts/deploy_report.py --probe
```

`--probe` sube, lee y borra un archivo de prueba en el bucket privado: si
termina en verde, el token tiene permisos y el bucket existe.

### Correo (SMTP)

Las notificaciones del proceso de inscripción se envían por SMTP:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `SMTP_FROM_EMAIL`
  son obligatorios para enviar. El servidor usa `starttls()` y, si defines
  `SMTP_USER`, autentica con usuario y contraseña.
- **Sin SMTP el envío falla**: la notificación queda en estado `error` en la
  salida y el administrador lo ve en `/dashboard/notificaciones`. Nunca se
  marca como enviada si no se entregó.
- `EMAIL_DEV_MODE=true` es sólo para desarrollo local: imprime el correo en la
  consola y marca la notificación como `simulado` (visible en la salida).
  **No lo actives en el servidor.**
- Los códigos de verificación (2FA) también usan este canal: si el envío
  falla, el inicio de sesión responde 503 en lugar de dejar al usuario esperando
  un código que nunca llega.

### Drenar la salida de notificaciones

El backend guarda cada aviso en la salida (`notificacion_outbox`) y el worker
la envía. Para drenarla a mano (admin):

```bash
curl -X POST https://api.example.com/api/v1/notificaciones/procesar \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

O desde el propio servidor, con la clave del worker:

```bash
curl -X POST -H "X-Worker-Key: $WORKER_API_KEY" \
  https://api.example.com/api/v1/worker/notificaciones
```

Para no depender de que alguien lo haga a mano, instala el temporizador de
sistema (los archivos están en `infra/`):

```ini
# /etc/systemd/system/cuep-notificaciones.service
[Unit]
Description=Drena la salida de notificaciones del CUEP
After=network.target cuep-api.service
Requires=cuep-api.service

[Service]
Type=oneshot
EnvironmentFile=/opt/cuep/backend/.env
ExecStart=/bin/bash -c 'curl -sS --fail -X POST -H "X-Worker-Key: ${WORKER_API_KEY}" http://127.0.0.1:2013/api/v1/worker/notificaciones'

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/cuep-notificaciones.timer
[Unit]
Description=Envía las notificaciones pendientes del CUEP cada 5 minutos

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo cp infra/cuep-notificaciones.service infra/cuep-notificaciones.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cuep-notificaciones.timer
systemctl list-timers | grep notificaciones
```

### Usuarios con rol de inscripción

El rol `inscripcion` opera su sede: consulta el padrón, confirma asistencia y
registra cobros en efectivo (no exporta ni valida transferencias).

```bash
cd /opt/cuep/backend
source .venv/bin/activate
python scripts/manage_users.py set-role --email persona@cuep.mx --role inscripcion
python scripts/manage_users.py set-sede --email persona@cuep.mx --sede-id 3
```

### Servicio systemd

`/etc/systemd/system/cuep-api.service`:

```ini
[Unit]
Description=CUEP API
After=network.target postgresql.service
[Service]
User=cuep
WorkingDirectory=/opt/cuep/backend
EnvironmentFile=/opt/cuep/backend/.env
ExecStart=/opt/cuep/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now cuep-api
```

## 4. Frontend (Next.js)

```bash
cd /opt/cuep/frontend
npm ci
cp .env.example .env
# Si el frontend y la API comparten dominio, usa una ruta relativa:
# NEXT_PUBLIC_API_URL=/api/v1
npm run build
```

### Ejecución en producción

Opción A (servidor Node):

```bash
npm start
```

Opción B (servicio systemd):

`/etc/systemd/system/cuep-web.service`:

```ini
[Unit]
Description=CUEP Web
After=network.target
[Service]
User=cuep
WorkingDirectory=/opt/cuep/frontend
Environment=PORT=3000
ExecStart=/opt/cuep/frontend/node_modules/.bin/next start -p 3000
Restart=always
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now cuep-web
```

## 5. Worker local (PC del coordinador)

```bash
cd /opt/cuep/worker
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# API_BASE_URL=https://api.example.com/api/v1
# WORKER_API_KEY=...
python worker.py
```

Variables del worker:

```text
API_BASE_URL=https://api.example.com/api/v1
WORKER_API_KEY=<misma clave del backend>
POLL_INTERVAL=5
SOLVER_TIMEOUT=300
```

El worker puede ejecutarse en terminal o como servicio. Para pruebas basta `python worker.py`.

## 6. Nginx + SSL

`/etc/nginx/sites-available/cuep`:

```nginx
server {
  listen 80;
  server_name app.example.com api.example.com;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name app.example.com;
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
  ssl_certificate /etc/letsencrypt/live/app.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;
}

server {
  listen 443 ssl http2;
  server_name api.example.com;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    client_max_body_size 10M;
  }
  ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
}
```

Certificados:

```bash
sudo certbot --nginx -d app.example.com -d api.example.com
```

## 7. Equipo local (pruebas)

- Backend: `uvicorn app.main:app --reload`.
- Frontend: `npm run dev` (proxy a API).
- Worker apuntando a `http://localhost:8000/api/v1`.
- Sin R2 configurado, la subida de comprobantes responde 503 (no hay
  almacenamiento local alternativo: los comprobantes siempre van a R2).
- Sin SMTP configurado, pon `EMAIL_DEV_MODE=true` en `backend/.env`: los
  correos se imprimen en la consola y quedan marcados como `simulado` en la
  salida de notificaciones.
- PostgreSQL local o instancia en puerto alternativo.

## 8. Backups

Cron diario:

```bash
pg_dump -U cuep cuep | gzip > /backups/cuep_$(date +%F).sql.gz
find /backups -name '*.sql.gz' -mtime +14 -delete
```

Archivos R2: habilitar versionado del bucket.

## 9. Actualización

```bash
cd /opt/cuep && git pull
./scripts/deploy.sh
```

El script `scripts/deploy.sh` instala dependencias del backend si existe
`backend/.venv`, aplica migraciones, reinicia `cuep-api.service`, instala
dependencias del frontend, carga `frontend/.env.production.local` o
`.env.production` antes de construir Next.js y reinicia `cuep-web.service`.

Opciones:

| Opción | Para qué sirve |
|---|---|
| `--skip-frontend` | No reinstala ni reconstruye el frontend. |
| `--skip-report` | No imprime el reporte final de módulos. |
| `--strict` | Devuelve error si el reporte encuentra módulos sin configurar. |

### Reporte de estado de los módulos

Al final del despliegue el script imprime el estado de cada módulo con
colores (verde = correcto, amarillo = aviso, rojo = falta configuración):

- variables de `backend/.env`: cuáles están puestas, cuáles faltan y cuáles
  siguen con el valor de ejemplo;
- migraciones: revisión del código y la que tiene aplicada la base;
- configuración del ciclo: año, registro, simulacro, efectivo y
  transferencias;
- datos del momento: padrón del año activo, cargos, pagos por validar y cola de
  notificaciones;
- Cloudflare R2: si los buckets responden y si el privado es distinto del
  público;
- servicios: API, web, worker y temporizador de avisos.

El reporte también se puede ejecutar solo, sin desplegar:

```bash
cd /opt/cuep/backend && source .venv/bin/activate
python ../scripts/deploy_report.py
```

En `ENVIRONMENT=production` lo que falta se marca en rojo (falla) y lo
recomendable en amarillo (aviso); en desarrollo los módulos opcionales sin
configurar sólo generan avisos.

### Migraciones nuevas del módulo de inscripción

Después de actualizar el código, aplica las migraciones antes de reiniciar los
servicios:

```bash
cd /opt/cuep/backend && source .venv/bin/activate
alembic upgrade head
sudo systemctl restart cuep-api cuep-web
```

Para actualizar el worker (corre en la computadora del coordinador):

```bash
cd /opt/cuep/worker && source .venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart cuep-worker
```

Migraciones del módulo: `b1c2d3e4f5a6` (núcleo de inscripción),
`c2d3e4f5a6b7` (cargos y pagos), `d3e4f5a6b7c8` (notificaciones),
`e4f5a6b7c8d9` (plantillas), `f5a6b7c8d9e0` (estado `simulado` en la salida de
notificaciones) y `a6b7c8d9e0f1` (eventos y plantillas de asignación de
grupos).

### Si agregas variables nuevas al `.env`

`backend/.env` **no** se versiona: después de un `git pull` las variables nuevas
no aparecen solas. Compara `backend/.env.example` con tu `.env` y añade lo que
falte (por ejemplo `PUBLIC_APP_URL`, `R2_PRIVATE_BUCKET`, `EMAIL_DEV_MODE`).

## 10. CI/CD

El repositorio incluye `.github/workflows/ci.yml` con:
- Backend: migraciones, seed, ruff, pytest.
- Frontend: lint y build.
- Worker: compilación.

## 11. Solución de problemas

- **Error de conexión a PostgreSQL**: verificar `DATABASE_URL`, usuario y contraseña.
- **Error de migración por columnas NOT NULL**: ejecutar `alembic upgrade head` después de actualizar código.
- **2FA no envía correo**: el login responde 503 si el envío falla. Revisar
  `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`/`SMTP_PASSWORD` y `SMTP_FROM_EMAIL`; en
  el log del backend aparece el error del servidor SMTP. Con
  `EMAIL_DEV_MODE=true` (sólo local) el código se imprime en consola.
- **Las notificaciones quedan en `error`**: mismo diagnóstico SMTP. En
  `/dashboard/notificaciones` la columna "Error" explica el motivo.
- **Las notificaciones quedan en `simulado`**: `EMAIL_DEV_MODE` está activo en
  el servidor; hay que ponerlo en `false` y configurar SMTP.
- **Subida de comprobantes responde 503**: falta `R2_PRIVATE_BUCKET` (o las
  credenciales de R2). Recordar que el bucket privado es obligatorio y nunca es
  el público.
- **El QR o el pase apuntan a un dominio equivocado**: ajustar `PUBLIC_APP_URL`
  y reiniciar `cuep-api`.
- **Worker no toma tareas**: verificar `WORKER_API_KEY` y `API_BASE_URL`.
- **La salida de notificaciones no se drena**: activar el temporizador
  `cuep-notificaciones.timer` o llamar a `POST /notificaciones/procesar`.
- **Frontend no conecta a API**: si usa el mismo dominio, verificar `NEXT_PUBLIC_API_URL=/api/v1` y el proxy de nginx; si usa otro dominio, revisar CORS.
