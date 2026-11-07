"""Monolith local Ollama emergency fallback.

Explicit model routing: no fabricated replies, no root execution, no silent fallback.
Uses stdlib HTTP only. Caller configures primary and secondary Ollama models.
"""
import json
import os
import urllib.error
import urllib.request

DEFAULT_EMERGENCY_MODEL = "qwen3:1.7b"


class AllModelsUnavailable(RuntimeError):
    pass


def _ollama_generate(endpoint, model, prompt, timeout):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/api/generate", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload.get("response"), str):
        raise ValueError("Ollama returned no response text")
    return payload["response"]


def generate_with_fallback(prompt, *, endpoint=None, primary=None, secondary=None,
                           emergency=None, timeout=30, generator=None):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    endpoint = endpoint or os.environ.get("MONOLITH_OLLAMA_URL", "http://127.0.0.1:11434")
    primary = primary if primary is not None else os.environ.get("MONOLITH_LLM_PRIMARY", "")
    secondary = secondary if secondary is not None else os.environ.get("MONOLITH_LLM_SECONDARY", "")
    emergency = emergency or os.environ.get("MONOLITH_LLM_EMERGENCY", DEFAULT_EMERGENCY_MODEL)
    models = list(dict.fromkeys(m for m in (primary, secondary, emergency) if m))
    call = generator or _ollama_generate
    errors = []
    for index, model in enumerate(models):
        try:
            answer = call(endpoint, model, prompt, timeout)
            return {"answer": answer, "provider": "ollama", "model": model,
                    "fallback_used": index > 0, "attempted_models": models[:index + 1]}
        except (OSError, TimeoutError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            errors.append({"model": model, "error_type": type(exc).__name__})
    raise AllModelsUnavailable("All configured Ollama models failed: " + json.dumps(errors))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("prompt")
    args = p.parse_args()
    print(json.dumps(generate_with_fallback(args.prompt), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
