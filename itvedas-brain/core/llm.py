"""Shared Google Gemini HTTP call helpers for all ITVedas brain scripts.

Replaces legacy Anthropic and OpenAI integrations with Google Gemini (gemini-2.5-flash)
using standard library urllib.request (zero external dependencies).

Backwards-compatible aliases for claude and openai_chat are provided so all
pipeline modules continue to function without requiring refactoring.
"""
from __future__ import annotations

import json
import os
import random
import time
import urllib.request
import urllib.error
from typing import Callable

from core.log import log as _default_log

DEFAULT_MODEL = "gemini-2.5-flash"
# `or` (not a default arg) so an empty GEMINI_MODEL from CI counts as unset.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL

# Model that actually worked this process; set after a 404 fallback so later
# calls in the same run go straight to it.
_resolved_model: str | None = None
_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=100"
_BAD_NAME_PARTS = ("lite", "image", "tts", "live", "audio", "embedding", "exp",
                   "preview", "thinking", "8b", "vision", "robotics", "computer")

RETRY_ATTEMPTS = 5            # per model, for transient errors only
RETRY_SLEEP_SECONDS = 5       # backoff: 5, 10, 20, 40 (+jitter), capped below
MAX_BACKOFF_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 90
# Errors worth retrying: rate limit, overloaded, gateway/server trouble.
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
# Spacing between calls keeps us under free-tier requests-per-minute limits.
MIN_INTERVAL_SECONDS = float(os.environ.get("GEMINI_MIN_INTERVAL") or 6)
_last_call_at = 0.0


def _model_rank(name: str):
    """Sort key: newest stable `gemini-X[.Y]-flash*` first. None = not a candidate."""
    import re
    m = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-flash(?:-latest)?", name)
    if m:
        return (1, float(m.group(1)))
    if name in ("gemini-flash-latest",):
        return (1, 999.0)
    return None


def discover_models(key: str, log: Callable[[str], None]) -> list[str]:
    """Ask Google which Flash models this key can call, best first."""
    req = urllib.request.Request(_MODELS_URL, headers={"x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # never leak the key into logs
        log(f"Could not list Gemini models: {str(e).replace(key, '***')}")
        return []
    names = []
    for m in data.get("models", []):
        if "generateContent" not in m.get("supportedGenerationMethods", []):
            continue
        name = m.get("name", "").removeprefix("models/")
        if any(bad in name for bad in _BAD_NAME_PARTS):
            continue
        if _model_rank(name):
            names.append(name)
    names.sort(key=_model_rank, reverse=True)
    log(f"Gemini models available to this key: {', '.join(names) or 'none matched'}")
    return names


class _ModelNotFound(Exception):
    pass


class _ModelBusy(Exception):
    """Retries exhausted on 429/5xx/timeouts; another model may still work."""


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
    # Only ever send a Gemini key to Google. Never fall back to keys issued by
    # other providers (ANTHROPIC_API_KEY / OPENAI_API_KEY): doing so would hand
    # a third party's secret to Google's endpoint and its request logs.
    key = ((api_key or "").strip() or os.environ.get("GEMINI_API_KEY", "")).strip()

    notify = log_fn or (lambda msg: _default_log("llm", msg))
    global _resolved_model
    target_model = _resolved_model or model or GEMINI_MODEL

    if not key:
        notify("Warning: GEMINI_API_KEY is not set.")
        return ""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": min(max_tokens, 8192),
        },
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    body = json.dumps(payload).encode("utf-8")

    def call(model_name: str) -> str:
        """One model, with backoff for transient errors.

        404 -> _ModelNotFound; retries exhausted on 429/5xx -> _ModelBusy;
        any other HTTP error (bad key, bad request) fails at once.
        """
        global _last_call_at
        # Key goes in a header, not the query string, so it can't leak into
        # proxy, CDN or exception logs that record full URLs.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
        wait = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_call_at)
        if wait > 0:
            time.sleep(wait)
        err: Exception = RuntimeError("unknown error")
        for attempt in range(RETRY_ATTEMPTS):
            request = urllib.request.Request(url, data=body, headers=headers)
            retry_after = None
            try:
                _last_call_at = time.monotonic()
                with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return strip_code_fence(parts[0].get("text", "").strip())
                    return ""
            except urllib.error.HTTPError as e:
                if e.code == 404:  # model does not exist: retrying is pointless
                    raise _ModelNotFound(model_name) from None
                err = RuntimeError(str(e).replace(key, "***"))
                if e.code not in RETRYABLE_HTTP:  # 400/401/403...: retrying can't help
                    notify(f"Gemini API error (not retrying): {err}")
                    raise err
                ra = (e.headers.get("Retry-After") if e.headers else None) or ""
                retry_after = float(ra) if ra.replace(".", "", 1).isdigit() else None
            except Exception as e:  # timeouts / connection resets
                err = RuntimeError(str(e).replace(key, "***")) if key in str(e) else e
            if attempt == RETRY_ATTEMPTS - 1:
                break
            delay = min(RETRY_SLEEP_SECONDS * (2 ** attempt), MAX_BACKOFF_SECONDS)
            delay += random.uniform(0, delay * 0.1)
            if retry_after:  # Google told us how long to wait
                delay = max(delay, min(retry_after, MAX_BACKOFF_SECONDS))
            notify(f"Gemini '{model_name}' retry {attempt + 1}/{RETRY_ATTEMPTS - 1}: {err} (waiting {delay:.0f}s)")
            time.sleep(delay)
        notify(f"Gemini '{model_name}' still failing after {RETRY_ATTEMPTS} attempts: {err}")
        raise _ModelBusy(str(err))

    reason = ""
    try:
        return call(target_model)
    except _ModelNotFound:
        reason = "returned 404 (retired or renamed?)"
    except _ModelBusy as e:
        reason = f"is overloaded or rate-limited ({e})"
    notify(f"Gemini model '{target_model}' {reason}. Looking for another model...")

    candidates = [m for m in discover_models(key, notify) if m != target_model]
    last_busy = ""
    for candidate in candidates[:4]:
        try:
            out = call(candidate)
        except _ModelNotFound:
            continue
        except _ModelBusy as e:
            last_busy = str(e)
            continue
        _resolved_model = candidate
        notify(f"Using Gemini model '{candidate}' instead. Set GEMINI_MODEL={candidate} to make this permanent.")
        return out
    raise RuntimeError(
        f"No usable Gemini model found (tried '{target_model}' and {candidates[:4] or 'no alternatives'}). "
        + (f"Last error: {last_busy}. " if last_busy else "")
        + "If this is 429, the API quota is exhausted (check Google AI Studio usage/billing); "
        "otherwise check that the key is valid and the Generative Language API is enabled."
    )


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
