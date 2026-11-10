#!/usr/bin/env bash
# Despliegue del CUEP: migraciones, API, frontend y servicios systemd.
#
# Uso:
#   ./scripts/deploy.sh
#   sudo ./scripts/deploy.sh
#
# Requiere que el entorno de Python del backend tenga instaladas las
# dependencias (por ejemplo, con el .venv activado) y que el usuario pueda
# reiniciar los servicios vía systemd.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

log() {
  printf '\n\033[1;31m[CUEP]\033[0m %s\n' "$*"
}

fail() {
  printf '\n\033[1;31m[CUEP] Error:\033[0m %s\n' "$*" >&2
  exit 1
}

run_privileged() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

[[ -d "$BACKEND_DIR" ]] || fail "No se encontró el directorio del backend: $BACKEND_DIR"
[[ -d "$FRONTEND_DIR" ]] || fail "No se encontró el directorio del frontend: $FRONTEND_DIR"

if [[ -f "$BACKEND_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/.venv/bin/activate"
  log "Instalando dependencias del backend"
  python -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

log "Aplicando migraciones de base de datos"
cd "$BACKEND_DIR"
alembic upgrade head

log "Reiniciando API (cuep-api.service)"
run_privileged systemctl restart cuep-api.service

log "Instalando dependencias del frontend"
cd "$FRONTEND_DIR"
npm ci

log "Cargando variables de producción del frontend"
if [[ -f "$FRONTEND_DIR/.env.production.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$FRONTEND_DIR/.env.production.local"
  set +a
elif [[ -f "$FRONTEND_DIR/.env.production" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$FRONTEND_DIR/.env.production"
  set +a
fi

log "Construyendo frontend"
npm run build

log "Reiniciando web (cuep-web.service)"
run_privileged systemctl restart cuep-web.service

log "Despliegue completado"
