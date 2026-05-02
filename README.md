# RunPod Serverless Ollama Aya Expanse

RunPod Serverless worker template for Ollama with `aya-expanse:8b` pre-pulled into the Docker image.

The worker exposes a queue-style RunPod handler, sends non-streaming chat requests to Ollama's local `/api/chat` endpoint, and returns a compact JSON response.

## Request Format

```json
{
  "input": {
    "messages": [
      {
        "role": "user",
        "content": "Write a short greeting in Spanish."
      }
    ],
    "options": {
      "temperature": 0.7,
      "num_predict": 256
    }
  }
}
```

Supported `input` fields:

- `messages`: required non-empty chat message array.
- `system`: optional system prompt prepended to `messages`.
- `options`: optional Ollama generation options.
- `keep_alive`: optional Ollama model keep-alive duration.

The model is fixed to `aya-expanse:8b` by default. You can override it with `OLLAMA_MODEL`, but the image pre-pulls `aya-expanse:8b`.

## Response Format

```json
{
  "content": "Hola, espero que tengas un dia excelente.",
  "model": "aya-expanse:8b",
  "done_reason": "stop",
  "prompt_eval_count": 18,
  "eval_count": 11
}
```

Invalid inputs return a structured error:

```json
{
  "error": {
    "message": "input.messages must be a non-empty array.",
    "status_code": 400
  }
}
```

## Local Handler Test

Start Ollama locally:

```bash
ollama serve
```

In another terminal, pull the model:

```bash
ollama pull aya-expanse:8b
```

Then install dependencies and run the RunPod local test:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python handler.py
```

RunPod's SDK automatically reads `test_input.json` for local tests. You can also pass input directly:

```bash
python handler.py --test_input '{"input":{"messages":[{"role":"user","content":"Say hello in French."}]}}'
```

## Docker Build

Build the image for RunPod:

```bash
docker build --platform linux/amd64 -t runpod-ollama-aya-expanse .
```

Run it locally with GPU access when available:

```bash
docker run --rm --gpus all runpod-ollama-aya-expanse
```

For CPU-only smoke testing:

```bash
docker run --rm runpod-ollama-aya-expanse
```

## Push To A Registry

Tag and push the image to your registry:

```bash
docker tag runpod-ollama-aya-expanse YOUR_REGISTRY/YOUR_IMAGE:latest
docker push YOUR_REGISTRY/YOUR_IMAGE:latest
```

Use `YOUR_REGISTRY/YOUR_IMAGE:latest` as the container image when creating the RunPod Serverless endpoint.

## RunPod Deployment

1. Build and push the Docker image.
2. Create a new RunPod Serverless endpoint.
3. Select a GPU with enough VRAM for `aya-expanse:8b`.
4. Set the container image to your pushed image.
5. Send a test job using the sample payload from `test_input.json`.

## Environment Variables

- `OLLAMA_MODEL`: model passed to Ollama, defaults to `aya-expanse:8b`.
- `OLLAMA_HOST`: Ollama host and port, defaults to `127.0.0.1:11434`.
- `OLLAMA_REQUEST_TIMEOUT_SECONDS`: request timeout, defaults to `600`.

## Endpoint Protection

RunPod protects Serverless endpoint calls with your RunPod API key. The local Ollama server itself is not exposed publicly; it listens inside the container and is called by `handler.py`.

## License Notice

Aya Expanse is released under a Creative Commons Attribution-NonCommercial license with additional usage policies. Verify that your intended use complies with the model license before deploying it.
