#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export PORT="${PORT:-8000}"
export PORT_HEALTH="${PORT_HEALTH:-${PORT}}"

ollama serve &
OLLAMA_PID=$!

cleanup() {
  kill "${OLLAMA_PID}" 2>/dev/null || true
}
trap cleanup EXIT

until curl -fsS "http://${OLLAMA_HOST}/api/tags" >/dev/null; do
  echo "Waiting for Ollama at ${OLLAMA_HOST}..."
  sleep 1
done

if [[ "${PORT_HEALTH}" != "${PORT}" ]]; then
  uvicorn handler:health_app --host 0.0.0.0 --port "${PORT_HEALTH}" &
fi

uvicorn handler:app --host 0.0.0.0 --port "${PORT}"
