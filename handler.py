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
        return "input.messages must be a non-empty array."

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            return f"input.messages[{index}] must be an object."

        role = message.get("role")
        content = message.get("content")

        if role not in {"system", "user", "assistant", "tool"}:
            return f"input.messages[{index}].role must be one of: system, user, assistant, tool."

        if not isinstance(content, str) or not content.strip():
            return f"input.messages[{index}].content must be a non-empty string."

    return None


def build_messages(job_input: dict[str, Any]) -> list[dict[str, str]]:
    messages = job_input["messages"]
    system_prompt = job_input.get("system")

    if isinstance(system_prompt, str) and system_prompt.strip():
        return [{"role": "system", "content": system_prompt}, *messages]

    return messages


def compact_ollama_response(response: dict[str, Any]) -> dict[str, Any]:
    message = response.get("message") or {}

    result = {
        "content": message.get("content", ""),
        "model": response.get("model", MODEL),
    }

    for key in (
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    ):
        if key in response:
            result[key] = response[key]

    return result


def normalize_input(payload: dict[str, Any]) -> dict[str, Any]:
    job_input = payload.get("input")
    if isinstance(job_input, dict):
        return job_input

    return payload


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


@app.post("/chat")
def chat(payload: dict[str, Any]) -> JSONResponse:
    job_input = normalize_input(payload)
    if not isinstance(job_input, dict):
        return JSONResponse(error_response("Request body must be an object."), status_code=400)

    validation_error = validate_messages(job_input.get("messages"))
    if validation_error:
        return JSONResponse(error_response(validation_error), status_code=400)

    payload: dict[str, Any] = {
        "model": MODEL,
        "messages": build_messages(job_input),
        "stream": False,
    }

    for optional_key in ("options", "keep_alive"):
        if optional_key in job_input:
            payload[optional_key] = job_input[optional_key]

    try:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.Timeout:
        return JSONResponse(error_response("Timed out waiting for Ollama.", 504), status_code=504)
    except requests.RequestException as exc:
        return JSONResponse(error_response(f"Ollama request failed: {exc}", 502), status_code=502)

    try:
        return JSONResponse(compact_ollama_response(response.json()))
    except ValueError:
        return JSONResponse(error_response("Ollama returned a non-JSON response.", 502), status_code=502)
