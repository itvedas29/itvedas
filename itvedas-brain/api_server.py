#!/usr/bin/env python3
"""Phase 9 - COO Agent API server.

A thin FastAPI wrapper around itvedas-brain/coo-agent.py. It imports the
hyphenated module via importlib (the file is intentionally not renamed,
so the existing CLI usage - `python3 itvedas-brain/coo-agent.py` and
`--once "..."` - keeps working unchanged for the GitHub Actions workflow
docstrings and any manual SSH usage) and exposes the same conversation,
context, recommendation, and whitelisted-action surface over HTTP for the
ITVedas COO dashboard frontend.

This file adds zero new business logic: every endpoint below just calls a
function that already exists in coo-agent.py (load_context,
format_context_markdown, recommend_actions, dispatch, handle_run_command,
handle_approve_command, ACTIONS, Memory). The approval gate for mutating
actions (currently only create-github-issues) is preserved exactly as-is.

Run with:
    uvicorn itvedas-brain.api_server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import secrets
import threading
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

BASE_DIR = pathlib.Path(__file__).resolve().parent


def _load_coo_agent():
    spec = importlib.util.spec_from_file_location("coo_agent", BASE_DIR / "coo-agent.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


coo_agent = _load_coo_agent()

# Single shared Memory instance + lock: this is a single-user system (one
# operator, one dashboard), so a per-process instance guarded by a lock is
# enough - no need for per-request state or a database.
_memory_lock = threading.Lock()
_memory = coo_agent.Memory(coo_agent.DEFAULT_MEMORY)

_DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")
# Random token minted at startup; invalidated on process restart.
_SESSION_TOKEN = secrets.token_hex(32)

_bearer = HTTPBearer(auto_error=False)


def _require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if not _DASHBOARD_PASSWORD:
        return
    if credentials is None or credentials.credentials != _SESSION_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(title="ITVedas COO Agent API")

# Dev: Vite default port. Production: the dashboard's real origin.
# Add additional origins here (or switch to an env var) once the
# production domain is finalized.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ai.itvedas.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    password: str


class ChatRequest(BaseModel):
    message: str


class RunRequest(BaseModel):
    action_id: str


class ApproveRequest(BaseModel):
    action_id: str
    confirm: bool = False


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login")
def login(body: LoginRequest) -> dict[str, str]:
    if not _DASHBOARD_PASSWORD:
        return {"token": "no-auth"}
    if body.password != _DASHBOARD_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"token": _SESSION_TOKEN}


@app.post("/api/chat")
def chat(body: ChatRequest, _: None = Depends(_require_auth)) -> dict[str, str]:
    context = coo_agent.load_context()
    with _memory_lock:
        _memory.add_turn("user", body.message)
        reply = coo_agent.answer_question(body.message, context, _memory)
        _memory.add_turn("assistant", reply)
    return {"reply": reply}


@app.get("/api/context")
def context(_: None = Depends(_require_auth)) -> dict[str, str]:
    ctx = coo_agent.load_context()
    return {"context": coo_agent.format_context_markdown(ctx)}


@app.get("/api/recommend")
def recommend(_: None = Depends(_require_auth)) -> dict[str, str]:
    ctx = coo_agent.load_context()
    return {"recommendations": coo_agent.recommend_actions(ctx)}


@app.get("/api/actions")
def actions(_: None = Depends(_require_auth)) -> dict[str, list[dict[str, Any]]]:
    items = [
        {
            "id": action_id,
            "description": action["description"],
            "requires_approval": action["requires_approval"],
        }
        for action_id, action in sorted(coo_agent.ACTIONS.items())
    ]
    return {"actions": items}


@app.post("/api/run")
def run(body: RunRequest, _: None = Depends(_require_auth)) -> dict[str, str]:
    action = coo_agent.ACTIONS.get(body.action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Unknown action '{body.action_id}'.")
    if action["requires_approval"]:
        raise HTTPException(
            status_code=403,
            detail=f"'{body.action_id}' requires approval - use /api/approve instead.",
        )
    with _memory_lock:
        output = coo_agent.handle_run_command(body.action_id, _memory)
    return {"output": output}


@app.post("/api/approve")
def approve(body: ApproveRequest, _: None = Depends(_require_auth)) -> dict[str, str]:
    action = coo_agent.ACTIONS.get(body.action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Unknown action '{body.action_id}'.")
    if not action["requires_approval"]:
        raise HTTPException(
            status_code=400,
            detail=f"'{body.action_id}' does not require approval - use /api/run instead.",
        )
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="This action mutates an external system. Set confirm=true to proceed.",
        )
    with _memory_lock:
        output = coo_agent.handle_approve_command(body.action_id, _memory)
    return {"output": output}


@app.get("/api/memory")
def memory(_: None = Depends(_require_auth)) -> dict[str, list[dict[str, Any]]]:
    return {
        "conversation_log": _memory.data.get("conversation_log", [])[-50:],
        "decisions": _memory.data.get("decisions", [])[-50:],
    }
