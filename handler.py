import os
from typing import Any

import requests
import runpod


MODEL = os.getenv("OLLAMA_MODEL", "aya-expanse:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
OLLAMA_CHAT_URL = f"http://{OLLAMA_HOST}/api/chat"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_REQUEST_TIMEOUT_SECONDS", "600"))


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


def handler(job: dict[str, Any]) -> dict[str, Any]:
    job_input = job.get("input", {})
    if not isinstance(job_input, dict):
        return error_response("Job input must be an object.")

    if OLLAMA_API_KEY and job_input.get("api_key") != OLLAMA_API_KEY:
        return error_response("Invalid or missing API key.", 401)

    validation_error = validate_messages(job_input.get("messages"))
    if validation_error:
        return error_response(validation_error)

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
        return error_response("Timed out waiting for Ollama.", 504)
    except requests.RequestException as exc:
        return error_response(f"Ollama request failed: {exc}", 502)

    try:
        return compact_ollama_response(response.json())
    except ValueError:
        return error_response("Ollama returned a non-JSON response.", 502)


runpod.serverless.start({"handler": handler})
