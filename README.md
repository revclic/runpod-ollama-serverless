# RunPod Load-Balanced Ollama Aya Expanse

RunPod load-balanced Serverless template for native Ollama chat requests with `aya-expanse:8b` pre-pulled into the Docker image.

The container exposes Ollama directly on `PORT=11434` and runs a tiny standard-library Python health server on `PORT_HEALTH=8000` for RunPod's `/ping` check.

The Dockerfile clears the upstream Ollama image entrypoint so `/app/start.sh` can launch both the health server and `ollama serve`.

## HTTP Endpoints

- `GET /ping`: RunPod health check served by the health server on `PORT_HEALTH`.
- `POST /api/chat`: native Ollama chat endpoint served directly by Ollama on `PORT`.
- Other Ollama endpoints, such as `GET /api/tags`, are also exposed through RunPod.

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

Because traffic goes directly to Ollama, callers must provide the normal Ollama payload fields they need, including `model` and `stream`.

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

## Test Your RunPod URL

Set your RunPod API key locally:

```bash
export RUNPOD_API_KEY="YOUR_RUNPOD_API_KEY"
```

RunPod health check configuration:

```bash
curl -i https://YOUR_ENDPOINT_ID.api.runpod.ai/ping \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
```

When `PORT` and `PORT_HEALTH` are different, RunPod uses `/ping` for internal worker health checks on `PORT_HEALTH`. Public requests are routed to Ollama on `PORT`, so use a native Ollama endpoint for public smoke testing:

```bash
curl -i https://YOUR_ENDPOINT_ID.api.runpod.ai/api/tags \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
```

Chat request:

```bash
curl -i --request POST \
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
        "content": "Say only: ok"
      }
    ],
    "options": {
      "temperature": 0,
      "num_predict": 8
    }
  }'
```

Do not use `/runsync`, `/run`, or `/status` for this load-balanced template. Those operations are for queue-based RunPod endpoints.

## Backend Configuration

For an existing app that uses native Ollama URLs:

```bash
OLLAMA_URL=https://YOUR_ENDPOINT_ID.api.runpod.ai
OLLAMA_MODEL=aya-expanse:8b
OLLAMA_API_KEY=YOUR_RUNPOD_API_KEY
```

Your app must send the RunPod auth header:

```http
Authorization: Bearer YOUR_RUNPOD_API_KEY
```

## Local Test

Start the container locally and map both ports:

```bash
docker run --rm --gpus all \
  -p 11434:11434 \
  -p 8000:8000 \
  runpod-ollama-aya-expanse
```

Health check:

```bash
curl -i http://127.0.0.1:8000/ping
```

Chat request:

```bash
curl -i --request POST \
  --url http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d @test_input.json
```

## Docker Build

Build the image for RunPod:

```bash
docker build --platform linux/amd64 -t runpod-ollama-aya-expanse .
```

For CPU-only smoke testing:

```bash
docker run --rm \
  -p 11434:11434 \
  -p 8000:8000 \
  runpod-ollama-aya-expanse
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
5. Configure the HTTP port as `11434`.
6. Configure the health port as `8000`.
7. Configure the health path as `/ping`.
8. Confirm the worker becomes healthy, then send a request to `/api/tags` and `/api/chat`.

## Environment Variables

- `OLLAMA_HOST`: Ollama bind host and port, defaults to `0.0.0.0:11434`.
- `OLLAMA_MODEL`: model pre-pulled into the image, defaults to `aya-expanse:8b`.
- `PORT`: main Ollama HTTP port expected by RunPod load balancing, defaults to `11434`.
- `PORT_HEALTH`: health HTTP port expected by RunPod load balancing, defaults to `8000`.

## Endpoint Protection

RunPod protects load-balanced endpoint calls with your RunPod API key. This image exposes Ollama's native HTTP API through RunPod, so any reachable Ollama endpoint is available to callers with that key.

## License Notice

Aya Expanse is released under a Creative Commons Attribution-NonCommercial license with additional usage policies. Verify that your intended use complies with the model license before deploying it.
