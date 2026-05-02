#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-11434}"
export PORT_HEALTH="${PORT_HEALTH:-8000}"
export OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0:${PORT}}"

if [[ "${PORT_HEALTH}" == "${PORT}" ]]; then
  echo "PORT_HEALTH must be different from PORT for direct Ollama mode." >&2
  exit 1
fi

if [[ "${OLLAMA_HOST}" == 0.0.0.0:* ]]; then
  export OLLAMA_HOST="0.0.0.0:${PORT}"
fi

python3 -u /app/health.py &
HEALTH_PID=$!

cleanup() {
  kill "${HEALTH_PID}" 2>/dev/null || true
}
trap cleanup EXIT

echo "Starting Ollama on ${OLLAMA_HOST}..."
exec ollama serve
