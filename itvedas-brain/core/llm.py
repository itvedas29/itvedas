"""Shared Claude API helper for all ITVedas brain scripts.

Every LLM call in the pipeline goes through claude() here, using the official
`anthropic` SDK (pinned in requirements.txt). The SDK retries 429/5xx and
connection errors itself.

openai_chat() is kept as an alias so older call sites keep working.
"""
from __future__ import annotations

import json
import os
from typing import Callable

import anthropic

from core.log import log as _default_log

DEFAULT_MODEL = "claude-opus-5-5"
# `or` (not a default arg) so an empty CLAUDE_MODEL from CI counts as unset.
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL") or DEFAULT_MODEL

# Server-side refusal fallback: if the safety classifiers decline a request
# (security news about exploits can trip the cyber classifier), the API re-runs
# it on Anthropic's recommended fallback model instead of returning nothing.
# Only these models accept the "default" form.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

REQUEST_TIMEOUT_SECONDS = 300
MAX_RETRIES = 4

_clients: dict[str, anthropic.Anthropic] = {}


def _client(key: str) -> anthropic.Anthropic:
    if key not in _clients:
        _clients[key] = anthropic.Anthropic(
            api_key=key, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES)
    return _clients[key]


def claude(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    effort: str = "medium",
    json_schema: dict | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Send one user prompt to Claude and return the reply text.

    Returns "" when Claude declines or produces no text (the reason is logged).
    Raises RuntimeError on API errors once the SDK's retries are exhausted.
    With json_schema, the reply is guaranteed to be JSON matching it.
    """
    # Only ever send an Anthropic key to Anthropic; never fall back to keys
    # issued by other providers.
    key = ((api_key or "").strip() or os.environ.get("ANTHROPIC_API_KEY", "")).strip()
    notify = log_fn or (lambda msg: _default_log("llm", msg))
    model_name = model or CLAUDE_MODEL

    if not key:
        notify("Warning: ANTHROPIC_API_KEY is not set.")
        return ""

    output_config: dict = {"effort": effort}
    if json_schema:
        output_config["format"] = {"type": "json_schema", "schema": json_schema}
    params: dict = {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "output_config": output_config,
    }
    if system:
        params["system"] = system
    if model_name in _FALLBACK_MODELS:
        params["betas"] = [_FALLBACK_BETA]
        params["fallbacks"] = "default"

    try:
        response = _client(key).beta.messages.create(**params)
    except anthropic.APIStatusError as e:
        notify(f"Claude API error {e.status_code} ({model_name}): {e.message} "
               f"[request {e.request_id}]")
        raise RuntimeError(f"Claude API error {e.status_code}: {e.message}") from None
    except anthropic.APIConnectionError as e:
        notify(f"Claude API unreachable ({model_name}): {e}")
        raise RuntimeError(f"Claude API unreachable: {e}") from None

    if response.stop_reason == "refusal":
        category = getattr(response.stop_details, "category", None)
        notify(f"Claude declined the request (category: {category or 'unknown'}, "
               f"model {response.model}) [request {response._request_id}]")
        return ""

    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if response.stop_reason == "max_tokens":
        notify(f"Claude hit max_tokens={max_tokens} ({response.model}); reply may be truncated.")
    if not text:
        notify(f"Claude returned no text (stop reason: {response.stop_reason}) "
               f"[request {response._request_id}]")
        return ""
    return text if json_schema else strip_code_fence(text)


def claude_json(prompt: str, schema: dict, **kwargs) -> dict | None:
    """claude() with a JSON schema; returns the parsed object, or None."""
    text = claude(prompt, json_schema=schema, **kwargs)
    return json.loads(text) if text else None


def openai_chat(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 4000,
    *,
    api_key: str | None = None,
    model: str | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> str:
    """Compatibility alias for legacy call sites; routes to Claude."""
    return claude(prompt, system=system, max_tokens=max_tokens,
                  api_key=api_key, model=model, log_fn=log_fn)


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
