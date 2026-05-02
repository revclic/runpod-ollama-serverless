# RunPod Load-Balanced Ollama Aya Expanse

RunPod load-balanced Serverless template for native Ollama-compatible chat requests with `aya-expanse:8b` pre-pulled into the Docker image.

The container starts Ollama privately on `127.0.0.1:11434`, then starts a FastAPI HTTP server on the port RunPod provides in `PORT`. RunPod routes external traffic to the FastAPI app, not directly to Ollama.

## HTTP Endpoints

- `GET /ping`: health check endpoint expected by RunPod load balancing.
- `GET /health`: alias for `/ping`.
- `POST /api/chat`: Ollama-compatible chat endpoint.

## Request Format

Existing Ollama clients can point their base URL at this RunPod endpoint and keep calling `/api/chat`.

```json
{
  "model": "aya-expanse:8b",
  "stream": false,
  "keep_alive": -1,
  "messages": [
    {
      "role": "user",
      "content": "Write a short greeting in Spanish."
    }
  ]
}
```

If `model` is omitted, the service defaults it to `aya-expanse:8b`. The service always forces `stream: false`.

## Response Format

`/api/chat` returns Ollama's native response shape unchanged, including `message.content`:

```json
{
  "model": "aya-expanse:8b",
  "created_at": "...",
  "message": {
    "role": "assistant",
    "content": "Hola, espero que tengas un dia excelente."
  },
  "done_reason": "stop",
  "done": true
}
```

Invalid inputs return a structured error:

```json
{
  "error": {
    "message": "messages must be a non-empty array.",
    "status_code": 400
  }
}
```

## Test Your RunPod URL

Set your RunPod API key locally:

```bash
export RUNPOD_API_KEY="YOUR_RUNPOD_API_KEY"
```

Health check:

```bash
curl https://YOUR_ENDPOINT_ID.api.runpod.ai/ping \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
```

Chat request:

```bash
curl --request POST \
  --url https://YOUR_ENDPOINT_ID.api.runpod.ai/api/chat \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "aya-expanse:8b",
    "stream": false,
    "keep_alive": -1,
    "messages": [
      {
        "role": "user",
        "content": "Write a short greeting in Spanish."
      }
    ]
  }'
```

Do not use `/runsync`, `/run`, or `/status` for this load-balanced template. Those operations are for queue-based RunPod endpoints.

## Backend Configuration

For an existing app that uses native Ollama URLs:

```bash
OLLAMA_URL=https://YOUR_ENDPOINT_ID.api.runpod.ai
OLLAMA_MODEL=aya-expanse:8b
RUNPOD_API_KEY=YOUR_RUNPOD_API_KEY
```

Your app must send the RunPod auth header:

```http
Authorization: Bearer YOUR_RUNPOD_API_KEY
```

## Local Test

Start Ollama locally:

```bash
ollama serve
```

In another terminal, pull the model:

```bash
ollama pull aya-expanse:8b
```

Then install dependencies and run the HTTP app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PORT=8000 uvicorn handler:app --host 0.0.0.0 --port 8000
```

Test locally:

```bash
curl --request POST \
  --url http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d @test_input.json
```

## Docker Build

Build the image for RunPod:

```bash
docker build --platform linux/amd64 -t runpod-ollama-aya-expanse .
```

Run it locally with GPU access when available:

```bash
docker run --rm --gpus all -p 8000:8000 runpod-ollama-aya-expanse
```

For CPU-only smoke testing:

```bash
docker run --rm -p 8000:8000 runpod-ollama-aya-expanse
```

## Push To A Registry

Tag and push the image to your registry:

```bash
docker tag runpod-ollama-aya-expanse YOUR_REGISTRY/YOUR_IMAGE:latest
docker push YOUR_REGISTRY/YOUR_IMAGE:latest
```

Use `YOUR_REGISTRY/YOUR_IMAGE:latest` as the container image when creating the RunPod load-balanced endpoint.

## RunPod Deployment

1. Build and push the Docker image.
2. Create a RunPod Serverless endpoint with load balancing enabled.
3. Select a GPU with enough VRAM for `aya-expanse:8b`.
4. Set the container image to your pushed image.
5. Configure the HTTP port to match the `PORT` environment variable. The image defaults to `8000`, but RunPod may inject its own value.
6. Configure the health port to match `PORT_HEALTH`. The image defaults `PORT_HEALTH` to the same value as `PORT`.
7. Send a request to `/ping`, then `/api/chat`.

## Environment Variables

- `OLLAMA_MODEL`: default model used when requests omit `model`, defaults to `aya-expanse:8b`.
- `OLLAMA_HOST`: Ollama host and port, defaults to `127.0.0.1:11434`.
- `OLLAMA_REQUEST_TIMEOUT_SECONDS`: request timeout, defaults to `600`.
- `PORT`: main HTTP port expected by RunPod load balancing, defaults to `8000`.
- `PORT_HEALTH`: health HTTP port expected by RunPod load balancing, defaults to `PORT`.

## Endpoint Protection

RunPod protects load-balanced endpoint calls with your RunPod API key. The local Ollama server itself is not exposed publicly; it listens inside the container and is called by `handler.py`.

## License Notice

Aya Expanse is released under a Creative Commons Attribution-NonCommercial license with additional usage policies. Verify that your intended use complies with the model license before deploying it.
