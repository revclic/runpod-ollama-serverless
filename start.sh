#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export PORT="${PORT:-8000}"
export PORT_HEALTH="${PORT_HEALTH:-${PORT}}"

echo "Starting Ollama on ${OLLAMA_HOST}..."
ollama serve &
OLLAMA_PID=$!

HEALTH_PID=""

cleanup() {
  kill "${OLLAMA_PID}" 2>/dev/null || true
  if [[ -n "${HEALTH_PID}" ]]; then
    kill "${HEALTH_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [[ "${PORT_HEALTH}" != "${PORT}" ]]; then
  echo "Starting health server on port ${PORT_HEALTH}..."
  python -m uvicorn handler:health_app --host 0.0.0.0 --port "${PORT_HEALTH}" &
  HEALTH_PID=$!
fi

echo "Starting API server on port ${PORT}..."
python -m uvicorn handler:app --host 0.0.0.0 --port "${PORT}"
