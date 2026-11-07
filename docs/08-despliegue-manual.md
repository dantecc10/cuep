# 08 — Despliegue Manual (sin Docker)

Configuración detallada para servidor Linux (producción) y equipo local (pruebas). Sin contenedores.

## Requisitos

- Ubuntu 22.04/24.04 LTS (servidor) o cualquier Linux/macOS/Windows (local).
- Python 3.11+, Node 20+, PostgreSQL 16, Nginx, Git.
- Cuenta Cloudflare con bucket R2.

## 1. PostgreSQL

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE USER cuep WITH PASSWORD 'CAMBIAR';"
sudo -u postgres psql -c "CREATE DATABASE cuep OWNER cuep;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cuep TO cuep;"
```

Configurar `pg_hba.conf` para acceso local; reiniciar: `sudo systemctl restart postgresql`.

## 2. Backend (FastAPI)

```bash
cd /opt/cuep
git clone <repo> .
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # editar valores
alembic upgrade head
python seeds/load.py
```

`.env` (backend):
```
DATABASE_URL=postgresql+psycopg://cuep:CAMBIAR@localhost:5432/cuep
JWT_SECRET=<hex 64>
WORKER_API_KEY=<hex 32>
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=cuep-files
R2_PUBLIC_BASE=https://files.example.com
CORS_ORIGINS=https://app.example.com
SOLVER_TIMEOUT=300
```

Servicio systemd `/etc/systemd/system/cuep-api.service`:
```
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
`sudo systemctl enable --now cuep-api`.

## 3. Frontend (build estático)

```bash
cd /opt/cuep/frontend
npm ci
cp .env.example .env
# VITE_API_URL=https://api.example.com/api/v1
npm run build
sudo mkdir -p /var/www/cuep
sudo cp -r dist/* /var/www/cuep/
```

## 4. Nginx + SSL

`/etc/nginx/sites-available/cuep`:
```
server {
  listen 80;
  server_name app.example.com api.example.com;
  return 301 https://$host$request_uri;
}
server {
  listen 443 ssl http2;
  server_name app.example.com;
  root /var/www/cuep;
  index index.html;
  location / { try_files $uri /index.html; }
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
  ssl_certificate ...;
  ssl_certificate_key ...;
}
```
Certificados: `sudo certbot --nginx -d app.example.com -d api.example.com`.

## 5. Worker local (PC coordinador)

```bash
cd worker
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# API_BASE_URL=https://api.example.com/api/v1
# WORKER_API_KEY=...
python worker.py
```

Ejecutar como servicio o en terminal; para pruebas basta `python worker.py`.

## 6. Equipo local (pruebas)

- Usar SQLite opcional o PostgreSQL local.
- `uvicorn app.main:app --reload` en backend.
- `npm run dev` en frontend (proxy a API).
- Worker apuntando a `http://localhost:8000/api/v1`.
- R2 puede sustituirse por almacenamiento local en dev (`STORAGE_BACKEND=local`, carpeta `./uploads`).

## 7. Backups

- Cron diario: `pg_dump -U cuep cuep | gzip > /backups/cuep_$(date +%F).sql.gz`.
- Retención 14 días: `find /backups -name '*.sql.gz' -mtime +14 -delete`.
- Archivos R2: versionado del bucket habilitado.

## 8. Actualización

```bash
cd /opt/cuep && git pull
cd backend && source .venv/bin/activate && pip install -r requirements.txt && alembic upgrade head
cd ../frontend && npm ci && npm run build && sudo cp -r dist/* /var/www/cuep/
sudo systemctl restart cuep-api
```