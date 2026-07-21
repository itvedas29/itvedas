"""Shared Anthropic/OpenAI HTTP call helpers for all ITVedas brain scripts.

Extracted from the three near-identical copies that used to live in
scripts/brain.py, scripts/news_agent_v2.py, and scripts/self_improve.py
(coo-agent.py has its own single-shot call_claude() with no retry, used
only for the interactive chat loop - it is left as-is since it serves a
different purpose and isn't a duplicate of these retrying helpers).

Retry/timeout behavior matches the most complete of the three originals
(scripts/brain.py and scripts/self_improve.py both used this exact
pattern): up to 3 attempts, 90s per-request timeout, 8s sleep between
retries, raising on the final failed attempt.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Callable

from core.log import log as _default_log

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

RETRY_ATTEMPTS = 3
RETRY_SLEEP_SECONDS = 8
REQUEST_TIMEOUT_SECONDS = 90


def claude(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Call the Anthropic Messages API, with retry.

    api_key defaults to the ANTHROPIC_API_KEY environment variable.
    log_fn receives retry notices (defaults to core.log.log under the
    "llm" component); pass a no-op lambda to silence them.
    """
    key = (api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")).strip()
    notify = log_fn or (lambda msg: _default_log("llm", msg))

    payload = {
        "model": model or ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    for attempt in range(RETRY_ATTEMPTS):
        try:
            res = json.load(urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS))
            return strip_code_fence(res["content"][0]["text"].strip())
        except Exception as e:
            if attempt == RETRY_ATTEMPTS - 1:
                raise
            notify(f"Claude API retry {attempt + 1}: {e}")
            time.sleep(RETRY_SLEEP_SECONDS)


def openai_chat(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Call the OpenAI chat completions API, with retry.

    api_key defaults to the OPENAI_API_KEY environment variable.
    """
    key = (api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")).strip()
    notify = log_fn or (lambda msg: _default_log("llm", msg))

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model or OPENAI_MODEL, "max_tokens": max_tokens, "messages": messages}

    request = urllib.request.Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
        },
    )
    for attempt in range(RETRY_ATTEMPTS):
        try:
            res = json.load(urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS))
            return strip_code_fence(res["choices"][0]["message"]["content"].strip())
        except Exception as e:
            if attempt == RETRY_ATTEMPTS - 1:
                raise
            notify(f"OpenAI API retry {attempt + 1}: {e}")
            time.sleep(RETRY_SLEEP_SECONDS)


def strip_code_fence(text: str) -> str:
    """Strip a leading/trailing ``` markdown code fence, if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text
