#!/usr/bin/env python3
"""Small client for an OpenAI-compatible chat endpoint, such as llama.cpp's llama-server."""

from __future__ import annotations

import json
import os
import urllib.request

# The workflow starts llama-server here; locally, nothing listens and callers fall back.
LLM_URL = os.environ.get("TECHULTURE_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
# llama-server serves the one model it was started with, so the name is informational.
DEFAULT_MODEL = os.environ.get("TECHULTURE_LLM_MODEL", "qwen2.5-3b-instruct")
# CPU-only runners are slow; a batch of ten headlines can take a minute.
DEFAULT_TIMEOUT_SECONDS = 180


def build_payload(prompt: str, model: str = DEFAULT_MODEL) -> bytes:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "stream": False,
    }
    return json.dumps(body).encode("utf-8")


def call_llm(prompt: str, model: str = DEFAULT_MODEL, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    request = urllib.request.Request(
        LLM_URL,
        data=build_payload(prompt, model=model),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
    return str(body["choices"][0]["message"]["content"])
