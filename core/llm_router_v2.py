"""Production-facing Ollama router. Emergency Llama 3.2 3B is OFF by default."""
import json
import os
import urllib.error
import urllib.request

EMERGENCY_MODEL = "llama3.2:3b"


class ModelUnavailable(RuntimeError):
    pass


def _generate(endpoint, model, prompt, timeout):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(endpoint.rstrip("/") + "/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        result = json.load(response)
    if not isinstance(result.get("response"), str):
        raise ValueError("Model response missing")
    return result["response"]


def route(prompt, *, primary=None, secondary=None, emergency_enabled=None,
          endpoint=None, timeout=30, generator=None):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt required")
    primary = primary if primary is not None else os.getenv("MONOLITH_LLM_PRIMARY", "")
    secondary = secondary if secondary is not None else os.getenv("MONOLITH_LLM_SECONDARY", "")
    if emergency_enabled is None:
        emergency_enabled = os.getenv("MONOLITH_LLM_EMERGENCY_ENABLED", "false").lower() in ("true", "1", "yes")
    models = [m for m in (primary, secondary) if m]
    if emergency_enabled:
        models.append(EMERGENCY_MODEL)
    models = list(dict.fromkeys(models))
    if not models:
        raise ModelUnavailable("No enabled LLM configured")
    endpoint = endpoint or os.getenv("MONOLITH_OLLAMA_URL", "http://127.0.0.1:11434")
    call = generator or _generate
    failures = []
    for index, model in enumerate(models):
        try:
            return {"response": call(endpoint, model, prompt, timeout),
                    "provider": "ollama", "model": model,
                    "emergency_model": model == EMERGENCY_MODEL,
                    "fallback_used": index > 0}
        except (OSError, TimeoutError, urllib.error.URLError, ValueError) as exc:
            failures.append({"model": model, "error": type(exc).__name__})
    raise ModelUnavailable("All enabled LLMs failed: " + json.dumps(failures))
