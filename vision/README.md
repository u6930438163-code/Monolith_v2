# Real Vision — Ollama Llama 3.2 Vision 11B

Default model: `llama3.2-vision:11b`. This is a functional Python client, not yet wired into the Monolith_v2 chat or agent workers.

On the host running Ollama:
```bash
ollama pull llama3.2-vision:11b
ollama serve
```

From a trusted host that can reach the Ollama API:
```bash
export OLLAMA_API_URL=http://127.0.0.1:11434
python3 -m vision.ollama_vision screenshot.png --prompt "Zdiagnozuj widoczne błędy"
python3 -m unittest discover -s tests -v
```

Do not expose port 11434 publicly. Set OLLAMA_API_URL only through trusted server configuration, not chat inputs. The client checks file size and image signatures and reports the actual model/provider. Integrating attachments requires authenticated file access, request limits, error handling and a backend route. No remote host has been deployed or tested here.
