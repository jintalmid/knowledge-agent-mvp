#!/usr/bin/env bash

set -euo pipefail

REPO_URL_DEFAULT="https://github.com/jintalmid/knowledge-agent-mvp.git"
PROJECT_NAME="knowledge-agent-mvp"
SCRIPT_VERSION="2026-04-28.4"
SCRIPT_UPDATED_AT_UTC="2026-04-28 01:05:00 UTC"
COMMAND="install"
INSTALL_DIR_ARG=""
ASSUME_YES="0"

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
  bash install_ubuntu.sh --uninstall
  bash install_ubuntu.sh --install-dir "\$HOME/knowledge-agent-mvp"

Options:
  --install-dir DIR   Install or uninstall directory. Must be inside \$HOME.
  --uninstall         Remove the installed project directory after confirmation.
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
      --install-dir)
        shift
        [ "$#" -gt 0 ] || die "--install-dir requires a value"
        INSTALL_DIR_ARG="$1"
        ;;
      --install-dir=*)
        INSTALL_DIR_ARG="${1#*=}"
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
  host="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  if [ -z "$host" ]; then
    host="127.0.0.1"
  fi
  printf "%s" "$host"
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
  prompt BACKEND_HOST "Backend bind host for external access" "0.0.0.0"
  prompt BACKEND_PORT "Backend port" "8000"
  prompt FRONTEND_HOST "Frontend bind host for external access" "0.0.0.0"
  prompt FRONTEND_PORT "Frontend port" "3000"
  prompt PUBLIC_HOST "Public host/IP used by the browser" "$default_public_host"
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

LLM settings were written to:
  $INSTALL_DIR/backend/.env

Frontend API settings were written to:
  $INSTALL_DIR/frontend/.env.local

INFO
}

parse_args "$@"

if [ "$COMMAND" = "uninstall" ]; then
  uninstall_project
  exit 0
fi

main "$@"
