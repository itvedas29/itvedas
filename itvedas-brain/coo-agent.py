#!/usr/bin/env python3
"""Phase 8 - ITVedas COO Agent.

A conversational manager that sits on top of the entire brain pipeline.
It reads everything the other phases have already produced, keeps its
own memory of conversations and decisions across runs, answers business
questions, recommends actions, and executes a whitelisted set of those
actions when explicitly approved.

It never invents new data sources: every fact it can discuss comes from
files already written by repo-scanner.py, knowledge-builder.py,
decision-engine.py, execution-engine.py, and github-agent.py. This script is the
conversation/decision layer on top of that pipeline, not a replacement
for it.

Credentials
-----------
  ANTHROPIC_API_KEY    Required for free-form conversation (the
                        question-answering loop). Without it, the agent
                        still supports all slash commands (/context,
                        /recommend, /run, /approve, /memory) - only the
                        natural-language chat degrades to a notice that
                        explains what's missing.
  ANTHROPIC_MODEL       Optional override (defaults to the same Haiku
                        model used by scripts/brain.py).
  GITHUB_TOKEN          Required only for the create-issues action,
                        which is gated behind explicit approval.

Usage
-----
  python3 itvedas-brain/coo-agent.py                  # interactive REPL
  python3 itvedas-brain/coo-agent.py --once "What should we prioritize this week?"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from typing import Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

DEFAULT_MEMORY = BASE_DIR / "memory" / "coo_memory.json"
MAX_STORED_TURNS = 200       # how many turns are persisted to disk
MAX_PROMPT_TURNS = 16        # how many recent turns are sent to the model

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

INPUTS = {
    "repository": BASE_DIR / "memory" / "repository.json",
    "repository_knowledge": BASE_DIR / "repository_knowledge.json",
    "daily_plan": BASE_DIR / "state" / "daily-plan.json",
    "execution_plan": BASE_DIR / "state" / "execution-plan.json",
    "github_actions": BASE_DIR / "state" / "github-actions.json",
}

# Whitelisted actions the COO agent is allowed to run. Anything that only
# refreshes local state (rebuilds memory/*.json or brain/*.json) is safe
# to run on request. Anything that mutates an external system (creating
# real GitHub issues) requires an explicit /approve step.
ACTIONS: dict[str, dict[str, Any]] = {
    "scan-repository": {
        "description": "Re-scan the repository into itvedas-brain/memory/repository.json.",
        "command": [sys.executable, str(BASE_DIR / "repo-scanner.py")],
        "requires_approval": False,
    },
    "build-knowledge": {
        "description": "Rebuild itvedas-brain/knowledge/*.json and repository_knowledge.json.",
        "command": [sys.executable, str(BASE_DIR / "knowledge-builder.py")],
        "requires_approval": False,
    },
    "build-daily-plan": {
        "description": "Re-score opportunities into itvedas-brain/state/daily-plan.json.",
        "command": [sys.executable, str(BASE_DIR / "decision-engine.py")],
        "requires_approval": False,
    },
    "build-execution-plan": {
        "description": "Turn the daily plan into task briefs in itvedas-brain/state/execution-plan.json.",
        "command": [sys.executable, str(BASE_DIR / "execution-engine.py")],
        "requires_approval": False,
    },
    "build-github-plan": {
        "description": "Group tasks into issue/PR-ready groups in itvedas-brain/state/github-actions.json (no GitHub API calls).",
        "command": [sys.executable, str(BASE_DIR / "github-agent.py")],
        "requires_approval": False,
    },
    "create-github-issues": {
        "description": (
            "Actually create GitHub issues from itvedas-brain/state/github-actions.json via the GitHub API. "
            "Mutates a real, external, shared system - requires explicit approval."
        ),
        "command": [sys.executable, str(BASE_DIR / "github-agent.py"), "--create-issues"],
        "requires_approval": True,
    },
}

HELP_TEXT = """\
Commands:
  /help                     Show this message.
  /context                  Show the condensed business snapshot the agent is using.
  /recommend                List ranked recommended actions across all data sources.
  /run <action-id>          Run a non-mutating pipeline action immediately.
  /approve <action-id>      Run a mutating action (e.g. create-github-issues) after confirmation.
  /actions                  List every action the agent is allowed to run.
  /memory                   Show the recent decision log.
  /reset                    Clear conversation history (decision log is kept).
  /exit                     Quit.

Anything else is treated as a free-form business question (requires ANTHROPIC_API_KEY).
"""


def load_json(path: pathlib.Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json_atomic(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ─────────────────────────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────────────────────────

class Memory:
    """Persists conversation turns and the decision log across runs."""

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        data = load_json(path, None)
        if not isinstance(data, dict):
            data = {"schema_version": 1, "conversation_log": [], "decisions": []}
        self.data: dict[str, Any] = data
        self.data.setdefault("conversation_log", [])
        self.data.setdefault("decisions", [])

    def recent_turns(self, limit: int = MAX_PROMPT_TURNS) -> list[dict[str, str]]:
        return self.data["conversation_log"][-limit:]

    def add_turn(self, role: str, content: str) -> None:
        self.data["conversation_log"].append(
            {"timestamp": now_iso(), "role": role, "content": content}
        )
        self.data["conversation_log"] = self.data["conversation_log"][-MAX_STORED_TURNS:]
        self.save()

    def reset_conversation(self) -> None:
        self.data["conversation_log"] = []
        self.save()

    def log_decision(self, action_id: str, status: str, detail: str) -> None:
        self.data["decisions"].append(
            {"timestamp": now_iso(), "action": action_id, "status": status, "detail": detail}
        )
        self.data["decisions"] = self.data["decisions"][-MAX_STORED_TURNS:]
        self.save()

    def save(self) -> None:
        write_json_atomic(self.path, self.data)


# ─────────────────────────────────────────────────────────────────
# Context: read everything the brain pipeline has already produced
# ─────────────────────────────────────────────────────────────────

def load_context() -> dict[str, Any]:
    repository = load_json(INPUTS["repository"], {})
    repository_knowledge = load_json(INPUTS["repository_knowledge"], {})
    daily_plan = load_json(INPUTS["daily_plan"], {})
    execution_plan = load_json(INPUTS["execution_plan"], {})
    github_actions = load_json(INPUTS["github_actions"], {})

    return {
        "repository": repository,
        "repository_knowledge": repository_knowledge,
        "daily_plan": daily_plan,
        "execution_plan": execution_plan,
        "github_actions": github_actions,
    }


def format_context_markdown(context: dict[str, Any]) -> str:
    repository = context["repository"]
    knowledge = context["repository_knowledge"]
    plan = context["daily_plan"]
    execution = context["execution_plan"]
    github_actions = context["github_actions"]

    lines: list[str] = []

    lines.append("## Repository")
    summary = repository.get("summary", {})
    lines.append(
        f"- {summary.get('file_count', '?')} files / {summary.get('folder_count', '?')} folders, "
        f"generated {repository.get('generated_at', 'unknown')}"
    )

    lines.append("\n## Knowledge base")
    ks = knowledge.get("summary", {})
    lines.append(
        f"- {ks.get('courses', 0)} courses, {ks.get('career_paths', 0)} career paths, "
        f"{ks.get('certifications', 0)} certifications, {ks.get('technologies', 0)} technologies, "
        f"{ks.get('faqs', 0)} FAQs, {ks.get('relationships', 0)} cross-references"
    )

    lines.append("\n## Daily plan (itvedas-brain/state/daily-plan.json)")
    if plan:
        lines.append(f"- date: {plan.get('date')} | top priority: {plan.get('top_priority')} (score {plan.get('score')})")
        for opp in plan.get("opportunities", [])[:5]:
            lines.append(f"  - [{opp['score']}] {opp['title']} ({opp['type']})")
    else:
        lines.append("- not yet generated. Run decision-engine.py (action: build-daily-plan).")

    lines.append("\n## Execution plan (itvedas-brain/state/execution-plan.json)")
    queue = execution.get("execution_queue", [])
    lines.append(f"- {len(queue)} queued item(s)")
    for item in queue[:5]:
        lines.append(f"  - [{item.get('score')}] {item.get('priority')}: {len(item.get('tasks', []))} task(s)")

    lines.append("\n## GitHub action plan (itvedas-brain/state/github-actions.json)")
    gh_summary = github_actions.get("summary", {})
    lines.append(
        f"- {gh_summary.get('total_issues', 0)} issue(s) ready "
        f"across {sum(1 for c in github_actions.get('groups', {}).values() if c)} categories"
    )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Recommendations
# ─────────────────────────────────────────────────────────────────

def recommend_actions(context: dict[str, Any]) -> str:
    plan = context["daily_plan"]
    execution = context["execution_plan"]
    github_actions = context["github_actions"]

    if not plan.get("opportunities"):
        return (
            "No daily plan is available yet. Run `/run build-daily-plan` "
            "(after `/run build-knowledge`) to generate recommendations."
        )

    lines = ["Top recommended actions, ranked by score:\n"]

    for rank, opp in enumerate(plan.get("opportunities", [])[:5], start=1):
        lines.append(
            f"{rank}. [{opp['score']}] {opp['title']} - {opp['reason']} "
            f"(actions: {', '.join(opp['actions'])})"
        )

    issue_count = github_actions.get("summary", {}).get("total_issues", 0)
    if issue_count:
        lines.append(
            f"\n{issue_count} issue(s) are staged in itvedas-brain/state/github-actions.json and ready to file. "
            "Run `/approve create-github-issues` to create them on GitHub (requires GITHUB_TOKEN)."
        )
    elif execution.get("execution_queue"):
        lines.append(
            "\nitvedas-brain/state/github-actions.json has no staged issues yet - run `/run build-github-plan` first."
        )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# Action execution
# ─────────────────────────────────────────────────────────────────

def run_action(action_id: str, memory: Memory) -> str:
    action = ACTIONS.get(action_id)
    if action is None:
        known = ", ".join(sorted(ACTIONS))
        return f"Unknown action '{action_id}'. Known actions: {known}"

    result = subprocess.run(
        action["command"], cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=600
    )
    status = "success" if result.returncode == 0 else "failed"
    output = (result.stdout or "").strip() or (result.stderr or "").strip()
    memory.log_decision(action_id, status, output[-2000:])

    if result.returncode == 0:
        return f"Ran '{action_id}' successfully.\n{output}"
    return f"'{action_id}' failed (exit {result.returncode}).\n{output}"


def handle_run_command(action_id: str, memory: Memory) -> str:
    action = ACTIONS.get(action_id)
    if action is None:
        known = ", ".join(sorted(ACTIONS))
        return f"Unknown action '{action_id}'. Known actions: {known}"
    if action["requires_approval"]:
        return (
            f"'{action_id}' mutates an external system and requires explicit approval. "
            f"Use `/approve {action_id}` to run it."
        )
    return run_action(action_id, memory)


def handle_approve_command(action_id: str, memory: Memory) -> str:
    action = ACTIONS.get(action_id)
    if action is None:
        known = ", ".join(sorted(ACTIONS))
        return f"Unknown action '{action_id}'. Known actions: {known}"
    if not action["requires_approval"]:
        return f"'{action_id}' does not require approval - use `/run {action_id}` instead."
    return run_action(action_id, memory)


# ─────────────────────────────────────────────────────────────────
# Conversation (Anthropic API)
# ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """\
You are the ITVedas COO Agent: a conversational operations manager for the
ITVedas content platform. You answer business questions and recommend
actions using ONLY the data snapshot below, which was produced by the
ITVedas brain pipeline (repository scan, knowledge graph, and a scored
opportunity plan). Do not invent metrics
that aren't in the snapshot - say so plainly if something isn't covered.

When you recommend an action, name it using one of these action ids so
the human operator can run it: {action_ids}. Mutating actions
(currently: create-github-issues) require human approval via
`/approve <action-id>` before they execute - never imply they already ran.

Current data snapshot:

{context_markdown}
"""


def call_claude(system_prompt: str, messages: list[dict[str, str]]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set, so free-form business questions are not "
            "available. Slash commands (/context, /recommend, /run, /approve, /memory) "
            "still work without it."
        )

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(
            {
                "model": MODEL,
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": messages,
            }
        ).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"Anthropic API returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach the Anthropic API: {error.reason}") from error

    parts = payload.get("content", [])
    text = "".join(part.get("text", "") for part in parts if part.get("type") == "text")
    return text.strip() or "(no response)"


def answer_question(question: str, context: dict[str, Any], memory: Memory) -> str:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        action_ids=", ".join(sorted(ACTIONS)),
        context_markdown=format_context_markdown(context),
    )
    messages = [
        {"role": turn["role"], "content": turn["content"]}
        for turn in memory.recent_turns()
        if turn["role"] in ("user", "assistant")
    ]
    messages.append({"role": "user", "content": question})

    try:
        return call_claude(system_prompt, messages)
    except RuntimeError as error:
        return str(error)


# ─────────────────────────────────────────────────────────────────
# REPL
# ─────────────────────────────────────────────────────────────────

def dispatch(line: str, context: dict[str, Any], memory: Memory) -> tuple[str, bool]:
    """Returns (response, should_continue)."""
    stripped = line.strip()
    if not stripped:
        return "", True

    if stripped in ("/exit", "/quit"):
        return "Goodbye.", False
    if stripped == "/help":
        return HELP_TEXT, True
    if stripped == "/context":
        return format_context_markdown(context), True
    if stripped == "/recommend":
        return recommend_actions(context), True
    if stripped == "/actions":
        lines = ["Available actions:"]
        for action_id, action in sorted(ACTIONS.items()):
            gate = "approval required" if action["requires_approval"] else "runs on /run"
            lines.append(f"- {action_id} ({gate}): {action['description']}")
        return "\n".join(lines), True
    if stripped == "/memory":
        decisions = memory.data.get("decisions", [])[-10:]
        if not decisions:
            return "No decisions logged yet.", True
        lines = ["Recent decisions:"]
        for entry in decisions:
            lines.append(f"- [{entry['timestamp']}] {entry['action']}: {entry['status']}")
        return "\n".join(lines), True
    if stripped == "/reset":
        memory.reset_conversation()
        return "Conversation history cleared (decision log kept).", True
    if stripped.startswith("/run "):
        return handle_run_command(stripped[len("/run "):].strip(), memory), True
    if stripped.startswith("/approve "):
        return handle_approve_command(stripped[len("/approve "):].strip(), memory), True
    if stripped.startswith("/"):
        return f"Unknown command: {stripped}\n\n{HELP_TEXT}", True

    memory.add_turn("user", stripped)
    response = answer_question(stripped, context, memory)
    memory.add_turn("assistant", response)
    return response, True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ITVedas COO Agent - conversational manager for the brain pipeline.")
    parser.add_argument("--memory", type=pathlib.Path, default=DEFAULT_MEMORY)
    parser.add_argument("--once", help="Run a single message non-interactively and exit (also accepts slash commands).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    memory = Memory(args.memory)
    context = load_context()

    if args.once is not None:
        response, _ = dispatch(args.once, context, memory)
        print(response)
        return 0

    print("ITVedas COO Agent. Type /help for commands, /exit to quit.\n")
    while True:
        try:
            line = input("you> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        response, keep_going = dispatch(line, context, memory)
        if response:
            print(f"\ncoo> {response}\n")
        if not keep_going:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
