#!/usr/bin/env python3
"""Small Ollama client, copied from newscalm."""

from __future__ import annotations

import json
import os
import urllib.request

OLLAMA_URL = os.environ.get("TECHULTURE_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
DEFAULT_MODEL = os.environ.get("TECHULTURE_OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_TIMEOUT_SECONDS = 60


def build_payload(prompt: str, model: str = DEFAULT_MODEL) -> bytes:
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    return json.dumps(body).encode("utf-8")


def call_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    request = urllib.request.Request(
        OLLAMA_URL,
        data=build_payload(prompt, model=model),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
