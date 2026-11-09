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

### Variables de entorno (backend/.env)

```text
DATABASE_URL=postgresql+asyncpg://cuep:CAMBIAR@localhost:5432/cuep
JWT_SECRET=<hex 64>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
WORKER_API_KEY=<hex 32>
CORS_ORIGINS=https://app.example.com
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=cuep-files
R2_PUBLIC_BASE=https://files.example.com
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=CUEP
SOLVER_TIMEOUT=300
TOTP_ENCRYPTION_KEY=<fernet key>
```

Genera la clave Fernet con:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
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
# NEXT_PUBLIC_API_URL=https://api.example.com/api/v1
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
- R2 puede sustituirse por almacenamiento local en desarrollo (`STORAGE_BACKEND=local`, carpeta `./uploads`).
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
cd backend && source .venv/bin/activate && pip install -r requirements.txt && alembic upgrade head
cd ../frontend && npm ci && npm run build
cd ../worker && source .venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart cuep-api cuep-web
```

## 10. CI/CD

El repositorio incluye `.github/workflows/ci.yml` con:
- Backend: migraciones, seed, ruff, pytest.
- Frontend: lint y build.
- Worker: compilación.

## 11. Solución de problemas

- **Error de conexión a PostgreSQL**: verificar `DATABASE_URL`, usuario y contraseña.
- **Error de migración por columnas NOT NULL**: ejecutar `alembic upgrade head` después de actualizar código.
- **2FA no envía correo**: verificar SMTP o revisar logs; en desarrollo el código se imprime en consola.
- **Worker no toma tareas**: verificar `WORKER_API_KEY` y `API_BASE_URL`.
- **Frontend no conecta a API**: verificar `NEXT_PUBLIC_API_URL` y CORS.
