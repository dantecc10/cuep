#!/usr/bin/env bash
# Despliegue del CUEP: migraciones, API, frontend, servicios y reporte de estado.
#
# Uso:
#   ./scripts/deploy.sh
#   sudo ./scripts/deploy.sh
#
# Opciones:
#   --skip-frontend   No reinstala ni reconstruye el frontend.
#   --skip-report     No muestra el reporte final de módulos.
#   --strict          Devuelve error si el reporte encuentra fallos (no se
#                     recomienda la primera vez: el despliegue se completa igual).
#
# Al final imprime el estado de cada módulo (variables, base de datos, R2,
# configuración del ciclo) con colores: verde = correcto, amarillo = aviso,
# rojo = falta configuración.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

API_SERVICE="${API_SERVICE:-cuep-api.service}"
WEB_SERVICE="${WEB_SERVICE:-cuep-web.service}"
WORKER_SERVICE="${WORKER_SERVICE:-cuep-worker.service}"
AVISOS_TIMER="${AVISOS_TIMER:-cuep-notificaciones.timer}"

SKIP_FRONTEND=0
SKIP_REPORT=0
STRICT=0

for arg in "$@"; do
  case "$arg" in
    --skip-frontend) SKIP_FRONTEND=1 ;;
    --skip-report) SKIP_REPORT=1 ;;
    --strict) STRICT=1 ;;
    -h|--help)
      awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *)
      printf 'Opción desconocida: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_RED=$'\033[31m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[34m'
  C_CYAN=$'\033[36m'
  C_GREY=$'\033[90m'
else
  C_RESET=""
  C_BOLD=""
  C_RED=""
  C_GREEN=""
  C_YELLOW=""
  C_BLUE=""
  C_CYAN=""
  C_GREY=""
fi

step() { printf '\n%s▸ %s%s\n' "$C_BLUE$C_BOLD" "$*" "$C_RESET"; }
sub()  { printf '  %s·%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
ok()   { printf '  %s✔%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '  %s⚠%s %s\n' "$C_YELLOW" "$C_RESET" "$*"; }
err()  { printf '  %s✖%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; }

log() {
  printf '\n%s[CUEP]%s %s\n' "$C_BOLD$C_RED" "$C_RESET" "$*"
}

fail() {
  printf '\n%s[CUEP] Error:%s %s\n' "$C_BOLD$C_RED" "$C_RESET" "$*" >&2
  exit 1
}

run_privileged() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

# ¿Se pueden reiniciar servicios? (root, o sudo sin contraseña)
can_privileged() {
  if [[ "${EUID}" -eq 0 ]]; then
    return 0
  fi
  command -v sudo >/dev/null 2>&1 || return 1
  sudo -n true >/dev/null 2>&1
}

HAVE_SYSTEMD=0
if command -v systemctl >/dev/null 2>&1; then
  HAVE_SYSTEMD=1
fi

service_active() {
  [[ "$HAVE_SYSTEMD" -eq 1 ]] || return 1
  systemctl is-active --quiet "$1" 2>/dev/null
}

service_exists() {
  [[ "$HAVE_SYSTEMD" -eq 1 ]] || return 1
  systemctl list-unit-files --no-legend 2>/dev/null | awk '{print $1}' | grep -qx "$1"
}

# Puerto de la API: se deduce del propio servicio systemd si está definido.
api_port() {
  local puerto
  [[ "$HAVE_SYSTEMD" -eq 1 ]] || { printf '8000'; return 0; }
  puerto="$(systemctl cat "$API_SERVICE" 2>/dev/null | grep -oE '\-\-port[= ]+[0-9]+' | grep -oE '[0-9]+' | head -n1 || true)"
  if [[ -z "$puerto" ]]; then
    puerto="$(systemctl show "$API_SERVICE" --property=ExecStart --value 2>/dev/null | grep -oE '\-\-port[= ]+[0-9]+' | grep -oE '[0-9]+' | head -n1 || true)"
  fi
  printf '%s' "${puerto:-8000}"
}

printf '%s\n' "${C_BOLD}▁▁▁ Despliegue del CUEP ▁▁▁${C_RESET}"
sub "$(date '+%Y-%m-%d %H:%M:%S') · $(hostname) · $(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo 'sin git')"

[[ -d "$BACKEND_DIR" ]] || fail "No se encontró el directorio del backend: $BACKEND_DIR"
[[ -d "$FRONTEND_DIR" ]] || fail "No se encontró el directorio del frontend: $FRONTEND_DIR"

# ---------------------------------------------------------------------------
step "Comprobando el entorno"
# ---------------------------------------------------------------------------
PYTHON_BIN=""
if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
  ok "Entorno virtual del backend: $($PYTHON_BIN --version 2>&1)"
else
  warn "No hay .venv en backend/: se usará el Python del sistema."
  PYTHON_BIN="$(command -v python3 || true)"
  [[ -n "$PYTHON_BIN" ]] || fail "No se encontró python3 en el sistema."
fi

if command -v node >/dev/null 2>&1; then
  ok "Node $(node --version) · npm $(npm --version 2>/dev/null || echo '?')"
else
  warn "Node no está instalado: el frontend no se puede construir."
fi

if [[ -f "$BACKEND_DIR/.env" ]]; then
  ok "backend/.env presente"
else
  warn "No existe backend/.env: copia backend/.env.example y ajústalo."
fi

# ---------------------------------------------------------------------------
step "Dependencias del backend"
# ---------------------------------------------------------------------------
if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  if (
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
    "$PYTHON_BIN" -m pip install -r requirements.txt
  ) >/tmp/cuep-pip.log 2>&1; then
    grep -E "^Successfully installed" /tmp/cuep-pip.log | head -n1 | sed 's/^/    /' || true
    ok "Dependencias del backend instaladas"
  else
    tail -n 5 /tmp/cuep-pip.log | sed 's/^/    /'
    warn "Falló la instalación de dependencias: comprueba que ya estén en el .venv."
  fi
else
  warn "Se omite la instalación de dependencias (no hay .venv)."
fi

# ---------------------------------------------------------------------------
step "Migraciones de base de datos"
# ---------------------------------------------------------------------------
cd "$BACKEND_DIR"
if command -v alembic >/dev/null 2>&1 || [[ -x "$BACKEND_DIR/.venv/bin/alembic" ]]; then
  ALEMBIC_BIN="$(command -v alembic || echo "$BACKEND_DIR/.venv/bin/alembic")"
  BEFORE="$("$ALEMBIC_BIN" current 2>/dev/null | tr -d '\n' || true)"
  if MIG_OUTPUT="$("$ALEMBIC_BIN" upgrade head 2>&1)"; then
    AFTER="$("$ALEMBIC_BIN" current 2>/dev/null | tr -d '\n' || true)"
    ok "Esquema actualizado${BEFORE:+ (antes: ${BEFORE})}"
    sub "Revisión actual: ${AFTER:-desconocida}"
    printf '%s\n' "$MIG_OUTPUT" | grep -v '^INFO' | sed 's/^/    /' | head -n 5 || true
    ALEMBIC_HEAD="$(cd "$BACKEND_DIR" && "$ALEMBIC_BIN" heads 2>/dev/null | head -n1 | awk '{print $1}')"
  else
    printf '%s\n' "$MIG_OUTPUT" | tail -n 20 | sed 's/^/    /' >&2
    fail "Fallaron las migraciones. Revisa el error anterior antes de continuar."
  fi
else
  fail "No se encontró alembic; instala las dependencias del backend."
fi

# ---------------------------------------------------------------------------
step "API (${API_SERVICE})"
# ---------------------------------------------------------------------------
if [[ "$HAVE_SYSTEMD" -eq 1 && "$(can_privileged; echo $?)" -eq 0 ]]; then
  run_privileged systemctl restart "$API_SERVICE"
  sleep 1
  if service_active "$API_SERVICE"; then
    ok "Servicio activo"
  else
    err "El servicio no quedó activo. Diagnóstico:"
    systemctl status --no-pager -n 20 "$API_SERVICE" >&2 || true
  fi
elif [[ "$HAVE_SYSTEMD" -eq 1 ]]; then
  warn "Sin privilegios para reiniciar systemd: ejecuta el script con sudo o como root."
else
  warn "systemd no está disponible en este equipo: no se reinician servicios."
fi

PUERTO="$(api_port)"
HEALTH_URL="${CUEP_API_URL:-http://127.0.0.1:${PUERTO}/health}"
if command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 10 "$HEALTH_URL" >/dev/null 2>&1; then
    ok "La API responde en $HEALTH_URL"
  else
    warn "La API no respondió en $HEALTH_URL (puede estar arrancando o haber un error)."
  fi
else
  warn "curl no está disponible: no se pudo comprobar la salud de la API."
fi

# ---------------------------------------------------------------------------
if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  step "Frontend"
  # -------------------------------------------------------------------------
  cd "$FRONTEND_DIR"
  if command -v npm >/dev/null 2>&1; then
    if npm ci >/tmp/cuep-npm.log 2>&1; then
      ok "Dependencias del frontend instaladas"
    else
      tail -n 10 /tmp/cuep-npm.log | sed 's/^/    /'
      fail "Falló la instalación de dependencias del frontend."
    fi

    if [[ -f "$FRONTEND_DIR/.env.production.local" ]]; then
      set -a
      # shellcheck disable=SC1091
      source "$FRONTEND_DIR/.env.production.local"
      set +a
      sub "Variables cargadas desde .env.production.local"
    elif [[ -f "$FRONTEND_DIR/.env.production" ]]; then
      set -a
      # shellcheck disable=SC1091
      source "$FRONTEND_DIR/.env.production"
      set +a
      sub "Variables cargadas desde .env.production"
    else
      warn "No hay .env.production.local ni .env.production: el frontend usará el valor por defecto."
    fi

    if [[ -z "${NEXT_PUBLIC_API_URL:-}" ]]; then
      warn "Falta NEXT_PUBLIC_API_URL: revisa que el frontend apunte a la API correcta."
    else
      ok "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL"
    fi

    if npm run build 2>&1 | tail -n 3; then
      ok "Frontend construido"
    else
      fail "Falló la construcción del frontend."
    fi

    if [[ "$HAVE_SYSTEMD" -eq 1 && "$(can_privileged; echo $?)" -eq 0 ]]; then
      run_privileged systemctl restart "$WEB_SERVICE"
      sleep 1
      if service_active "$WEB_SERVICE"; then
        ok "Web ($WEB_SERVICE) activo"
      else
        err "El servicio web no quedó activo. Diagnóstico:"
        systemctl status --no-pager -n 20 "$WEB_SERVICE" >&2 || true
      fi
    elif [[ "$HAVE_SYSTEMD" -eq 1 ]]; then
      warn "Sin privilegios para reiniciar systemd: el frontend se construyó pero el servicio no se reinició."
    else
      warn "systemd no está disponible: el frontend se construyó pero no se reinició el servicio."
    fi
  else
    warn "npm no disponible: se omite el despliegue del frontend."
  fi
else
  step "Frontend"
  sub "Omitido (--skip-frontend)"
fi

# ---------------------------------------------------------------------------
step "Servicios auxiliares"
# ---------------------------------------------------------------------------
if service_exists "$WORKER_SERVICE"; then
  if service_active "$WORKER_SERVICE"; then
    ok "Worker de cálculo activo"
  else
    warn "El worker no está activo (puede ejecutarse en la computadora del coordinador)."
  fi
else
  sub "El worker de cálculo no está instalado aquí (opcional: corre en el equipo del coordinador)."
fi

if service_exists "$AVISOS_TIMER"; then
  if systemctl is-active --quiet "$AVISOS_TIMER"; then
    ok "Temporizador de avisos activo ($AVISOS_TIMER)"
  else
    warn "El temporizador de avisos no está activo: systemctl enable --now $AVISOS_TIMER"
  fi
else
  warn "No está instalado $AVISOS_TIMER: la cola de avisos se drena a mano."
  sub "Instálalo con: sudo cp infra/cuep-notificaciones.* /etc/systemd/system/ && sudo systemctl enable --now $AVISOS_TIMER"
fi

# ---------------------------------------------------------------------------
if [[ "$SKIP_REPORT" -eq 0 ]]; then
  step "Reporte de estado de los módulos"
  # -------------------------------------------------------------------------
  set +e
  "$PYTHON_BIN" "$ROOT_DIR/scripts/deploy_report.py" --head "${ALEMBIC_HEAD:-}"
  REPORT_STATUS=$?
  set -e
else
  sub "Omitido (--skip-report)"
  REPORT_STATUS=0
fi

# ---------------------------------------------------------------------------
step "Resumen del despliegue"
# ---------------------------------------------------------------------------
if [[ "$REPORT_STATUS" -eq 0 ]]; then
  ok "Despliegue completado sin errores de configuración"
else
  warn "Despliegue completado, pero el reporte encontró puntos sin configurar"
  sub "Revisa el reporte anterior y backend/.env.example para corregirlos"
fi
printf '\n%s[CUEP]%s Listo. Recuerda reiniciar el worker si lo usas en este servidor.\n' "$C_BOLD$C_RED" "$C_RESET"

if [[ "$STRICT" -eq 1 && "$REPORT_STATUS" -ne 0 ]]; then
  exit 1
fi
