import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests


MODEL = os.getenv("OLLAMA_MODEL", "aya-expanse:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
OLLAMA_CHAT_URL = f"http://{OLLAMA_HOST}/api/chat"
REQUEST_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_REQUEST_TIMEOUT_SECONDS", "600"))

app = FastAPI(title="RunPod Ollama Aya Expanse")
health_app = FastAPI(title="RunPod Ollama Aya Expanse Health")


def error_response(message: str, status_code: int = 400) -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "status_code": status_code,
        }
    }


def validate_messages(messages: Any) -> str | None:
    if not isinstance(messages, list) or not messages:
        return "messages must be a non-empty array."

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            return f"messages[{index}] must be an object."

        role = message.get("role")
        content = message.get("content")

        if role not in {"system", "user", "assistant", "tool"}:
            return f"messages[{index}].role must be one of: system, user, assistant, tool."

        if not isinstance(content, str) or not content.strip():
            return f"messages[{index}].content must be a non-empty string."

    return None


def post_ollama_chat(payload: dict[str, Any]) -> requests.Response:
    return requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def health_status() -> dict[str, Any]:
    try:
        response = requests.get(f"http://{OLLAMA_HOST}/api/tags", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {
            "status": "unhealthy",
            "model": MODEL,
            "ollama_host": OLLAMA_HOST,
            "error": str(exc),
        }

    return {
        "status": "healthy",
        "model": MODEL,
        "ollama_host": OLLAMA_HOST,
    }


@app.get("/ping")
def ping() -> dict[str, Any]:
    return health_status()


@app.get("/health")
def health() -> dict[str, Any]:
    return health_status()


@health_app.get("/ping")
def health_ping() -> dict[str, Any]:
    return health_status()


@app.post("/api/chat")
def ollama_compatible_chat(payload: dict[str, Any]) -> JSONResponse:
    payload = {
        **payload,
        "model": payload.get("model", MODEL),
        "stream": False,
    }

    validation_error = validate_messages(payload.get("messages"))
    if validation_error:
        return JSONResponse(error_response(validation_error), status_code=400)

    try:
        response = post_ollama_chat(payload)
        response.raise_for_status()
    except requests.Timeout:
        return JSONResponse(error_response("Timed out waiting for Ollama.", 504), status_code=504)
    except requests.RequestException as exc:
        return JSONResponse(error_response(f"Ollama request failed: {exc}", 502), status_code=502)

    try:
        return JSONResponse(response.json())
    except ValueError:
        return JSONResponse(error_response("Ollama returned a non-JSON response.", 502), status_code=502)
