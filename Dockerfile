FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MODEL=aya-expanse:8b \
    PORT=11434 \
    PORT_HEALTH=8000 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN OLLAMA_HOST=127.0.0.1:11434 ollama serve > /tmp/ollama-build.log 2>&1 & \
    OLLAMA_PID=$! \
    && until curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; do sleep 1; done \
    && OLLAMA_HOST=127.0.0.1:11434 ollama pull aya-expanse:8b \
    && kill "$OLLAMA_PID" \
    && wait "$OLLAMA_PID" || true

COPY health.py start.sh test_input.json ./
RUN chmod +x /app/start.sh

EXPOSE 11434 8000

CMD ["/app/start.sh"]
