#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"

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

python -u /app/handler.py
