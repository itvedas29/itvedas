"""Shared Google Gemini HTTP call helpers for all ITVedas brain scripts.

Replaces legacy Anthropic and OpenAI integrations with Google Gemini (gemini-2.5-flash)
using standard library urllib.request (zero external dependencies).

Backwards-compatible aliases for claude and openai_chat are provided so all
pipeline modules continue to function without requiring refactoring.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Callable

from core.log import log as _default_log

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
RETRY_ATTEMPTS = 3
RETRY_SLEEP_SECONDS = 8
REQUEST_TIMEOUT_SECONDS = 90


def gemini(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Call Google Gemini generateContent API, with automatic retry."""
    key = api_key if api_key is not None else (
        os.environ.get("GEMINI_API_KEY") or
        os.environ.get("ANTHROPIC_API_KEY") or
        os.environ.get("OPENAI_API_KEY") or ""
    )
    notify = log_fn or (lambda msg: _default_log("llm", msg))
    target_model = model or GEMINI_MODEL

    if not key:
        notify("Warning: GEMINI_API_KEY is not set.")
        return ""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": min(max_tokens, 8192),
        },
    }
    if system:
        payload["systemInstruction"] = {
            "parts": [{"text": system}]
        }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )

    for attempt in range(RETRY_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return strip_code_fence(parts[0].get("text", "").strip())
                return ""
        except Exception as e:
            if attempt == RETRY_ATTEMPTS - 1:
                notify(f"Gemini API failed after {RETRY_ATTEMPTS} attempts: {e}")
                raise
            notify(f"Gemini API retry {attempt + 1}: {e}")
            time.sleep(RETRY_SLEEP_SECONDS)
    return ""


def claude(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Compatibility wrapper redirecting legacy Claude calls to Gemini."""
    return gemini(prompt, system=system, max_tokens=max_tokens, api_key=api_key, log_fn=log_fn)


def openai_chat(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Compatibility wrapper redirecting legacy OpenAI calls to Gemini."""
    return gemini(prompt, system=system, max_tokens=max_tokens, api_key=api_key, log_fn=log_fn)


def strip_code_fence(text: str) -> str:
    """Strip a leading/trailing ``` markdown code fence, if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text
