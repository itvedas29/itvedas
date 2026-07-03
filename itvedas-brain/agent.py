#!/usr/bin/env python3
"""
ITVedas Standalone AI Agent
─────────────────────────────
A fully autonomous AI agent with:
  • Web search + URL browsing
  • Full GitHub repo control
  • Article publishing via brain-bot
  • Extended thinking (Claude Sonnet)
  • Streaming chat UI (Flask + SSE)
  • All site skills: SEO, UI/UX, content strategy

Run:  python agent.py
Open: http://localhost:5000
"""

from __future__ import annotations

import base64
import html
import json
import math
import os
import pathlib
import re
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Generator

# ── optional deps ───────────────────────────────────────────────────────────
try:
    from flask import Flask, Response, request, stream_with_context
    FLASK_OK = True
except ImportError:
    FLASK_OK = False

try:
    from duckduckgo_search import DDGS
    DDG_OK = True
except ImportError:
    DDG_OK = False

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO     = os.environ.get("GITHUB_REPOSITORY", "itvedas29/itvedas")
GITHUB_BRANCH   = os.environ.get("GITHUB_BRANCH", "main")

MODEL = "claude-haiku-4-5-20251001"
MAX_ITERATIONS  = 20
PORT            = int(os.environ.get("PORT", 5001))
AUTO_INTERVAL   = int(os.environ.get("AUTO_INTERVAL", 900))  # seconds between autonomous runs (default 15 min)

ROOT      = pathlib.Path(__file__).resolve().parent.parent
BRAIN_DIR = pathlib.Path(__file__).resolve().parent
STATE_DIR = BRAIN_DIR / "state"
MEM_DIR   = BRAIN_DIR / "memory"

# ═══════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT  (all skills embedded)
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM = """You are the ITVedas AI Agent — an advanced autonomous assistant for the ITVedas IT education platform (itvedas.com).

## Your Identity
- You are the site's brain: you manage content, SEO, GitHub, publishing, and strategy
- You think deeply before acting, use multiple tools when needed, and always explain what you're doing
- You are direct, precise, and action-oriented

## Site Context
- itvedas.com — IT education platform covering Networking, Cloud, Security, DevOps, Databases, Linux, Hardware, Compliance, CVE Database
- 9 chapters ("Nine Pillars of IT Mastery"), ~171 seed articles being published by brain-bot
- Dark theme (#0A0A0F background, #FF6B35 orange accent)
- GitHub repo: itvedas29/itvedas (static site on GitHub Pages)
- Brain-bot publishes articles autonomously via GitHub Actions every 15 min

## Skill: SEO (30x-SEO)
- Target Featured Snippets: answer the question in first 50 words
- FAQ sections targeting "People Also Ask" (minimum 4 Q&As)
- Title formula: [Primary Keyword]: [Benefit/Number] [Modifier] (60 chars max)
- Meta description: 155 chars, active voice, includes CTA
- Schema markup: Article + FAQ + HowTo where applicable
- Internal linking: 3-5 contextual links per article
- Target: 0-5 word difficulty score keywords with 1k+ monthly searches
- Long-tail clusters: one pillar page + 8-12 supporting articles per chapter

## Skill: Content Writing (Anti-AI Detection)
Forbidden words: delve, tapestry, multifaceted, nuanced, leverage, paradigm, synergy,
  holistic, robust, streamline, cutting-edge, revolutionize, transformative, game-changing,
  groundbreaking, innovative, comprehensive, meticulous, crucial, pivotal
Forbidden openers: "In today's digital landscape", "In the ever-evolving", "As we navigate"
Rules: Start with a hook fact or question. Vary sentence length. Use contractions. Be direct.

## Skill: UI/UX Design
- Dark theme primary (#0A0A0F bg, #12121A surface, #1A1A26 surface2)
- Orange accent: #FF6B35 (use sparingly — calls to action and highlights only)
- Typography: Inter for body, monospace for code
- Cards: 1px border rgba(255,255,255,0.08), 16px radius, subtle glow on hover
- Minimum touch targets: 44×44px
- No emoji icons — use SVG (Heroicons/Lucide)
- Text contrast: 4.5:1 minimum

## Skill: Topic Cluster Architecture
- Each chapter = 1 pillar page + supporting articles
- Internal link structure: hub-and-spoke
- Pillar page targets broad keyword, spokes target long-tail
- Breadcrumbs on every article page

## Skill: GitHub Operations
You can read/write files, manage PRs, trigger workflows, publish articles,
check bot status, search code, create branches — use your tools freely.

## Behavior Rules
1. Always search the web before answering factual questions that need current data
2. When asked to do something on the site, do it — don't just describe how
3. Think step by step for complex tasks (you have extended thinking)
4. Use multiple tools in sequence when needed
5. Report clearly what you did and what the result was
"""

# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
TOOLS = [
    {
        "name": "web_search",
        "description": "Search the internet for current information. Use this for any factual question that needs up-to-date data, recent news, or external knowledge.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Number of results (default 8)", "default": 8},
            },
            "required": ["query"],
        },
    },
    {
        "name": "browse_url",
        "description": "Fetch and read the content of any webpage. Use this to read articles, documentation, GitHub pages, or any URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to fetch"},
                "extract_text": {"type": "boolean", "description": "Extract clean text only (default true)", "default": True},
            },
            "required": ["url"],
        },
    },
    {
        "name": "github_read_file",
        "description": "Read any file from the itvedas GitHub repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root (e.g. index.html)"},
                "branch": {"type": "string", "description": "Branch name (default: main)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "github_write_file",
        "description": "Create or update any file in the itvedas GitHub repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root"},
                "content": {"type": "string", "description": "Full file content"},
                "message": {"type": "string", "description": "Commit message"},
                "branch": {"type": "string", "description": "Branch name (default: main)"},
            },
            "required": ["path", "content", "message"],
        },
    },
    {
        "name": "github_delete_file",
        "description": "Delete a file from the itvedas GitHub repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to delete"},
                "message": {"type": "string", "description": "Commit message"},
            },
            "required": ["path", "message"],
        },
    },
    {
        "name": "github_list_files",
        "description": "List files in a directory of the itvedas repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: root)", "default": ""},
                "branch": {"type": "string", "description": "Branch (default: main)"},
            },
        },
    },
    {
        "name": "github_search_code",
        "description": "Search code in the itvedas repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (code or text to find)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "github_list_issues",
        "description": "List GitHub issues for the itvedas repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "description": "open, closed, or all (default: open)"},
                "label": {"type": "string", "description": "Filter by label"},
            },
        },
    },
    {
        "name": "github_create_issue",
        "description": "Create a new GitHub issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],
        },
    },
    {
        "name": "github_list_prs",
        "description": "List pull requests in the itvedas repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "description": "open, closed, or all"},
            },
        },
    },
    {
        "name": "github_trigger_workflow",
        "description": "Trigger a GitHub Actions workflow manually.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_file": {"type": "string", "description": "Workflow filename (e.g. brain-bot.yml)"},
                "inputs": {"type": "object", "description": "Optional workflow inputs"},
                "branch": {"type": "string", "description": "Branch to run on (default: main)"},
            },
            "required": ["workflow_file"],
        },
    },
    {
        "name": "github_list_workflow_runs",
        "description": "List recent workflow runs to check bot status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_file": {"type": "string", "description": "Filter by workflow file (optional)"},
                "limit": {"type": "integer", "description": "Max results (default 10)"},
            },
        },
    },
    {
        "name": "get_brain_status",
        "description": "Get the current status of the brain-bot: articles published, seeds remaining, last run, memory state.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "publish_article",
        "description": "Request the brain-bot to publish a specific article topic immediately.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The article topic to publish"},
                "chapter": {"type": "string", "description": "The chapter it belongs to (optional)"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "run_python",
        "description": "Execute Python code for calculations, data processing, or analysis. Returns stdout output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
            },
            "required": ["code"],
        },
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
#  GITHUB HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _gh_headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "ITVedasAgent/1.0",
    }

def _gh(method: str, path: str, body: dict | None = None, params: dict | None = None) -> Any:
    url = f"https://api.github.com{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_gh_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub {method} {path} → {e.code}: {e.read().decode()}") from e

# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════
def tool_web_search(query: str, max_results: int = 8) -> str:
    if not DDG_OK:
        return "web_search unavailable — install: pip install duckduckgo-search"
    try:
        results = []
        with DDGS() as ddg:
            for r in ddg.text(query, max_results=max_results):
                results.append(f"**{r['title']}**\n{r['href']}\n{r['body']}\n")
        if not results:
            return "No results found."
        return f"Search results for: {query}\n\n" + "\n---\n".join(results)
    except Exception as e:
        return f"Search error: {e}"

def tool_browse_url(url: str, extract_text: bool = True) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ITVedasAgent"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="replace")
        if extract_text and BS4_OK:
            soup = BeautifulSoup(raw, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [l for l in text.splitlines() if len(l.strip()) > 20]
            return "\n".join(lines[:300])
        return raw[:8000]
    except Exception as e:
        return f"Browse error: {e}"

def tool_github_read_file(path: str, branch: str = "main") -> str:
    try:
        data = _gh("GET", f"/repos/{GITHUB_REPO}/contents/{path}", params={"ref": branch})
        if isinstance(data, list):
            return "\n".join(f.get("name", "") for f in data)
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return f"File: {path}\n---\n{content}"
    except Exception as e:
        return f"Error reading {path}: {e}"

def tool_github_write_file(path: str, content: str, message: str, branch: str = "main") -> str:
    try:
        encoded = base64.b64encode(content.encode()).decode()
        body: dict = {"message": message, "content": encoded, "branch": branch}
        try:
            existing = _gh("GET", f"/repos/{GITHUB_REPO}/contents/{path}", params={"ref": branch})
            if isinstance(existing, dict):
                body["sha"] = existing["sha"]
        except Exception:
            pass
        _gh("PUT", f"/repos/{GITHUB_REPO}/contents/{path}", body)
        return f"✓ Written: {path} (branch: {branch})"
    except Exception as e:
        return f"Error writing {path}: {e}"

def tool_github_delete_file(path: str, message: str) -> str:
    try:
        existing = _gh("GET", f"/repos/{GITHUB_REPO}/contents/{path}")
        if not isinstance(existing, dict):
            return f"File not found: {path}"
        _gh("DELETE", f"/repos/{GITHUB_REPO}/contents/{path}", {
            "message": message, "sha": existing["sha"]
        })
        return f"✓ Deleted: {path}"
    except Exception as e:
        return f"Error deleting {path}: {e}"

def tool_github_list_files(path: str = "", branch: str = "main") -> str:
    try:
        data = _gh("GET", f"/repos/{GITHUB_REPO}/contents/{path}", params={"ref": branch})
        if isinstance(data, list):
            lines = []
            for f in data:
                icon = "📁" if f["type"] == "dir" else "📄"
                lines.append(f"{icon} {f['name']}")
            return "\n".join(lines)
        return str(data)
    except Exception as e:
        return f"Error: {e}"

def tool_github_search_code(query: str) -> str:
    try:
        data = _gh("GET", "/search/code", params={"q": f"{query} repo:{GITHUB_REPO}", "per_page": 10})
        items = data.get("items", [])
        if not items:
            return "No matches found."
        return "\n".join(f"• {i['path']} — {i['html_url']}" for i in items)
    except Exception as e:
        return f"Search error: {e}"

def tool_github_list_issues(state: str = "open", label: str = "") -> str:
    try:
        params: dict = {"state": state, "per_page": 20}
        if label:
            params["labels"] = label
        data = _gh("GET", f"/repos/{GITHUB_REPO}/issues", params=params)
        if not data:
            return "No issues found."
        return "\n".join(f"#{i['number']} [{i['state']}] {i['title']}" for i in data)
    except Exception as e:
        return f"Error: {e}"

def tool_github_create_issue(title: str, body: str = "", labels: list | None = None) -> str:
    try:
        payload: dict = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        data = _gh("POST", f"/repos/{GITHUB_REPO}/issues", payload)
        return f"✓ Issue #{data['number']} created: {data['html_url']}"
    except Exception as e:
        return f"Error: {e}"

def tool_github_list_prs(state: str = "open") -> str:
    try:
        data = _gh("GET", f"/repos/{GITHUB_REPO}/pulls", params={"state": state, "per_page": 20})
        if not data:
            return "No pull requests found."
        return "\n".join(f"#{p['number']} [{p['state']}] {p['title']} (base: {p['base']['ref']})" for p in data)
    except Exception as e:
        return f"Error: {e}"

def tool_github_trigger_workflow(workflow_file: str, inputs: dict | None = None, branch: str = "main") -> str:
    try:
        _gh("POST", f"/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches", {
            "ref": branch,
            "inputs": inputs or {},
        })
        return f"✓ Triggered {workflow_file} on branch {branch}"
    except Exception as e:
        return f"Error triggering workflow: {e}"

def tool_github_list_workflow_runs(workflow_file: str = "", limit: int = 10) -> str:
    try:
        params: dict = {"per_page": limit}
        path = f"/repos/{GITHUB_REPO}/actions/runs"
        if workflow_file:
            path = f"/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/runs"
        data = _gh("GET", path, params=params)
        runs = data.get("workflow_runs", [])
        if not runs:
            return "No runs found."
        lines = []
        for r in runs:
            lines.append(f"#{r['run_number']} {r['name']} — {r['status']}/{r['conclusion']} — {r['created_at'][:16]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

def tool_get_brain_status() -> str:
    try:
        lines = ["## Brain-Bot Status\n"]
        try:
            d = _gh("GET", f"/repos/{GITHUB_REPO}/contents/itvedas-brain/memory/brain_memory.json")
            mem = json.loads(base64.b64decode(d["content"]).decode())
            stats = mem.get("stats", {})
            published = mem.get("published_articles", mem.get("published_topics", []))
            done = mem.get("done_topics", [])
            last_run = stats.get("last_run", "?")
            lines.append(f"Last run: {last_run}")
            lines.append(f"Total published: {len(published)} articles")
            lines.append(f"Done topics: {len(done)}")
            lines.append(f"Failed topics: {len(mem.get('failed_topics', []))}")
            lines.append(f"Autonomous runs: {stats.get('runs', '?')}")
            if published:
                last = published[-1]
                title = last.get("title", last) if isinstance(last, dict) else last
                lines.append(f"Latest article: {title}")
        except Exception as e:
            lines.append(f"Memory read error: {e}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

def tool_publish_article(topic: str, chapter: str = "") -> str:
    try:
        payload = {"topic": topic, "chapter": chapter, "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        content = json.dumps(payload, indent=2)
        write_res = tool_github_write_file(
            "itvedas-brain/state/requested_topic.json",
            content,
            f"agent: request article — {topic}",
        )
        trig_res = tool_github_trigger_workflow("brain-bot.yml", {"bot_mode": "article"})
        return f"{write_res}\n{trig_res}\nArticle on '{topic}' queued — brain-bot will publish it within minutes."
    except Exception as e:
        return f"Error: {e}"

def tool_run_python(code: str) -> str:
    import subprocess, sys
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=15
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if err:
            return f"STDOUT:\n{out}\nSTDERR:\n{err}"
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return "Timeout: code ran >15s"
    except Exception as e:
        return f"Error: {e}"

# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════
def dispatch_tool(name: str, args: dict) -> str:
    try:
        if name == "web_search":         return tool_web_search(args["query"], args.get("max_results", 8))
        if name == "browse_url":         return tool_browse_url(args["url"], args.get("extract_text", True))
        if name == "github_read_file":   return tool_github_read_file(args["path"], args.get("branch", "main"))
        if name == "github_write_file":  return tool_github_write_file(args["path"], args["content"], args["message"], args.get("branch", "main"))
        if name == "github_delete_file": return tool_github_delete_file(args["path"], args["message"])
        if name == "github_list_files":  return tool_github_list_files(args.get("path", ""), args.get("branch", "main"))
        if name == "github_search_code": return tool_github_search_code(args["query"])
        if name == "github_list_issues": return tool_github_list_issues(args.get("state", "open"), args.get("label", ""))
        if name == "github_create_issue":return tool_github_create_issue(args["title"], args.get("body", ""), args.get("labels"))
        if name == "github_list_prs":    return tool_github_list_prs(args.get("state", "open"))
        if name == "github_trigger_workflow": return tool_github_trigger_workflow(args["workflow_file"], args.get("inputs"), args.get("branch", "main"))
        if name == "github_list_workflow_runs": return tool_github_list_workflow_runs(args.get("workflow_file", ""), args.get("limit", 10))
        if name == "get_brain_status":   return tool_get_brain_status()
        if name == "publish_article":    return tool_publish_article(args["topic"], args.get("chapter", ""))
        if name == "run_python":         return tool_run_python(args["code"])
        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error ({name}): {e}\n{traceback.format_exc()}"

# ═══════════════════════════════════════════════════════════════════════════════
#  ANTHROPIC CLIENT (raw HTTP — no SDK dependency)
# ═══════════════════════════════════════════════════════════════════════════════
def _claude(messages: list) -> Any:
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": SYSTEM,
        "tools": TOOLS,
        "messages": messages,
    }
    body = json.dumps(payload).encode()
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body, headers=headers, method="POST"
    )
    return urllib.request.urlopen(req, timeout=60)

def call_claude_full(messages: list) -> dict:
    with _claude(messages) as r:
        return json.loads(r.read())

# ═══════════════════════════════════════════════════════════════════════════════
#  AGENTIC LOOP (streaming SSE version)
# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL DISPATCHER — handles requests locally without calling Claude
# ═══════════════════════════════════════════════════════════════════════════════
def _skill_dispatch(msg: str) -> str | None:
    """
    Try to handle the message with a built-in skill.
    Returns response text if handled, None if Claude should take over.
    """
    m = msg.lower().strip()

    # STATUS
    if any(k in m for k in ["status", "brain bot", "brain-bot", "how many article", "articles published", "heartbeat"]):
        return tool_get_brain_status()

    # LIST ARTICLES
    if any(k in m for k in ["list article", "show article", "all article", "published article"]):
        try:
            files = tool_github_list_files("articles")
            count = len([l for l in files.splitlines() if l.strip().startswith("📄")])
            return f"## Published Articles\n\n{files}\n\n**Total: {count} articles published.**"
        except Exception as e:
            return f"Error listing articles: {e}"

    # PUBLISH NOW
    if any(k in m for k in ["publish now", "publish article", "write article", "trigger publish", "run bot"]):
        topic = msg
        for strip in ["publish now", "publish article", "write article", "publish", "write"]:
            topic = topic.lower().replace(strip, "").strip()
        if len(topic) < 4:
            topic = "next pending topic"
        return tool_publish_article(topic)

    # WORKFLOW RUNS
    if any(k in m for k in ["workflow", "actions", "runs", "ci", "pipeline"]):
        return tool_github_list_workflow_runs(limit=10)

    # LIST FILES
    if m.startswith("list files") or m.startswith("show files"):
        path = m.replace("list files", "").replace("show files", "").strip() or ""
        return tool_github_list_files(path)

    # READ FILE
    if m.startswith("read ") and ("/" in m or "." in m):
        path = msg.strip()[5:].strip()
        return tool_github_read_file(path)

    # OPEN ISSUES
    if any(k in m for k in ["list issue", "show issue", "open issue", "github issue"]):
        return tool_github_list_issues()

    # OPEN PRS
    if any(k in m for k in ["pull request", "list pr", "open pr", "show pr"]):
        return tool_github_list_prs()

    # SEARCH WEB
    if m.startswith("search ") or m.startswith("search the web"):
        query = msg[7:].strip()
        return tool_web_search(query)

    # SITE INFO
    if any(k in m for k in ["what is itvedas", "about the site", "site info", "tell me about"]):
        return (
            "## ITVedas\n\n"
            "**itvedas.com** is an IT education platform covering 9 chapters:\n"
            "Networking, Cloud, Security, DevOps, Databases, Linux, Hardware, Compliance, CVE Database.\n\n"
            "- Static site hosted on GitHub Pages (repo: itvedas29/itvedas)\n"
            "- Dark theme (#0A0A0F bg, #FF6B35 orange accent)\n"
            "- VPS agent (this bot) publishes articles every 15 minutes autonomously\n"
            "- 171 seed articles in the pipeline"
        )

    # HELP
    if any(k in m for k in ["help", "what can you do", "commands", "capabilities"]):
        return (
            "## What I can do\n\n"
            "**Without Claude (instant):**\n"
            "- `status` — brain-bot status, articles published\n"
            "- `list articles` — all published articles\n"
            "- `publish [topic]` — queue an article for publishing\n"
            "- `list files [path]` — browse repo files\n"
            "- `read [path]` — read any repo file\n"
            "- `list issues` / `list prs` — GitHub activity\n"
            "- `search [query]` — web search\n"
            "- `workflow runs` — recent CI runs\n\n"
            "**With Claude (complex tasks):**\n"
            "- Write full articles from scratch\n"
            "- Analyse and improve site content\n"
            "- Answer technical IT questions\n"
            "- Plan content strategy\n"
            "- Debug and fix code"
        )

    return None  # Claude handles it


# ═══════════════════════════════════════════════════════════════════════════════
def agentic_loop_stream(user_message: str, history: list) -> Generator[str, None, None]:
    """
    Yields SSE-formatted strings:
      data: {"type":"thinking","text":"..."}
      data: {"type":"text","text":"..."}
      data: {"type":"tool_start","name":"...","input":{}}
      data: {"type":"tool_result","name":"...","result":"..."}
      data: {"type":"done"}
    """
    def emit(obj: dict) -> str:
        return f"data: {json.dumps(obj)}\n\n"

    messages = list(history) + [{"role": "user", "content": user_message}]
    iterations = 0

    while iterations < MAX_ITERATIONS:
        iterations += 1
        try:
            response = call_claude_full(messages)
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            yield emit({"type": "text", "text": f"\n\n❌ Claude API error: {e.code}\n{err}"})
            yield emit({"type": "done"})
            return
        except Exception as e:
            yield emit({"type": "text", "text": f"\n\n❌ Error: {e}"})
            yield emit({"type": "done"})
            return

        content = response.get("content", [])
        stop_reason = response.get("stop_reason", "end_turn")

        # Collect assistant content for history
        assistant_content = []
        tool_uses = []

        for block in content:
            btype = block.get("type")
            if btype == "thinking":
                thinking_text = block.get("thinking", "")
                if thinking_text:
                    yield emit({"type": "thinking", "text": thinking_text})
                assistant_content.append(block)
            elif btype == "text":
                text = block.get("text", "")
                if text:
                    yield emit({"type": "text", "text": text})
                assistant_content.append(block)
            elif btype == "tool_use":
                tool_uses.append(block)
                assistant_content.append(block)

        # Append assistant turn to history
        messages.append({"role": "assistant", "content": assistant_content})

        if stop_reason == "end_turn" or not tool_uses:
            break

        # Execute tools
        tool_results = []
        for tu in tool_uses:
            name = tu.get("name", "")
            args = tu.get("input", {})
            yield emit({"type": "tool_start", "name": name, "input": args})
            result = dispatch_tool(name, args)
            yield emit({"type": "tool_result", "name": name, "result": result[:3000]})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    yield emit({"type": "done"})

# ═══════════════════════════════════════════════════════════════════════════════
#  FLASK WEB APP
# ═══════════════════════════════════════════════════════════════════════════════
if FLASK_OK:
    import hashlib, secrets
    from flask import Flask, Response, request, stream_with_context, session, redirect, url_for

    app = Flask(__name__, static_folder=None)
    app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(32))

    # Password protection — set AGENT_PASSWORD env var (defaults to "itvedas")
    AGENT_PASSWORD = os.environ.get("AGENT_PASSWORD", "itvedas")

    def _check_auth() -> bool:
        return session.get("authed") is True

    # In-memory conversation history per session (single user)
    _history: list = []

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = ""
        if request.method == "POST":
            pw = request.form.get("password", "")
            if pw == AGENT_PASSWORD:
                session["authed"] = True
                return redirect("/")
            error = "Wrong password"
        err_html = f'<div class="error">{error}</div>' if error else ""
        return Response(LOGIN_HTML.replace("{{ERROR}}", err_html), mimetype="text/html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @app.route("/")
    def index():
        if not _check_auth():
            return redirect("/login")
        return Response(CHAT_HTML, mimetype="text/html")

    @app.route("/chat", methods=["POST"])
    def chat():
        if not _check_auth():
            return {"error": "unauthorized"}, 401
        global _history
        data = request.get_json()
        msg = (data or {}).get("message", "").strip()
        if not msg:
            return Response("data: {\"type\":\"done\"}\n\n", mimetype="text/event-stream")

        def generate_and_track():
            global _history
            # Try built-in skills first — no Claude API call needed
            skill_result = _skill_dispatch(msg)
            if skill_result is not None:
                yield f"data: {json.dumps({'type': 'text', 'text': skill_result})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                _history.append({"role": "user", "content": msg})
                _history.append({"role": "assistant", "content": skill_result})
                if len(_history) > 40:
                    _history = _history[-40:]
                return
            # Fall back to Claude for complex requests
            assistant_text = ""
            for chunk in agentic_loop_stream(msg, _history):
                try:
                    obj = json.loads(chunk.replace("data: ", "").strip())
                    if obj.get("type") == "text":
                        assistant_text += obj.get("text", "")
                except Exception:
                    pass
                yield chunk
            if assistant_text:
                _history.append({"role": "user", "content": msg})
                _history.append({"role": "assistant", "content": assistant_text})
                if len(_history) > 40:
                    _history = _history[-40:]

        return Response(
            stream_with_context(generate_and_track()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.route("/clear", methods=["POST"])
    def clear():
        if not _check_auth():
            return {"error": "unauthorized"}, 401
        global _history
        _history = []
        return {"ok": True}

    @app.route("/auto-log")
    def auto_log():
        if not _check_auth():
            return redirect("/login")
        entries = list(reversed(_auto_log[-20:]))
        rows = "".join(
            f'<div style="border-bottom:1px solid #1A1A26;padding:14px 0"><div style="font-size:11px;color:#8888A8;margin-bottom:6px">{e["time"]}</div>'
            f'<div style="font-size:13px;color:#E8E8F0;line-height:1.6">{html.escape(e["summary"])}</div></div>'
            for e in entries
        ) or '<div style="color:#8888A8;padding:20px 0">No autonomous runs yet — first run starts 30s after startup.</div>'
        page = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Auto Log — ITVedas Agent</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0A0A0F;color:#E8E8F0;font-family:Inter,sans-serif;padding:32px;max-width:860px;margin:0 auto}}
h1{{font-size:20px;font-weight:700;margin-bottom:4px}}p{{color:#8888A8;font-size:13px;margin-bottom:24px}}
a{{color:#FF6B35;text-decoration:none;font-size:13px}}</style></head>
<body><h1>Autonomous Agent Log</h1><p>Last {len(entries)} runs · refreshes manually · <a href="/">← Back to chat</a></p>{rows}</body></html>"""
        return Response(page, mimetype="text/html")

# ═══════════════════════════════════════════════════════════════════════════════
#  CHAT UI HTML
# ═══════════════════════════════════════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ITVedas Agent — Login</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;background:#0A0A0F;display:flex;align-items:center;justify-content:center;font-family:'Inter',-apple-system,sans-serif}
.card{background:#12121A;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:40px;width:360px}
.logo{display:flex;align-items:center;gap:12px;margin-bottom:28px}
.logo-icon{width:44px;height:44px;background:#FF6B35;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px}
h1{font-size:20px;font-weight:700;color:#E8E8F0}
p{font-size:13px;color:#8888A8;margin-top:4px}
label{display:block;font-size:12px;color:#8888A8;margin:20px 0 6px}
input{width:100%;background:#1A1A26;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px 14px;color:#E8E8F0;font-size:14px;outline:none}
input:focus{border-color:rgba(255,107,53,.5)}
.error{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:8px;padding:8px 12px;font-size:13px;color:#FCA5A5;margin-top:12px}
button{width:100%;background:#FF6B35;border:none;border-radius:10px;padding:13px;color:white;font-size:14px;font-weight:600;cursor:pointer;margin-top:16px}
button:hover{opacity:.9}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">⚡</div>
    <div>
      <h1>ITVedas Agent</h1>
      <p>Private AI — site owner only</p>
    </div>
  </div>
  <form method="POST">
    <label>Password</label>
    <input type="password" name="password" placeholder="Enter password" autofocus autocomplete="current-password">
    {{ERROR}}
    <button type="submit">Sign In</button>
  </form>
</div>
</body>
</html>"""

CHAT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ITVedas AI Agent</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0A0A0F;
  --s1:#12121A;
  --s2:#1A1A26;
  --s3:#22223A;
  --border:rgba(255,255,255,.08);
  --accent:#FF6B35;
  --accent2:#FF8C5A;
  --text:#E8E8F0;
  --muted:#8888A8;
  --radius:16px;
  --thinking-bg:#0D1117;
  --thinking-border:#2A3A2A;
  --thinking-text:#7DBB7D;
  --tool-bg:#0A0D1A;
  --tool-border:#1A2A3A;
  --tool-accent:#38BDF8;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;overflow:hidden}
code,pre,kbd{font-family:'JetBrains Mono',monospace}

/* Layout */
#app{display:grid;grid-template-columns:260px 1fr;height:100vh}

/* Sidebar */
#sidebar{background:var(--s1);border-right:1px solid var(--border);display:flex;flex-direction:column;padding:20px 16px;gap:8px;overflow:hidden}
.logo{display:flex;align-items:center;gap:10px;padding:4px 0 16px;border-bottom:1px solid var(--border);margin-bottom:8px}
.logo-icon{width:36px;height:36px;background:var(--accent);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.logo-text{font-weight:700;font-size:15px;color:var(--text)}
.logo-sub{font-size:11px;color:var(--muted)}
.new-chat-btn{background:var(--accent);border:none;border-radius:10px;padding:10px 14px;color:white;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:8px;width:100%}
.new-chat-btn:hover{background:var(--accent2)}
.sidebar-section{font-size:11px;color:var(--muted);font-weight:600;letter-spacing:.05em;text-transform:uppercase;margin-top:12px;margin-bottom:4px;padding:0 4px}
.quick-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;cursor:pointer;font-size:13px;color:var(--muted);transition:all .15s;border:none;background:none;width:100%;text-align:left}
.quick-item:hover{background:var(--s2);color:var(--text)}
.quick-item .qi-icon{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.sidebar-footer{margin-top:auto;padding-top:12px;border-top:1px solid var(--border);font-size:11px;color:var(--muted);line-height:1.6}
.model-badge{display:inline-flex;align-items:center;gap:4px;background:var(--s2);border:1px solid var(--border);border-radius:6px;padding:3px 8px;font-size:11px;color:var(--muted);margin-top:6px}
.model-dot{width:6px;height:6px;border-radius:50%;background:#22C55E;box-shadow:0 0 4px #22C55E}

/* Main */
#main{display:flex;flex-direction:column;overflow:hidden}

/* Header */
#header{display:flex;align-items:center;gap:12px;padding:14px 24px;border-bottom:1px solid var(--border);flex-shrink:0}
#header h2{font-size:15px;font-weight:600}
#header p{font-size:12px;color:var(--muted)}
#thinking-indicator{margin-left:auto;display:none;align-items:center;gap:6px;font-size:12px;color:var(--thinking-text);background:var(--thinking-bg);border:1px solid var(--thinking-border);border-radius:20px;padding:4px 12px}
#thinking-indicator.active{display:flex}
.spin{animation:spin 1.4s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}

/* Messages */
#messages{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:20px;scroll-behavior:smooth}
#messages::-webkit-scrollbar{width:4px}
#messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}

/* Message rows */
#messages{display:flex;flex-direction:column;align-items:stretch}
.msg-row{display:flex;gap:12px;animation:slidein .2s ease;max-width:780px;width:fit-content}
@keyframes slidein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg-row.user{flex-direction:row-reverse;align-self:flex-end;margin-left:auto}
.msg-row.assistant{align-self:flex-start}
.avatar{width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;margin-top:2px}
.msg-row.user .avatar{background:rgba(100,100,220,.25);border:1px solid rgba(100,100,220,.3)}
.msg-row.assistant .avatar{background:rgba(255,107,53,.15);border:1px solid rgba(255,107,53,.25)}
.msg-body{min-width:0;max-width:680px}
.msg-row.user .msg-body{max-width:580px}
.bubble{padding:12px 16px;border-radius:var(--radius);font-size:14px;line-height:1.7;white-space:pre-wrap;word-break:break-word}
.msg-row.user .bubble{background:rgba(255,107,53,.15);border:1px solid rgba(255,107,53,.25);border-bottom-right-radius:4px}
.msg-row.assistant .bubble{background:var(--s1);border:1px solid var(--border);border-bottom-left-radius:4px}
.msg-meta{font-size:11px;color:var(--muted);margin-top:5px;padding:0 2px}
.msg-row.user .msg-meta{text-align:right}

/* Thinking block */
.thinking-block{background:var(--thinking-bg);border:1px solid var(--thinking-border);border-radius:12px;padding:12px 16px;margin-bottom:8px;overflow:hidden;transition:max-height .3s}
.thinking-header{display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;font-size:12px;color:var(--thinking-text);font-weight:500}
.thinking-header svg{flex-shrink:0}
.thinking-chevron{margin-left:auto;transition:transform .2s}
.thinking-block.collapsed .thinking-chevron{transform:rotate(-90deg)}
.thinking-content{font-size:12px;color:var(--thinking-text);line-height:1.6;margin-top:10px;font-family:'JetBrains Mono',monospace;white-space:pre-wrap;word-break:break-word;opacity:.85}
.thinking-block.collapsed .thinking-content{display:none}

/* Tool call block */
.tool-block{background:var(--tool-bg);border:1px solid var(--tool-border);border-radius:10px;padding:10px 14px;margin-bottom:8px;font-size:12px}
.tool-header{display:flex;align-items:center;gap:8px;color:var(--tool-accent);font-weight:500}
.tool-name{font-family:'JetBrains Mono',monospace;background:rgba(56,189,248,.1);padding:2px 8px;border-radius:5px}
.tool-args{color:var(--muted);margin-top:4px;font-family:'JetBrains Mono',monospace;white-space:pre-wrap;word-break:break-word;font-size:11px;max-height:80px;overflow:auto}
.tool-result{color:#94A3B8;margin-top:8px;padding-top:8px;border-top:1px solid var(--tool-border);font-family:'JetBrains Mono',monospace;font-size:11px;white-space:pre-wrap;word-break:break-word;max-height:150px;overflow:auto}
.tool-status{font-size:10px;margin-left:auto;padding:2px 6px;border-radius:4px;background:rgba(56,189,248,.1);color:var(--tool-accent)}

/* Markdown rendering */
.bubble h1,.bubble h2,.bubble h3{font-weight:600;margin:12px 0 6px;line-height:1.3}
.bubble h1{font-size:18px}.bubble h2{font-size:16px}.bubble h3{font-size:14px}
.bubble p{margin:6px 0}
.bubble ul,.bubble ol{margin:6px 0 6px 20px}
.bubble li{margin:3px 0}
.bubble code{background:rgba(255,255,255,.1);padding:2px 6px;border-radius:5px;font-size:12px}
.bubble pre{background:rgba(0,0,0,.4);border:1px solid var(--border);border-radius:10px;padding:14px;overflow-x:auto;margin:8px 0}
.bubble pre code{background:none;padding:0;font-size:12px}
.bubble strong{font-weight:600;color:var(--text)}
.bubble em{font-style:italic;color:var(--muted)}
.bubble a{color:var(--accent);text-decoration:none}
.bubble a:hover{text-decoration:underline}
.bubble blockquote{border-left:3px solid var(--accent);padding-left:12px;color:var(--muted);margin:8px 0}
.bubble hr{border:none;border-top:1px solid var(--border);margin:12px 0}
.bubble table{border-collapse:collapse;width:100%;margin:8px 0;font-size:13px}
.bubble th,.bubble td{border:1px solid var(--border);padding:6px 10px;text-align:left}
.bubble th{background:var(--s2);font-weight:600}

/* Typing cursor */
.cursor{display:inline-block;width:2px;height:16px;background:var(--accent);margin-left:2px;vertical-align:middle;animation:blink .8s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

/* Input */
#input-area{padding:16px 24px 24px;border-top:1px solid var(--border);flex-shrink:0}
#input-wrap{display:flex;gap:10px;background:var(--s2);border:1px solid var(--border);border-radius:16px;padding:12px 12px 12px 16px;align-items:flex-end;transition:border-color .2s}
#input-wrap:focus-within{border-color:rgba(255,107,53,.4)}
#chat-input{flex:1;background:none;border:none;color:var(--text);font-size:14px;resize:none;outline:none;max-height:200px;line-height:1.6;font-family:'Inter',sans-serif}
#chat-input::placeholder{color:var(--muted)}
#send-btn{background:var(--accent);border:none;border-radius:10px;width:40px;height:40px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:opacity .2s}
#send-btn:hover{opacity:.85}
#send-btn:disabled{opacity:.3;cursor:not-allowed}
.input-hint{font-size:11px;color:var(--muted);text-align:center;margin-top:8px}

/* Welcome */
#welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;gap:24px;padding:40px;text-align:center}
#welcome h2{font-size:28px;font-weight:700;background:linear-gradient(135deg,var(--text),var(--muted));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
#welcome p{font-size:15px;color:var(--muted);max-width:480px;line-height:1.7}
.suggestion-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:560px;width:100%}
.suggestion{background:var(--s1);border:1px solid var(--border);border-radius:12px;padding:14px 16px;cursor:pointer;text-align:left;transition:all .2s}
.suggestion:hover{border-color:rgba(255,107,53,.4);background:var(--s2)}
.suggestion .s-icon{font-size:20px;margin-bottom:6px}
.suggestion .s-title{font-size:13px;font-weight:600;margin-bottom:3px}
.suggestion .s-desc{font-size:12px;color:var(--muted)}

@media(max-width:700px){
  #app{grid-template-columns:1fr}
  #sidebar{display:none}
  .suggestion-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div id="app">
  <!-- Sidebar -->
  <div id="sidebar">
    <div class="logo">
      <div class="logo-icon">⚡</div>
      <div>
        <div class="logo-text">ITVedas Agent</div>
        <div class="logo-sub">AI-powered site control</div>
      </div>
    </div>

    <button class="new-chat-btn" onclick="newChat()">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
      New Chat
    </button>

    <div class="sidebar-section">Quick Actions</div>

    <button class="quick-item" onclick="quickSend('What is the current brain-bot status? How many articles published?')">
      <div class="qi-icon" style="background:rgba(255,107,53,.15);color:#FF6B35">📊</div>Site Status
    </button>
    <button class="quick-item" onclick="quickSend('Search the web for: latest IT security vulnerabilities 2025')">
      <div class="qi-icon" style="background:rgba(56,189,248,.1);color:#38BDF8">🔍</div>Web Search
    </button>
    <button class="quick-item" onclick="quickSend('List all published articles and pending topics from the seed list')">
      <div class="qi-icon" style="background:rgba(34,197,94,.1);color:#22C55E">📝</div>Articles
    </button>
    <button class="quick-item" onclick="quickSend('Trigger the brain-bot to publish an article now')">
      <div class="qi-icon" style="background:rgba(168,85,247,.1);color:#A855F7">🚀</div>Publish Now
    </button>
    <button class="quick-item" onclick="quickSend('List open pull requests and recent workflow runs')">
      <div class="qi-icon" style="background:rgba(251,191,36,.1);color:#FBB724">⚙️</div>GitHub
    </button>
    <a href="/auto-log" target="_blank" class="quick-item" style="text-decoration:none">
      <div class="qi-icon" style="background:rgba(34,197,94,.1);color:#22C55E">🤖</div>Auto Log
    </a>

    <div class="sidebar-footer">
      <div>Powered by Claude</div>
      <div class="model-badge"><span class="model-dot"></span>claude-haiku-4-5</div>
    </div>
  </div>

  <!-- Main -->
  <div id="main">
    <div id="header">
      <div style="width:32px;height:32px;background:rgba(255,107,53,.15);border:1px solid rgba(255,107,53,.3);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px">⚡</div>
      <div>
        <h2>ITVedas AI Agent</h2>
        <p>Full site control · Web search · GitHub · Publishing</p>
      </div>
      <div id="thinking-indicator">
        <span class="spin">⟳</span> Thinking...
      </div>
    </div>

    <div id="messages">
      <!-- Welcome shown initially -->
      <div id="welcome">
        <h2>How can I help?</h2>
        <p>I'm your ITVedas AI Agent. I can search the web, manage your GitHub repo, publish articles, check bot status, and answer any question — with advanced thinking.</p>
        <div class="suggestion-grid">
          <div class="suggestion" onclick="quickSend('What is the current status of brain-bot? Show articles published and seeds remaining.')">
            <div class="s-icon">📊</div>
            <div class="s-title">Site Status</div>
            <div class="s-desc">Brain-bot status, articles published</div>
          </div>
          <div class="suggestion" onclick="quickSend('Search the web for best SEO strategies for IT education websites in 2025')">
            <div class="s-icon">🔍</div>
            <div class="s-title">Web Research</div>
            <div class="s-desc">Search internet for current info</div>
          </div>
          <div class="suggestion" onclick="quickSend('Publish an article about \"How SSL/TLS encryption works\" in the Security chapter')">
            <div class="s-icon">✍️</div>
            <div class="s-title">Publish Article</div>
            <div class="s-desc">Trigger brain-bot for a topic</div>
          </div>
          <div class="suggestion" onclick="quickSend('Read the index.html file and suggest 3 specific improvements to increase visitor engagement')">
            <div class="s-icon">💡</div>
            <div class="s-title">Site Improvements</div>
            <div class="s-desc">Analyze and suggest improvements</div>
          </div>
        </div>
      </div>
    </div>

    <div id="input-area">
      <div id="input-wrap">
        <textarea id="chat-input" placeholder="Ask me anything — I'll think, search, and act..." rows="1"></textarea>
        <button id="send-btn" onclick="sendMsg()" title="Send (Enter)">
          <svg width="18" height="18" fill="white" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
      <div class="input-hint">Enter to send · Shift+Enter for new line · The agent uses extended thinking for complex tasks</div>
    </div>
  </div>
</div>

<script>
const messagesEl = document.getElementById('messages');
const welcomeEl  = document.getElementById('welcome');
const inputEl    = document.getElementById('chat-input');
const sendBtn    = document.getElementById('send-btn');
const thinkingEl = document.getElementById('thinking-indicator');
let isGenerating = false;

// ── Auto-resize textarea
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 200) + 'px';
});
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
});

function newChat() {
  fetch('/clear', {method:'POST'});
  messagesEl.innerHTML = '';
  messagesEl.appendChild(welcomeEl);
  welcomeEl.style.display = 'flex';
}

function quickSend(text) {
  inputEl.value = text;
  sendMsg();
}

function sendMsg() {
  if (isGenerating) return;
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  welcomeEl.style.display = 'none';
  appendUser(text);
  streamResponse(text);
}

function appendUser(text) {
  const el = document.createElement('div');
  el.className = 'msg-row user';
  el.innerHTML = `
    <div class="avatar">👤</div>
    <div class="msg-body">
      <div class="bubble">${escHtml(text)}</div>
      <div class="msg-meta">${timeStr()}</div>
    </div>`;
  messagesEl.appendChild(el);
  scrollBottom();
}

function streamResponse(message) {
  isGenerating = true;
  sendBtn.disabled = true;
  thinkingEl.classList.add('active');

  // Create assistant row
  const row = document.createElement('div');
  row.className = 'msg-row assistant';
  const body = document.createElement('div');
  body.className = 'msg-body';
  const avatarEl = document.createElement('div');
  avatarEl.className = 'avatar';
  avatarEl.textContent = '⚡';
  row.appendChild(avatarEl);
  row.appendChild(body);
  messagesEl.appendChild(row);
  scrollBottom();

  // Containers
  let thinkingDiv = null;
  let thinkingContent = null;
  let currentToolDiv = null;
  let textBubble = null;
  let textContent = '';

  function getTextBubble() {
    if (!textBubble) {
      textBubble = document.createElement('div');
      textBubble.className = 'bubble';
      body.appendChild(textBubble);
    }
    return textBubble;
  }

  function handleChunk(obj) {
    if (obj.type === 'thinking') {
      if (!thinkingDiv) {
        thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'thinking-block';
        thinkingDiv.innerHTML = `
          <div class="thinking-header" onclick="toggleThinking(this)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
            </svg>
            Extended thinking
            <svg class="thinking-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
          <div class="thinking-content"></div>`;
        body.insertBefore(thinkingDiv, body.firstChild);
        thinkingContent = thinkingDiv.querySelector('.thinking-content');
      }
      thinkingContent.textContent += obj.text;
    }
    else if (obj.type === 'tool_start') {
      currentToolDiv = document.createElement('div');
      currentToolDiv.className = 'tool-block';
      const argsStr = JSON.stringify(obj.input, null, 2);
      currentToolDiv.innerHTML = `
        <div class="tool-header">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
          </svg>
          <span class="tool-name">${escHtml(obj.name)}</span>
          <span class="tool-status">running</span>
        </div>
        <div class="tool-args">${escHtml(argsStr)}</div>
        <div class="tool-result"></div>`;
      body.appendChild(currentToolDiv);
      scrollBottom();
    }
    else if (obj.type === 'tool_result') {
      if (currentToolDiv) {
        const status = currentToolDiv.querySelector('.tool-status');
        if (status) { status.textContent = 'done'; status.style.background = 'rgba(34,197,94,.1)'; status.style.color = '#22C55E'; }
        const resultEl = currentToolDiv.querySelector('.tool-result');
        if (resultEl) resultEl.textContent = obj.result;
        currentToolDiv = null;
      }
      scrollBottom();
    }
    else if (obj.type === 'text') {
      textContent += obj.text;
      const bubble = getTextBubble();
      bubble.innerHTML = renderMarkdown(escHtml(textContent)) + '<span class="cursor"></span>';
      scrollBottom();
    }
    else if (obj.type === 'done') {
      if (textBubble) {
        textBubble.innerHTML = renderMarkdown(escHtml(textContent));
      }
      const meta = document.createElement('div');
      meta.className = 'msg-meta';
      meta.textContent = `ITVedas Agent · ${timeStr()}`;
      body.appendChild(meta);
      if (thinkingDiv) thinkingDiv.classList.add('collapsed');
      isGenerating = false;
      sendBtn.disabled = false;
      thinkingEl.classList.remove('active');
      scrollBottom();
    }
  }

  fetch('/chat', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: message})
  }).then(resp => {
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    function read() {
      reader.read().then(({done, value}) => {
        if (done) return;
        buf += decoder.decode(value, {stream: true});
        const lines = buf.split('\n');
        buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try { handleChunk(JSON.parse(line.slice(6))); } catch {}
        }
        read();
      });
    }
    read();
  }).catch(() => {
    const bubble = getTextBubble();
    if (!textContent) bubble.textContent = '⚠️ Connection error. Is the agent server running?';
    isGenerating = false;
    sendBtn.disabled = false;
    thinkingEl.classList.remove('active');
  });
}

// ── SSE via GET for EventSource
document.addEventListener('DOMContentLoaded', () => {
  // Patch: use EventSource with GET but we need to support POST.
  // Override: chat route accepts GET too.
});

function toggleThinking(header) {
  header.closest('.thinking-block').classList.toggle('collapsed');
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function timeStr() {
  return new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
}

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderMarkdown(s) {
  // Inline code first (protect from further processing)
  const codeMap = {};
  let ci = 0;
  s = s.replace(/`{3}([\s\S]*?)`{3}/g, (_, c) => {
    const k = `__CODE${ci++}__`;
    codeMap[k] = `<pre><code>${c}</code></pre>`;
    return k;
  });
  s = s.replace(/`([^`\n]+)`/g, (_, c) => {
    const k = `__CODE${ci++}__`;
    codeMap[k] = `<code>${c}</code>`;
    return k;
  });
  // Block elements
  s = s.replace(/^#{3} (.+)$/gm, '<h3>$1</h3>');
  s = s.replace(/^#{2} (.+)$/gm, '<h2>$1</h2>');
  s = s.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  s = s.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  s = s.replace(/^---+$/gm, '<hr>');
  // Lists
  s = s.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
  s = s.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
  s = s.replace(/<\/ul>\s*<ul>/g, '');
  s = s.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // Newlines
  s = s.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
  s = `<p>${s}</p>`;
  // Restore code
  Object.entries(codeMap).forEach(([k,v]) => { s = s.replace(k, v); });
  return s;
}
</script>
</body>
</html>
"""

# SSE route via GET for EventSource compatibility
if FLASK_OK:
    # /stream kept for backward compat — delegates to same logic as /chat
    @app.route("/stream", methods=["GET", "POST"])
    def stream():
        if not _check_auth():
            return Response("data: {\"type\":\"done\"}\n\n", mimetype="text/event-stream")
        global _history
        if request.method == "POST":
            data = request.get_json() or {}
            msg = (data.get("msg") or data.get("message") or "").strip()
        else:
            msg = request.args.get("msg", "").strip()
        if not msg:
            return Response("data: {\"type\":\"done\"}\n\n", mimetype="text/event-stream")

        def generate_and_track():
            global _history
            assistant_text = ""
            for chunk in agentic_loop_stream(msg, _history):
                try:
                    obj = json.loads(chunk.replace("data: ", "").strip())
                    if obj.get("type") == "text":
                        assistant_text += obj.get("text", "")
                except Exception:
                    pass
                yield chunk
            if assistant_text:
                _history.append({"role": "user", "content": msg})
                _history.append({"role": "assistant", "content": assistant_text})
                if len(_history) > 40:
                    _history = _history[-40:]

        return Response(
            stream_with_context(generate_and_track()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
#  AUTONOMOUS AGENT LOOP
# ═══════════════════════════════════════════════════════════════════════════════
import threading

_auto_log: list = []   # recent autonomous actions visible in chat

AUTONOMOUS_PROMPT = """You are the ITVedas site brain running autonomously on the VPS. You have FULL responsibility for this website. No human is watching — act independently.

YOUR MISSION THIS RUN:
1. Read itvedas-brain/memory/brain_memory.json to find the next unpublished topic
2. Read an existing article from chapters/ to understand the exact HTML structure and style
3. Write a COMPLETE, high-quality HTML article (1000-1500 words) for the next topic:
   - Full HTML page matching existing article style exactly
   - SEO title (keyword first, under 60 chars)
   - Meta description (155 chars, includes CTA)
   - First paragraph answers the question in under 50 words (Featured Snippet target)
   - At least 4 subheadings (H2/H3) with keywords
   - FAQ section with 4 Q&As targeting "People Also Ask"
   - Internal links to 3 related articles
   - Schema markup (Article + FAQ JSON-LD)
   - GA4 tracking: G-D98BFZSJYP
4. Save the article to the correct chapters/CHAPTER/SLUG.html path in GitHub
5. Read the chapter's index file and add the new article to the article list
6. Update itvedas-brain/memory/heartbeat.json with timestamp and publish count
7. Update itvedas-brain/memory/brain_memory.json to mark the topic as published

CONTENT RULES:
- Real, accurate technical content only — no filler, no AI-sounding phrases
- Start with a hook fact or question, not "In today's world..."
- Vary sentence length. Use contractions. Be direct and specific.
- Dark theme site (#0A0A0F bg, #FF6B35 orange accent) — match existing article HTML

Report exactly what article you published and its URL path."""

def _log(msg: str):
    print(msg, flush=True)
    sys.stdout.flush()

def _run_autonomous():
    import time as _time
    _log("[AUTO] Thread started — first run in 30s")
    _time.sleep(30)
    while True:
        ts = _time.strftime("%Y-%m-%d %H:%M:%S UTC")
        _log(f"[AUTO] Starting run at {ts}")
        try:
            result_text = ""
            for chunk in agentic_loop_stream(AUTONOMOUS_PROMPT, []):
                try:
                    obj = json.loads(chunk.replace("data: ", "").strip())
                    if obj.get("type") == "text":
                        result_text += obj.get("text", "")
                    elif obj.get("type") == "tool_start":
                        _log(f"[AUTO] Tool: {obj.get('name')}")
                except Exception:
                    pass
            summary = result_text.strip()[:500] if result_text.strip() else "No output"
            entry = {"time": ts, "summary": summary}
            _auto_log.append(entry)
            if len(_auto_log) > 50:
                _auto_log.pop(0)
            _log(f"[AUTO] Done: {summary[:200]}")
        except Exception as e:
            import traceback
            _log(f"[AUTO] Error: {e}\n{traceback.format_exc()}")
        _log(f"[AUTO] Sleeping {AUTO_INTERVAL}s until next run")
        _time.sleep(AUTO_INTERVAL)

def check_deps():
    missing = []
    if not FLASK_OK: missing.append("flask")
    if not DDG_OK:   missing.append("duckduckgo-search")
    if not BS4_OK:   missing.append("beautifulsoup4")
    if missing:
        print(f"\n⚠  Missing packages. Install with:\n   pip install {' '.join(missing)}\n")
        if not FLASK_OK:
            sys.exit(1)

def main():
    check_deps()
    if not ANTHROPIC_KEY:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Start autonomous publishing loop in background
    t = threading.Thread(target=_run_autonomous, daemon=True)
    t.start()

    print(f"""
╔═══════════════════════════════════════╗
║      ITVedas AI Agent  v2            ║
║  Open: http://localhost:{PORT}          ║
║  Model: {MODEL}        ║
║  Auto-publish: every {AUTO_INTERVAL}s        ║
╚═══════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)

if __name__ == "__main__":
    main()
