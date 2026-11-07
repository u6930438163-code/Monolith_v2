"""Real Vision client for local Ollama Llama 3.2 Vision 11B.

Uses Ollama /api/chat, standard library only. No shell execution.
"""
import base64
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MODEL = "llama3.2-vision:11b"
MAX_IMAGE_BYTES = 12 * 1024 * 1024
ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp"}
MAGIC = {b"\x89PNG\r\n\x1a\n": "image/png", b"\xff\xd8\xff": "image/jpeg", b"RIFF": "image/webp"}


def validate_image(data: bytes) -> str:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image empty or exceeds 12 MiB")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Only PNG, JPEG or WebP images are supported")


def analyze_image(image: bytes, prompt: str, *, base_url: str | None = None, timeout: int = 120) -> dict:
    """Analyze image; caller must authenticate user and authorize attachment access."""
    mime = validate_image(image)
    if not prompt.strip() or len(prompt) > 8000:
        raise ValueError("Prompt length must be 1..8000 characters")
    url = (base_url or os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434")).rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.path not in {"", "/"}:
        raise ValueError("Invalid Ollama endpoint")
    # Never take the endpoint from untrusted chat input; configure via trusted server env.
    payload = json.dumps({
        "model": MODEL, "stream": False,
        "messages": [{"role": "user", "content": prompt, "images": [base64.b64encode(image).decode("ascii")]}],
        "options": {"num_predict": 1024},
    }).encode("utf-8")
    req = Request(url + "/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout) as response:
        result = json.load(response)
    return {"provider": "Ollama", "model": MODEL, "mime": mime, "answer": result.get("message", {}).get("content", ""), "done": result.get("done", False)}


def analyze_file(path: str, prompt: str) -> dict:
    """Local CLI convenience only; paths must not come from remote users."""
    file = Path(path)
    if file.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds 12 MiB")
    return analyze_image(file.read_bytes(), prompt)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Local PNG/JPEG/WebP image")
    parser.add_argument("--prompt", default="Opisz dokładnie, co widać na obrazie.")
    args = parser.parse_args()
    print(json.dumps(analyze_file(args.image, args.prompt), ensure_ascii=False, indent=2))
