"""Runtime AI backend configuration and lightweight HTTP clients for midman."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_PROVIDER = "rule-based-local"


@dataclass
class AIBackendConfig:
    provider: str = DEFAULT_PROVIDER
    endpoint: str | None = None
    model: str | None = None
    api_key: str | None = None

    @property
    def display_name(self) -> str:
        if self.provider == DEFAULT_PROVIDER:
            return DEFAULT_PROVIDER
        parts = [self.provider]
        if self.model:
            parts.append(self.model)
        if self.endpoint:
            parts.append(f"@{self.endpoint}")
        return " ".join(parts)


_runtime_config = AIBackendConfig(
    provider=os.getenv("MIDMAN_AI_BACKEND") or os.getenv("NETDOC_AI_BACKEND", DEFAULT_PROVIDER),
    endpoint=(
        os.getenv("MIDMAN_OLLAMA_HOST")
        or os.getenv("MIDMAN_CLOUD_ENDPOINT")
        or os.getenv("NETDOC_OLLAMA_HOST")
        or os.getenv("NETDOC_CLOUD_ENDPOINT")
    ),
    model=(
        os.getenv("MIDMAN_OLLAMA_MODEL")
        or os.getenv("MIDMAN_OPENAI_MODEL")
        or os.getenv("NETDOC_OLLAMA_MODEL")
        or os.getenv("NETDOC_OPENAI_MODEL")
    ),
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("MIDMAN_CLOUD_API_KEY") or os.getenv("NETDOC_CLOUD_API_KEY"),
)


def get_backend_config() -> AIBackendConfig:
    return _runtime_config


def resolve_ai_backend() -> str:
    return _runtime_config.display_name


def configure_backend(provider: str, endpoint: str | None = None, model: str | None = None, api_key: str | None = None) -> AIBackendConfig:
    global _runtime_config
    _runtime_config = AIBackendConfig(provider=provider, endpoint=endpoint, model=model, api_key=api_key)
    return _runtime_config


def load_backend_from_mapping(payload: dict[str, str | None]) -> AIBackendConfig:
    return configure_backend(
        provider=payload.get("provider") or DEFAULT_PROVIDER,
        endpoint=payload.get("endpoint"),
        model=payload.get("model"),
        api_key=payload.get("api_key"),
    )


def backend_to_mapping(config: AIBackendConfig | None = None) -> dict[str, str | None]:
    return asdict(config or _runtime_config)


def normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint.rstrip("/")
    return f"http://{endpoint.rstrip('/')}"


def test_backend_connection(config: AIBackendConfig, timeout: float = 6.0) -> tuple[bool, str]:
    try:
        if config.provider == "openai":
            if not config.api_key:
                return False, "Missing OpenAI API key."
            _request_json(
                "GET",
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=timeout,
            )
            return True, "Connected to OpenAI API."
        if config.provider == "ollama":
            if not config.endpoint:
                return False, "Missing Ollama endpoint."
            _request_json("GET", f"{normalize_endpoint(config.endpoint)}/api/tags", timeout=timeout)
            return True, "Connected to Ollama."
        if config.provider == "cloud":
            if not config.endpoint:
                return False, "Missing cloud endpoint."
            headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
            _request_json("GET", f"{normalize_endpoint(config.endpoint)}/v1/models", headers=headers, timeout=timeout)
            return True, "Connected to cloud API."
        return True, "Using local rule-based parser."
    except RuntimeError as exc:
        return False, str(exc)


def chat_with_backend(config: AIBackendConfig, message: str, timeout: float = 20.0) -> str:
    try:
        if config.provider == "openai":
            if not config.api_key or not config.model:
                return "OpenAI backend is missing an API key or model."
            response = _request_json(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                payload={"model": config.model, "messages": [{"role": "user", "content": message}]},
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=timeout,
            )
            return response["choices"][0]["message"]["content"].strip()
        if config.provider == "ollama":
            if not config.endpoint or not config.model:
                return "Ollama backend is missing an endpoint or model."
            response = _request_json(
                "POST",
                f"{normalize_endpoint(config.endpoint)}/api/chat",
                payload={
                    "model": config.model,
                    "stream": False,
                    "messages": [{"role": "user", "content": message}],
                },
                timeout=timeout,
            )
            return response["message"]["content"].strip()
        if config.provider == "cloud":
            if not config.endpoint or not config.model:
                return "Cloud backend is missing an endpoint or model."
            headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
            response = _request_json(
                "POST",
                f"{normalize_endpoint(config.endpoint)}/v1/chat/completions",
                payload={"model": config.model, "messages": [{"role": "user", "content": message}]},
                headers=headers,
                timeout=timeout,
            )
            return response["choices"][0]["message"]["content"].strip()
    except RuntimeError as exc:
        return f"AI backend error: {exc}"

    return "Rule-based backend is active. Configure OpenAI or Ollama for free-form chat."


def _request_json(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> dict:
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode()
            return json.loads(body) if body else {}
    except HTTPError as exc:
        try:
            details = exc.read().decode()
        except Exception:  # noqa: BLE001
            details = exc.reason
        raise RuntimeError(_format_http_error(exc.code, details)) from exc
    except URLError as exc:
        raise RuntimeError(f"Connection failed: {exc.reason}") from exc


def _format_http_error(status_code: int, details: str) -> str:
    try:
        payload = json.loads(details)
    except json.JSONDecodeError:
        return f"HTTP {status_code}: {details}"
    error = payload.get("error", {})
    message = error.get("message")
    code = error.get("code") or error.get("type")
    if message and code:
        return f"HTTP {status_code} ({code}): {message}"
    if message:
        return f"HTTP {status_code}: {message}"
    return f"HTTP {status_code}: {details}"
