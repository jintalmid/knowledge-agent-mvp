#!/usr/bin/env bash

set -euo pipefail

REPO_URL_DEFAULT="https://github.com/jintalmid/knowledge-agent-mvp.git"
PROJECT_NAME="knowledge-agent-mvp"
SCRIPT_VERSION="2026-04-28.7"
SCRIPT_UPDATED_AT_UTC="2026-04-28 04:24:00 UTC"
COMMAND="install"
INSTALL_DIR_ARG=""
ASSUME_YES="0"
BACKEND_HOST_ARG=""
BACKEND_PORT_ARG=""
FRONTEND_HOST_ARG=""
FRONTEND_PORT_ARG=""
PUBLIC_HOST_ARG=""

say() {
  printf "\n==> %s\n" "$1"
}

script_updated_at_local() {
  if date -d "$SCRIPT_UPDATED_AT_UTC" "+%Y-%m-%d %H:%M:%S %Z (%z)" >/dev/null 2>&1; then
    date -d "$SCRIPT_UPDATED_AT_UTC" "+%Y-%m-%d %H:%M:%S %Z (%z)"
  else
    local updated_epoch
    updated_epoch="$(date -j -u -f "%Y-%m-%d %H:%M:%S" "${SCRIPT_UPDATED_AT_UTC% UTC}" "+%s" 2>/dev/null || true)"
    if [ -n "$updated_epoch" ]; then
      date -r "$updated_epoch" "+%Y-%m-%d %H:%M:%S %Z (%z)"
    else
      printf "%s" "$SCRIPT_UPDATED_AT_UTC"
    fi
  fi
}

print_script_banner() {
  printf "\n%s Ubuntu installer\n" "$PROJECT_NAME"
  printf "Script version: %s\n" "$SCRIPT_VERSION"
  printf "Script updated local: %s\n" "$(script_updated_at_local)"
  printf "Script updated UTC: %s\n" "$SCRIPT_UPDATED_AT_UTC"
}

die() {
  printf "\nERROR: %s\n" "$1" >&2
  exit 1
}

usage() {
  print_script_banner
  cat <<USAGE
Usage:
  bash install_ubuntu.sh
  bash install_ubuntu.sh --update
  bash install_ubuntu.sh --start
  bash install_ubuntu.sh --status
  bash install_ubuntu.sh --stop
  bash install_ubuntu.sh --uninstall
  bash install_ubuntu.sh --install-dir "\$HOME/knowledge-agent-mvp"

Options:
  --install-dir DIR   Install or uninstall directory. Must be inside \$HOME.
  --update            Pull latest code, update dependencies, migrate DB, rebuild frontend.
  --start             Start backend and frontend in the background.
  --status            Show backend and frontend process status.
  --stop              Stop backend and frontend processes started by this script.
  --uninstall         Remove the installed project directory after confirmation.
  --backend-host HOST Override backend bind host for install/start.
  --backend-port PORT Override backend port for install/start.
  --frontend-host HOST Override frontend bind host for install/start.
  --frontend-port PORT Override frontend port for install/start.
  --public-host HOST  Override public host used in printed URLs.
  -y, --yes           Skip uninstall confirmation. Still restricted to \$HOME.
  -h, --help          Show this help.
USAGE
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --uninstall|uninstall)
        COMMAND="uninstall"
        ;;
      --update|update)
        COMMAND="update"
        ;;
      --start|start)
        COMMAND="start"
        ;;
      --status|status)
        COMMAND="status"
        ;;
      --stop|stop)
        COMMAND="stop"
        ;;
      --install-dir)
        shift
        [ "$#" -gt 0 ] || die "--install-dir requires a value"
        INSTALL_DIR_ARG="$1"
        ;;
      --install-dir=*)
        INSTALL_DIR_ARG="${1#*=}"
        ;;
      --backend-host)
        shift
        [ "$#" -gt 0 ] || die "--backend-host requires a value"
        BACKEND_HOST_ARG="$1"
        ;;
      --backend-host=*)
        BACKEND_HOST_ARG="${1#*=}"
        ;;
      --backend-port)
        shift
        [ "$#" -gt 0 ] || die "--backend-port requires a value"
        BACKEND_PORT_ARG="$1"
        ;;
      --backend-port=*)
        BACKEND_PORT_ARG="${1#*=}"
        ;;
      --frontend-host)
        shift
        [ "$#" -gt 0 ] || die "--frontend-host requires a value"
        FRONTEND_HOST_ARG="$1"
        ;;
      --frontend-host=*)
        FRONTEND_HOST_ARG="${1#*=}"
        ;;
      --frontend-port)
        shift
        [ "$#" -gt 0 ] || die "--frontend-port requires a value"
        FRONTEND_PORT_ARG="$1"
        ;;
      --frontend-port=*)
        FRONTEND_PORT_ARG="${1#*=}"
        ;;
      --public-host)
        shift
        [ "$#" -gt 0 ] || die "--public-host requires a value"
        PUBLIC_HOST_ARG="$1"
        ;;
      --public-host=*)
        PUBLIC_HOST_ARG="${1#*=}"
        ;;
      -y|--yes)
        ASSUME_YES="1"
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown option: $1"
        ;;
    esac
    shift
  done
}

prompt() {
  local var_name="$1"
  local label="$2"
  local default_value="${3:-}"
  local value

  if [ -n "$default_value" ]; then
    if [ -r /dev/tty ]; then
      read -r -p "$label [$default_value]: " value < /dev/tty
    else
      read -r -p "$label [$default_value]: " value
    fi
    value="${value:-$default_value}"
  else
    if [ -r /dev/tty ]; then
      read -r -p "$label: " value < /dev/tty
    else
      read -r -p "$label: " value
    fi
  fi

  printf -v "$var_name" "%s" "$value"
}

prompt_secret() {
  local var_name="$1"
  local label="$2"
  local value

  if [ -r /dev/tty ]; then
    read -r -s -p "$label: " value < /dev/tty
  else
    read -r -s -p "$label: " value
  fi
  printf "\n"
  printf -v "$var_name" "%s" "$value"
}

detect_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  if [ -f "$script_dir/../module-registry.json" ] && [ -d "$script_dir/../backend" ] && [ -d "$script_dir/../frontend" ]; then
    (cd "$script_dir/.." && pwd)
  else
    printf "%s/%s" "$HOME" "$PROJECT_NAME"
  fi
}

detect_public_host() {
  local host
  if is_wsl; then
    printf "localhost"
    return
  fi
  host="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  if [ -z "$host" ]; then
    host="127.0.0.1"
  fi
  printf "%s" "$host"
}

is_wsl() {
  if [ -n "${WSL_DISTRO_NAME:-}" ]; then
    return 0
  fi
  if grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
    return 0
  fi
  return 1
}

absolute_path() {
  local input="$1"
  local parent
  local base

  case "$input" in
    "~")
      input="$HOME"
      ;;
    "~/"*)
      input="$HOME/${input#~/}"
      ;;
  esac

  if [ -d "$input" ]; then
    (cd "$input" && pwd -P)
    return
  fi

  parent="$(dirname "$input")"
  base="$(basename "$input")"

  if [ -d "$parent" ]; then
    printf "%s/%s" "$(cd "$parent" && pwd -P)" "$base"
    return
  fi

  case "$input" in
    /*)
      printf "%s" "$input"
      ;;
    *)
      printf "%s/%s" "$(pwd -P)" "$input"
      ;;
  esac
}

require_home_subdir() {
  local path="$1"
  local home_abs

  home_abs="$(cd "$HOME" && pwd -P)"

  case "$path" in
    "$home_abs"/*)
      ;;
    *)
      die "Install directory must be inside your home directory: $home_abs"
      ;;
  esac

  if [ "$path" = "$home_abs" ]; then
    die "Install directory cannot be your home directory itself."
  fi
}

ensure_ubuntu() {
  if ! command -v apt-get >/dev/null 2>&1; then
    die "This installer expects Ubuntu/Debian with apt-get."
  fi
}

ensure_node_20() {
  local node_major
  node_major="$(node -v 2>/dev/null | sed 's/^v//' | cut -d. -f1 || true)"

  if [ -n "$node_major" ] && [ "$node_major" -ge 20 ] 2>/dev/null; then
    say "Node.js $(node -v) detected"
    return
  fi

  say "Installing Node.js 20"
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
}

write_backend_env() {
  local env_file="$1"

  cat > "$env_file" <<ENV
LLM_PROVIDER_TYPE=$LLM_PROVIDER_TYPE
LLM_BASE_URL=$LLM_BASE_URL
LLM_API_KEY=$LLM_API_KEY
LLM_MODEL=$LLM_MODEL
LLM_TIMEOUT_SECONDS=$LLM_TIMEOUT_SECONDS
ENV

  chmod 600 "$env_file"
}

write_frontend_env() {
  local env_file="$1"
  local api_base_url="$2"

  cat > "$env_file" <<ENV
NEXT_PUBLIC_API_BASE_URL=$api_base_url
ENV
}

write_shell_var() {
  local var_name="$1"
  local value="$2"
  printf "%s=%q\n" "$var_name" "$value"
}

runtime_dir() {
  printf "%s/.runtime" "$INSTALL_DIR"
}

runtime_env_file() {
  printf "%s/app.env" "$(runtime_dir)"
}

backend_pid_file() {
  printf "%s/backend.pid" "$(runtime_dir)"
}

frontend_pid_file() {
  printf "%s/frontend.pid" "$(runtime_dir)"
}

backend_log_file() {
  printf "%s/backend.log" "$(runtime_dir)"
}

frontend_log_file() {
  printf "%s/frontend.log" "$(runtime_dir)"
}

write_runtime_env() {
  local runtime_env
  mkdir -p "$(runtime_dir)"
  runtime_env="$(runtime_env_file)"
  {
    write_shell_var INSTALL_DIR "$INSTALL_DIR"
    write_shell_var BACKEND_HOST "$BACKEND_HOST"
    write_shell_var BACKEND_PORT "$BACKEND_PORT"
    write_shell_var FRONTEND_HOST "$FRONTEND_HOST"
    write_shell_var FRONTEND_PORT "$FRONTEND_PORT"
    write_shell_var PUBLIC_HOST "$PUBLIC_HOST"
  } > "$runtime_env"
}

resolve_install_dir_for_runtime() {
  local default_install_dir
  default_install_dir="$(detect_repo_root)"

  if [ -n "$INSTALL_DIR_ARG" ]; then
    INSTALL_DIR="$INSTALL_DIR_ARG"
  else
    INSTALL_DIR="$default_install_dir"
  fi

  INSTALL_DIR="$(absolute_path "$INSTALL_DIR")"
  require_home_subdir "$INSTALL_DIR"
}

load_runtime_env() {
  resolve_install_dir_for_runtime
  BACKEND_HOST="0.0.0.0"
  BACKEND_PORT="8000"
  FRONTEND_HOST="0.0.0.0"
  FRONTEND_PORT="3000"
  PUBLIC_HOST="$(detect_public_host)"

  if [ -f "$(runtime_env_file)" ]; then
    # shellcheck disable=SC1090
    . "$(runtime_env_file)"
  fi

  BACKEND_HOST="${BACKEND_HOST_ARG:-$BACKEND_HOST}"
  BACKEND_PORT="${BACKEND_PORT_ARG:-$BACKEND_PORT}"
  FRONTEND_HOST="${FRONTEND_HOST_ARG:-$FRONTEND_HOST}"
  FRONTEND_PORT="${FRONTEND_PORT_ARG:-$FRONTEND_PORT}"
  PUBLIC_HOST="${PUBLIC_HOST_ARG:-$PUBLIC_HOST}"
}

is_pid_running() {
  local pid_file="$1"
  local pid

  if [ ! -f "$pid_file" ]; then
    return 1
  fi

  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [ -z "$pid" ]; then
    return 1
  fi

  kill -0 "$pid" >/dev/null 2>&1
}

print_one_service_status() {
  local service_name="$1"
  local pid_file="$2"
  local log_file="$3"
  local url="$4"
  local pid

  if is_pid_running "$pid_file"; then
    pid="$(cat "$pid_file")"
    printf "%s: running, pid=%s, url=%s, log=%s\n" "$service_name" "$pid" "$url" "$log_file"
  else
    printf "%s: stopped, url=%s, log=%s\n" "$service_name" "$url" "$log_file"
  fi
}

status_services() {
  print_script_banner
  printf "Mode: status\n"
  load_runtime_env

  if [ ! -d "$INSTALL_DIR" ]; then
    die "Install directory not found: $INSTALL_DIR"
  fi

  print_one_service_status "backend" "$(backend_pid_file)" "$(backend_log_file)" "http://$PUBLIC_HOST:$BACKEND_PORT/api/health"
  print_one_service_status "frontend" "$(frontend_pid_file)" "$(frontend_log_file)" "http://$PUBLIC_HOST:$FRONTEND_PORT"
}

start_one_service() {
  local service_name="$1"
  local pid_file="$2"
  local log_file="$3"
  shift 3

  mkdir -p "$(runtime_dir)"

  if is_pid_running "$pid_file"; then
    printf "%s already running, pid=%s\n" "$service_name" "$(cat "$pid_file")"
    return
  fi

  say "Starting $service_name"
  nohup "$@" > "$log_file" 2>&1 &
  printf "%s" "$!" > "$pid_file"
}

start_services() {
  print_script_banner
  printf "Mode: start\n"
  load_runtime_env

  [ -d "$INSTALL_DIR/backend" ] || die "Backend directory not found in $INSTALL_DIR"
  [ -d "$INSTALL_DIR/frontend" ] || die "Frontend directory not found in $INSTALL_DIR"
  [ -x "$INSTALL_DIR/backend/.venv/bin/uvicorn" ] || die "Backend venv not found. Run install first."
  [ -x "$INSTALL_DIR/frontend/node_modules/.bin/next" ] || die "Frontend dependencies not found. Run install first."
  [ -d "$INSTALL_DIR/frontend/.next" ] || die "Frontend build not found. Run install first."

  write_runtime_env

  (
    cd "$INSTALL_DIR/backend"
    start_one_service "backend" "$(backend_pid_file)" "$(backend_log_file)" \
      "$INSTALL_DIR/backend/.venv/bin/uvicorn" app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
  )

  (
    cd "$INSTALL_DIR/frontend"
    start_one_service "frontend" "$(frontend_pid_file)" "$(frontend_log_file)" \
      "$INSTALL_DIR/frontend/node_modules/.bin/next" start --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
  )

  sleep 1
  printf "\n"
  print_one_service_status "backend" "$(backend_pid_file)" "$(backend_log_file)" "http://$PUBLIC_HOST:$BACKEND_PORT/api/health"
  print_one_service_status "frontend" "$(frontend_pid_file)" "$(frontend_log_file)" "http://$PUBLIC_HOST:$FRONTEND_PORT"
}

stop_one_service() {
  local service_name="$1"
  local pid_file="$2"
  local pid
  local waited

  if ! is_pid_running "$pid_file"; then
    printf "%s already stopped\n" "$service_name"
    rm -f "$pid_file"
    return
  fi

  pid="$(cat "$pid_file")"
  say "Stopping $service_name pid=$pid"
  kill "$pid"

  waited=0
  while kill -0 "$pid" >/dev/null 2>&1 && [ "$waited" -lt 10 ]; do
    sleep 1
    waited=$((waited + 1))
  done

  if kill -0 "$pid" >/dev/null 2>&1; then
    printf "%s did not exit within 10s; pid=%s\n" "$service_name" "$pid"
  else
    rm -f "$pid_file"
    printf "%s stopped\n" "$service_name"
  fi
}

stop_services() {
  print_script_banner
  printf "Mode: stop\n"
  load_runtime_env

  if [ ! -d "$INSTALL_DIR" ]; then
    die "Install directory not found: $INSTALL_DIR"
  fi

  stop_one_service "frontend" "$(frontend_pid_file)"
  stop_one_service "backend" "$(backend_pid_file)"
}

update_project() {
  local backend_was_running
  local frontend_was_running

  print_script_banner
  printf "Mode: update\n"
  load_runtime_env

  [ -d "$INSTALL_DIR/.git" ] || die "Git repository not found in $INSTALL_DIR. Run install first."
  [ -d "$INSTALL_DIR/backend" ] || die "Backend directory not found in $INSTALL_DIR"
  [ -d "$INSTALL_DIR/frontend" ] || die "Frontend directory not found in $INSTALL_DIR"

  backend_was_running=0
  frontend_was_running=0

  if is_pid_running "$(backend_pid_file)"; then
    backend_was_running=1
  fi
  if is_pid_running "$(frontend_pid_file)"; then
    frontend_was_running=1
  fi

  if [ "$frontend_was_running" = "1" ]; then
    stop_one_service "frontend" "$(frontend_pid_file)"
  fi
  if [ "$backend_was_running" = "1" ]; then
    stop_one_service "backend" "$(backend_pid_file)"
  fi

  say "Pulling latest code"
  git -C "$INSTALL_DIR" pull --ff-only

  say "Updating backend"
  cd "$INSTALL_DIR/backend"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
  mkdir -p "$INSTALL_DIR/backend/uploads"
  .venv/bin/python -c "from app.db.sqlite import init_db; init_db(); print('SQLite database initialized')"

  say "Updating frontend"
  cd "$INSTALL_DIR/frontend"
  npm install
  write_frontend_env "$INSTALL_DIR/frontend/.env.local" "http://$PUBLIC_HOST:$BACKEND_PORT"
  write_runtime_env
  if [ -z "${NODE_OPTIONS:-}" ]; then
    export NODE_OPTIONS="--max-old-space-size=2048"
  else
    export NODE_OPTIONS="$NODE_OPTIONS --max-old-space-size=2048"
  fi
  npm exec next -- build --webpack

  if [ "$backend_was_running" = "1" ] || [ "$frontend_was_running" = "1" ]; then
    say "Restarting services that were running before update"
    start_services
  else
    say "Update complete. Services were not running before update."
    printf "Start services with:\n  bash \"%s/scripts/install_ubuntu.sh\" --start\n" "$INSTALL_DIR"
  fi
}

uninstall_project() {
  local default_install_dir
  default_install_dir="$(detect_repo_root)"

  print_script_banner
  printf "Mode: uninstall\n"

  if [ -n "$INSTALL_DIR_ARG" ]; then
    INSTALL_DIR="$INSTALL_DIR_ARG"
  else
    prompt INSTALL_DIR "Install directory to remove" "$default_install_dir"
  fi

  INSTALL_DIR="$(absolute_path "$INSTALL_DIR")"
  require_home_subdir "$INSTALL_DIR"

  if [ ! -e "$INSTALL_DIR" ]; then
    say "Nothing to remove: $INSTALL_DIR does not exist"
    exit 0
  fi

  if [ "$ASSUME_YES" != "1" ]; then
    local confirm
    printf "\nThis will permanently delete:\n  %s\n" "$INSTALL_DIR"
    prompt confirm "Type DELETE to confirm"
    if [ "$confirm" != "DELETE" ]; then
      say "Uninstall cancelled"
      exit 0
    fi
  fi

  say "Removing $INSTALL_DIR"
  rm -rf -- "$INSTALL_DIR"
  say "Uninstall complete"
}

main() {
  ensure_ubuntu

  local default_install_dir
  local default_public_host
  default_install_dir="$(detect_repo_root)"
  default_public_host="$(detect_public_host)"

  print_script_banner
  printf "Mode: install\n"
  printf "This script installs system dependencies, configures env files, and builds the frontend.\n"

  prompt REPO_URL "GitHub repository URL" "$REPO_URL_DEFAULT"
  if [ -n "$INSTALL_DIR_ARG" ]; then
    INSTALL_DIR="$INSTALL_DIR_ARG"
  else
    prompt INSTALL_DIR "Install directory" "$default_install_dir"
  fi
  INSTALL_DIR="$(absolute_path "$INSTALL_DIR")"
  require_home_subdir "$INSTALL_DIR"
  if [ -n "$BACKEND_HOST_ARG" ]; then BACKEND_HOST="$BACKEND_HOST_ARG"; else prompt BACKEND_HOST "Backend bind host for external access" "0.0.0.0"; fi
  if [ -n "$BACKEND_PORT_ARG" ]; then BACKEND_PORT="$BACKEND_PORT_ARG"; else prompt BACKEND_PORT "Backend port" "8000"; fi
  if [ -n "$FRONTEND_HOST_ARG" ]; then FRONTEND_HOST="$FRONTEND_HOST_ARG"; else prompt FRONTEND_HOST "Frontend bind host for external access" "0.0.0.0"; fi
  if [ -n "$FRONTEND_PORT_ARG" ]; then FRONTEND_PORT="$FRONTEND_PORT_ARG"; else prompt FRONTEND_PORT "Frontend port" "3000"; fi
  if [ -n "$PUBLIC_HOST_ARG" ]; then PUBLIC_HOST="$PUBLIC_HOST_ARG"; else prompt PUBLIC_HOST "Public host/IP used by the browser" "$default_public_host"; fi
  prompt LLM_PROVIDER_TYPE "LLM provider type" "openai_compatible"
  prompt LLM_BASE_URL "LLM base URL, for example https://api.openai.com/v1"
  prompt LLM_MODEL "Default LLM model" "gpt-4-turbo"
  prompt LLM_TIMEOUT_SECONDS "LLM timeout seconds" "180"
  prompt_secret LLM_API_KEY "LLM API key, input hidden; leave empty only for later manual setup"
  prompt OPEN_UFW "Open frontend/backend ports with ufw if available? y/N" "N"

  say "Installing system packages"
  sudo apt-get update
  sudo apt-get install -y git curl python3 python3-venv python3-pip build-essential
  ensure_node_20

  if [ -d "$INSTALL_DIR/.git" ]; then
    say "Using existing repository at $INSTALL_DIR"
  elif [ -e "$INSTALL_DIR" ] && [ "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
    die "Install directory exists and is not empty: $INSTALL_DIR"
  else
    say "Cloning repository"
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi

  [ -d "$INSTALL_DIR/backend" ] || die "Backend directory not found in $INSTALL_DIR"
  [ -d "$INSTALL_DIR/frontend" ] || die "Frontend directory not found in $INSTALL_DIR"

  say "Setting up backend"
  cd "$INSTALL_DIR/backend"
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
  write_backend_env "$INSTALL_DIR/backend/.env"
  mkdir -p "$INSTALL_DIR/backend/uploads"
  .venv/bin/python -c "from app.db.sqlite import init_db; init_db(); print('SQLite database initialized')"

  say "Setting up frontend"
  cd "$INSTALL_DIR/frontend"
  npm install
  write_frontend_env "$INSTALL_DIR/frontend/.env.local" "http://$PUBLIC_HOST:$BACKEND_PORT"
  write_runtime_env
  if [ -z "${NODE_OPTIONS:-}" ]; then
    export NODE_OPTIONS="--max-old-space-size=2048"
  else
    export NODE_OPTIONS="$NODE_OPTIONS --max-old-space-size=2048"
  fi
  npm exec next -- build --webpack

  if [[ "$OPEN_UFW" =~ ^[Yy]$ ]]; then
    if command -v ufw >/dev/null 2>&1; then
      say "Opening ports with ufw"
      sudo ufw allow "$BACKEND_PORT/tcp"
      sudo ufw allow "$FRONTEND_PORT/tcp"
    else
      say "ufw is not installed; skipping firewall changes"
    fi
  fi

  say "Installation complete"
  cat <<INFO

Frontend URL:
  http://$PUBLIC_HOST:$FRONTEND_PORT

Backend health:
  http://$PUBLIC_HOST:$BACKEND_PORT/api/health

Start backend:
  cd "$INSTALL_DIR/backend"
  source .venv/bin/activate
  uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"

Start frontend in production mode:
  cd "$INSTALL_DIR/frontend"
  npm run start -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"

Start frontend in development mode:
  cd "$INSTALL_DIR/frontend"
  npm run dev -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"

One-line service commands:
  bash "$INSTALL_DIR/scripts/install_ubuntu.sh" --start
  bash "$INSTALL_DIR/scripts/install_ubuntu.sh" --status
  bash "$INSTALL_DIR/scripts/install_ubuntu.sh" --stop

LLM settings were written to:
  $INSTALL_DIR/backend/.env

Frontend API settings were written to:
  $INSTALL_DIR/frontend/.env.local

INFO
}

parse_args "$@"

case "$COMMAND" in
  install)
    main "$@"
    ;;
  update)
    update_project
    ;;
  start)
    start_services
    ;;
  status)
    status_services
    ;;
  stop)
    stop_services
    ;;
  uninstall)
    uninstall_project
    ;;
  *)
    die "Unknown command: $COMMAND"
    ;;
esac
