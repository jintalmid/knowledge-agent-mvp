#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
ENV_FILE="$BACKEND_DIR/.env"
MESSAGE="Reply only: ok"
TIMEOUT_OVERRIDE=""

usage() {
  cat <<USAGE
Test LLM configuration from backend/.env.

Usage:
  bash scripts/test_llm_env.sh
  bash scripts/test_llm_env.sh --message "Reply only: ok"
  bash scripts/test_llm_env.sh --timeout 300
  bash scripts/test_llm_env.sh --env /path/to/.env

Options:
  --env FILE       Env file to read. Default: backend/.env
  --message TEXT   Test message. Default: Reply only: ok
  --timeout SEC    Override LLM_TIMEOUT_SECONDS for this test.
  -h, --help       Show this help.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --env)
      shift
      [ "$#" -gt 0 ] || { echo "ERROR: --env requires a value" >&2; exit 1; }
      ENV_FILE="$1"
      ;;
    --env=*)
      ENV_FILE="${1#*=}"
      ;;
    --message)
      shift
      [ "$#" -gt 0 ] || { echo "ERROR: --message requires a value" >&2; exit 1; }
      MESSAGE="$1"
      ;;
    --message=*)
      MESSAGE="${1#*=}"
      ;;
    --timeout)
      shift
      [ "$#" -gt 0 ] || { echo "ERROR: --timeout requires a value" >&2; exit 1; }
      TIMEOUT_OVERRIDE="$1"
      ;;
    --timeout=*)
      TIMEOUT_OVERRIDE="${1#*=}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: env file not found: $ENV_FILE" >&2
  echo "Create it from backend/.env.example or rerun scripts/install_ubuntu.sh." >&2
  exit 1
fi

if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "${PYTHON_BIN:-}" ]; then
  echo "ERROR: python3 not found, and backend/.venv/bin/python is missing." >&2
  exit 1
fi

"$PYTHON_BIN" - "$ENV_FILE" "$MESSAGE" "$TIMEOUT_OVERRIDE" <<'PY'
import json
import os
import sys
import time
from pathlib import Path

try:
    import httpx
except ModuleNotFoundError:
    print("ERROR: Python package 'httpx' is not installed.", file=sys.stderr)
    print("Run: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
            value = value[1:-1]
        values[key] = value
    return values


env_file = Path(sys.argv[1]).expanduser().resolve()
message = sys.argv[2]
timeout_override = sys.argv[3]

file_values = parse_env(env_file)

# Match pydantic-settings behavior closely enough for this test:
# real process environment variables override .env values.
config = {**file_values, **{key: value for key, value in os.environ.items() if key.startswith("LLM_")}}

provider = (config.get("LLM_PROVIDER_TYPE") or "").replace("-", "_")
base_url = (config.get("LLM_BASE_URL") or "").strip()
api_key = (config.get("LLM_API_KEY") or "").strip()
model = (config.get("LLM_MODEL") or "").strip()
timeout_raw = timeout_override or config.get("LLM_TIMEOUT_SECONDS") or "180"

print("LLM env test")
print(f"env_file: {env_file}")
print(f"provider: {provider or '<missing>'}")
print(f"base_url: {base_url or '<missing>'}")
print(f"api_key: {'<set, hidden>' if api_key else '<missing>'}")
print(f"model: {model or '<missing>'}")
print(f"timeout_seconds: {timeout_raw}")

missing = []
if provider != "openai_compatible":
    missing.append("LLM_PROVIDER_TYPE must be openai_compatible")
if not base_url:
    missing.append("LLM_BASE_URL is missing")
if not api_key:
    missing.append("LLM_API_KEY is missing")
if not model:
    missing.append("LLM_MODEL is missing")

if missing:
    print("\nConfiguration is incomplete:")
    for item in missing:
        print(f"- {item}")
    sys.exit(2)

try:
    timeout = float(timeout_raw)
except ValueError:
    print(f"ERROR: invalid timeout value: {timeout_raw}", file=sys.stderr)
    sys.exit(2)

url = base_url.rstrip("/")
if not url.endswith("/chat/completions"):
    url = f"{url}/chat/completions"

payload = {
    "model": model,
    "messages": [{"role": "user", "content": message}],
    "temperature": 0.2,
}

print(f"\nrequest_url: {url}")
print("sending test request...")

started_at = time.time()
try:
    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    latency = time.time() - started_at
except Exception as exc:
    latency = time.time() - started_at
    print(f"\nstatus: failed")
    print(f"latency_seconds: {latency:.2f}")
    print(f"error: {exc}")
    sys.exit(3)

print(f"\nstatus_code: {response.status_code}")
print(f"latency_seconds: {latency:.2f}")

try:
    body = response.json()
    print("response_json_preview:")
    print(json.dumps(body, ensure_ascii=False, indent=2)[:2000])
except Exception:
    print("response_text_preview:")
    print(response.text[:2000])

if response.status_code >= 400:
    sys.exit(4)

try:
    content = response.json()["choices"][0]["message"]["content"]
except Exception:
    content = ""

print("\nassistant_message_preview:")
print((content or "<empty>")[:1000])
PY
