FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_MODEL=aya-expanse:8b \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r requirements.txt

RUN ollama serve > /tmp/ollama-build.log 2>&1 & \
    OLLAMA_PID=$! \
    && until curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; do sleep 1; done \
    && ollama pull aya-expanse:8b \
    && kill "$OLLAMA_PID" \
    && wait "$OLLAMA_PID" || true

COPY handler.py start.sh test_input.json ./
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
