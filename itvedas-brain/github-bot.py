#!/usr/bin/env python3
"""
ITVedas GitHub Bot — Conversational AI Agent
Responds to GitHub issues and comments using Claude with tool_use.
"""

from __future__ import annotations

import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO     = os.environ.get("GITHUB_REPOSITORY", "itvedas29/itvedas")
GITHUB_BRANCH   = os.environ.get("GITHUB_BRANCH", "main")
MODEL           = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

ISSUE_NUMBER    = os.environ.get("ISSUE_NUMBER", "")
ISSUE_TITLE     = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY      = os.environ.get("ISSUE_BODY", "")
COMMENT_BODY    = os.environ.get("COMMENT_BODY", "")
TRIGGERED_BY    = os.environ.get("TRIGGERED_BY", "user")

ROOT       = pathlib.Path(__file__).resolve().parent.parent
BRAIN_DIR  = pathlib.Path(__file__).resolve().parent
STATE_DIR  = BRAIN_DIR / "state"
MEM_DIR    = BRAIN_DIR / "memory"

MAX_TOOL_ITERATIONS = 20

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
def log(tag: str, msg: str) -> None:
    print(f"[{tag.upper()}] {msg}", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  GITHUB API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _gh_headers() -> dict[str, str]:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "ITVedasBot/1.0",
    }

def _gh_request(
    method: str,
    path: str,
    body: dict | None = None,
    params: dict | None = None,
) -> Any:
    """Make a GitHub API request and return parsed JSON (or None for 204)."""
    url = f"https://api.github.com{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_gh_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} → {e.code}: {err_body}") from e

def _gh_get(path: str, params: dict | None = None) -> Any:
    return _gh_request("GET", path, params=params)

def _gh_post(path: str, body: dict) -> Any:
    return _gh_request("POST", path, body=body)

def _gh_put(path: str, body: dict) -> Any:
    return _gh_request("PUT", path, body=body)

def _gh_patch(path: str, body: dict) -> Any:
    return _gh_request("PATCH", path, body=body)

def _gh_delete(path: str, body: dict | None = None) -> Any:
    return _gh_request("DELETE", path, body=body)

# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_read_file(path: str) -> str:
    """Read any file in the repo via GitHub API."""
    try:
        res = _gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", {"ref": GITHUB_BRANCH})
        if isinstance(res, list):
            return f"Path is a directory. Files: {[f['name'] for f in res]}"
        content = base64.b64decode(res["content"]).decode("utf-8")
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def tool_write_file(path: str, content: str, message: str) -> str:
    """Create or update a file in the repo."""
    try:
        # Try to get existing SHA
        sha = None
        try:
            existing = _gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", {"ref": GITHUB_BRANCH})
            sha = existing.get("sha")
        except Exception:
            pass  # File doesn't exist yet

        body: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": GITHUB_BRANCH,
        }
        if sha:
            body["sha"] = sha

        res = _gh_put(f"/repos/{GITHUB_REPO}/contents/{path}", body)
        action = "updated" if sha else "created"
        commit_sha = res.get("commit", {}).get("sha", "unknown")[:8]
        return f"File {action}: {path} (commit: {commit_sha})"
    except Exception as e:
        return f"Error writing file: {e}"


def tool_delete_file(path: str, message: str) -> str:
    """Delete a file in the repo."""
    try:
        existing = _gh_get(f"/repos/{GITHUB_REPO}/contents/{path}", {"ref": GITHUB_BRANCH})
        sha = existing.get("sha")
        body = {
            "message": message,
            "sha": sha,
            "branch": GITHUB_BRANCH,
        }
        _gh_delete(f"/repos/{GITHUB_REPO}/contents/{path}", body)
        return f"Deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {e}"


def tool_list_files(path: str = "") -> str:
    """List files in a directory of the repo."""
    try:
        api_path = f"/repos/{GITHUB_REPO}/contents/{path}" if path else f"/repos/{GITHUB_REPO}/contents"
        res = _gh_get(api_path, {"ref": GITHUB_BRANCH})
        if isinstance(res, list):
            items = []
            for item in res:
                t = "📁" if item["type"] == "dir" else "📄"
                items.append(f"{t} {item['name']} ({item['type']})")
            return "\n".join(items) if items else "Empty directory"
        return f"Not a directory: {path}"
    except Exception as e:
        return f"Error listing files: {e}"


def tool_create_branch(branch_name: str, from_branch: str = "") -> str:
    """Create a new branch."""
    try:
        base = from_branch or GITHUB_BRANCH
        # Get SHA of base branch
        ref_res = _gh_get(f"/repos/{GITHUB_REPO}/git/ref/heads/{base}")
        sha = ref_res["object"]["sha"]
        body = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        _gh_post(f"/repos/{GITHUB_REPO}/git/refs", body)
        return f"Created branch '{branch_name}' from '{base}' (sha: {sha[:8]})"
    except Exception as e:
        return f"Error creating branch: {e}"


def tool_list_branches() -> str:
    """List all branches in the repo."""
    try:
        branches = _gh_get(f"/repos/{GITHUB_REPO}/branches", {"per_page": 30})
        names = [b["name"] for b in branches]
        return f"Branches ({len(names)}): " + ", ".join(names)
    except Exception as e:
        return f"Error listing branches: {e}"


def tool_create_pull_request(title: str, body: str, head: str, base: str = "") -> str:
    """Create a pull request."""
    try:
        base_branch = base or GITHUB_BRANCH
        res = _gh_post(f"/repos/{GITHUB_REPO}/pulls", {
            "title": title,
            "body": body,
            "head": head,
            "base": base_branch,
        })
        return f"Created PR #{res['number']}: {res['title']}\nURL: {res['html_url']}"
    except Exception as e:
        return f"Error creating PR: {e}"


def tool_merge_pull_request(pr_number: int, method: str = "squash") -> str:
    """Merge a pull request."""
    try:
        pr = _gh_get(f"/repos/{GITHUB_REPO}/pulls/{pr_number}")
        res = _gh_put(f"/repos/{GITHUB_REPO}/pulls/{pr_number}/merge", {
            "merge_method": method,
        })
        return f"Merged PR #{pr_number}: {pr['title']} via {method}\nSHA: {res.get('sha', 'unknown')[:8]}"
    except Exception as e:
        return f"Error merging PR: {e}"


def tool_list_pull_requests(state: str = "open") -> str:
    """List pull requests."""
    try:
        prs = _gh_get(f"/repos/{GITHUB_REPO}/pulls", {"state": state, "per_page": 10})
        if not prs:
            return f"No {state} pull requests."
        lines = []
        for pr in prs:
            lines.append(f"PR #{pr['number']}: {pr['title']} [{pr['state']}] by {pr['user']['login']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing PRs: {e}"


def tool_get_pull_request(pr_number: int) -> str:
    """Get details of a specific pull request."""
    try:
        pr = _gh_get(f"/repos/{GITHUB_REPO}/pulls/{pr_number}")
        return (
            f"PR #{pr['number']}: {pr['title']}\n"
            f"State: {pr['state']}\n"
            f"Author: {pr['user']['login']}\n"
            f"Head: {pr['head']['ref']} → Base: {pr['base']['ref']}\n"
            f"Mergeable: {pr.get('mergeable')}\n"
            f"URL: {pr['html_url']}\n"
            f"Body:\n{pr.get('body') or '(no description)'}"
        )
    except Exception as e:
        return f"Error getting PR: {e}"


def tool_create_issue(title: str, body: str, labels: list[str] | None = None) -> str:
    """Create a new issue."""
    try:
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        res = _gh_post(f"/repos/{GITHUB_REPO}/issues", payload)
        return f"Created issue #{res['number']}: {res['title']}\nURL: {res['html_url']}"
    except Exception as e:
        return f"Error creating issue: {e}"


def tool_list_issues(state: str = "open") -> str:
    """List issues (excludes PRs)."""
    try:
        issues = _gh_get(f"/repos/{GITHUB_REPO}/issues", {"state": state, "per_page": 15})
        # Exclude PRs (they appear in /issues too)
        issues = [i for i in issues if "pull_request" not in i]
        if not issues:
            return f"No {state} issues."
        lines = []
        for i in issues:
            labels = ", ".join(l["name"] for l in i.get("labels", []))
            lines.append(f"#{i['number']}: {i['title']} [{labels or 'no labels'}]")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing issues: {e}"


def tool_close_issue(issue_number: int) -> str:
    """Close an issue."""
    try:
        res = _gh_patch(f"/repos/{GITHUB_REPO}/issues/{issue_number}", {
            "state": "closed",
            "state_reason": "completed",
        })
        return f"Closed issue #{issue_number}: {res['title']}"
    except Exception as e:
        return f"Error closing issue: {e}"


def tool_add_issue_comment(issue_number: int, body: str) -> str:
    """Add a comment to an issue."""
    try:
        res = _gh_post(f"/repos/{GITHUB_REPO}/issues/{issue_number}/comments", {"body": body})
        return f"Posted comment #{res['id']} on issue #{issue_number}\nURL: {res['html_url']}"
    except Exception as e:
        return f"Error posting comment: {e}"


def tool_trigger_workflow(workflow_file: str, inputs: dict | None = None) -> str:
    """Trigger a GitHub Actions workflow dispatch."""
    try:
        body: dict[str, Any] = {"ref": GITHUB_BRANCH}
        if inputs:
            body["inputs"] = inputs
        _gh_post(f"/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches", body)
        return f"Triggered workflow: {workflow_file} on {GITHUB_BRANCH} with inputs: {inputs or {}}"
    except Exception as e:
        return f"Error triggering workflow: {e}"


def tool_list_workflow_runs(workflow_file: str) -> str:
    """List recent runs of a workflow."""
    try:
        res = _gh_get(
            f"/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/runs",
            {"per_page": 5}
        )
        runs = res.get("workflow_runs", [])
        if not runs:
            return f"No runs found for {workflow_file}"
        lines = []
        for r in runs:
            lines.append(
                f"Run #{r['run_number']}: {r['status']}/{r['conclusion']} "
                f"({r['created_at'][:10]})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing workflow runs: {e}"


def tool_list_commits(branch: str = "", limit: int = 10) -> str:
    """List recent commits on a branch."""
    try:
        b = branch or GITHUB_BRANCH
        commits = _gh_get(f"/repos/{GITHUB_REPO}/commits", {"sha": b, "per_page": limit})
        lines = []
        for c in commits:
            sha = c["sha"][:8]
            msg = c["commit"]["message"].split("\n")[0][:72]
            author = c["commit"]["author"]["name"]
            date = c["commit"]["author"]["date"][:10]
            lines.append(f"{sha} ({date}) {author}: {msg}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing commits: {e}"


def tool_search_code(query: str) -> str:
    """Search code in the repo."""
    try:
        res = _gh_get("/search/code", {"q": f"{query} repo:{GITHUB_REPO}", "per_page": 10})
        items = res.get("items", [])
        if not items:
            return f"No results for: {query}"
        lines = [f"Found {res['total_count']} matches (showing {len(items)}):"]
        for item in items:
            lines.append(f"  {item['path']} — {item.get('repository', {}).get('full_name', '')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching code: {e}"


def tool_get_repo_info() -> str:
    """Get repo statistics and info."""
    try:
        repo = _gh_get(f"/repos/{GITHUB_REPO}")
        return (
            f"Repo: {repo['full_name']}\n"
            f"Description: {repo.get('description') or 'none'}\n"
            f"Stars: {repo['stargazers_count']} | Forks: {repo['forks_count']} | Watchers: {repo['watchers_count']}\n"
            f"Default branch: {repo['default_branch']}\n"
            f"Open issues: {repo['open_issues_count']}\n"
            f"Language: {repo.get('language') or 'mixed'}\n"
            f"URL: {repo['html_url']}"
        )
    except Exception as e:
        return f"Error getting repo info: {e}"


def tool_publish_article(topic: str = "", chapter: str = "") -> str:
    """Trigger brain-bot to write and publish an article on a specific topic."""
    try:
        # Write the requested topic to state file so brain-bot picks it up
        if topic:
            topic_data = {"topic": topic, "chapter": chapter, "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
            topic_json = json.dumps(topic_data, indent=2)
            write_res = tool_write_file(
                "itvedas-brain/state/requested_topic.json",
                topic_json,
                f"bot: queue article request — {topic[:60]}"
            )
            log("publish", f"Wrote topic file: {write_res}")

        # Trigger the brain-bot workflow
        trigger_res = tool_trigger_workflow("brain-bot.yml", {"bot_mode": "article"})
        if topic:
            return f"Queued article on '{topic}' (chapter: {chapter or 'auto'}). {trigger_res}"
        return f"Triggered article generation. {trigger_res}"
    except Exception as e:
        return f"Error publishing article: {e}"


def tool_get_brain_status() -> str:
    """Read heartbeat.json and brain_memory.json to report bot status."""
    try:
        parts = []

        # Heartbeat
        try:
            heartbeat_raw = tool_read_file("itvedas-brain/state/heartbeat.json")
            heartbeat = json.loads(heartbeat_raw)
            parts.append("=== BRAIN BOT HEARTBEAT ===")
            parts.append(f"Last run: {heartbeat.get('last_run', 'unknown')}")
            parts.append(f"Status: {heartbeat.get('status', 'unknown')}")
            parts.append(f"Articles today: {heartbeat.get('articles_today', 0)}")
            parts.append(f"Total published: {heartbeat.get('total_published', 0)}")
            parts.append(f"Last article: {heartbeat.get('last_article_title', 'unknown')}")
            if heartbeat.get("error"):
                parts.append(f"Last error: {heartbeat['error']}")
        except Exception as e:
            parts.append(f"Heartbeat unavailable: {e}")

        # Brain memory
        try:
            mem_raw = tool_read_file("itvedas-brain/memory/brain_memory.json")
            mem = json.loads(mem_raw)
            parts.append("\n=== BRAIN MEMORY ===")
            seeds = mem.get("seed_topics", [])
            published = mem.get("published_topics", [])
            parts.append(f"Seed topics remaining: {len(seeds)}")
            parts.append(f"Published topics: {len(published)}")
            if seeds:
                parts.append(f"Next up: {seeds[0] if isinstance(seeds[0], str) else seeds[0].get('topic', str(seeds[0]))}")
            if published:
                recent = published[-3:]
                parts.append("Recent publications:")
                for p in recent:
                    title = p if isinstance(p, str) else p.get("title", str(p))
                    parts.append(f"  - {title}")
        except Exception as e:
            parts.append(f"Memory unavailable: {e}")

        # State
        try:
            state_raw = tool_read_file("itvedas-brain/state/state.json")
            state = json.loads(state_raw)
            parts.append("\n=== STATE ===")
            parts.append(f"Mode: {state.get('mode', 'unknown')}")
            parts.append(f"Seeds remaining: {state.get('seeds_remaining', 'unknown')}")
        except Exception:
            pass

        return "\n".join(parts) if parts else "No brain status data available."
    except Exception as e:
        return f"Error getting brain status: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════
def dispatch_tool(name: str, args: dict) -> str:
    """Call the appropriate tool function and return string result."""
    log("tool", f"Calling {name}({list(args.keys())})")
    try:
        if name == "read_file":
            return tool_read_file(args["path"])
        elif name == "write_file":
            return tool_write_file(args["path"], args["content"], args.get("message", "bot: update file"))
        elif name == "delete_file":
            return tool_delete_file(args["path"], args.get("message", "bot: delete file"))
        elif name == "list_files":
            return tool_list_files(args.get("path", ""))
        elif name == "create_branch":
            return tool_create_branch(args["branch_name"], args.get("from_branch", ""))
        elif name == "list_branches":
            return tool_list_branches()
        elif name == "create_pull_request":
            return tool_create_pull_request(
                args["title"], args["body"], args["head"], args.get("base", "")
            )
        elif name == "merge_pull_request":
            return tool_merge_pull_request(int(args["pr_number"]), args.get("method", "squash"))
        elif name == "list_pull_requests":
            return tool_list_pull_requests(args.get("state", "open"))
        elif name == "get_pull_request":
            return tool_get_pull_request(int(args["pr_number"]))
        elif name == "create_issue":
            return tool_create_issue(args["title"], args["body"], args.get("labels"))
        elif name == "list_issues":
            return tool_list_issues(args.get("state", "open"))
        elif name == "close_issue":
            return tool_close_issue(int(args["issue_number"]))
        elif name == "add_issue_comment":
            return tool_add_issue_comment(int(args["issue_number"]), args["body"])
        elif name == "trigger_workflow":
            return tool_trigger_workflow(args["workflow_file"], args.get("inputs"))
        elif name == "list_workflow_runs":
            return tool_list_workflow_runs(args["workflow_file"])
        elif name == "list_commits":
            return tool_list_commits(args.get("branch", ""), int(args.get("limit", 10)))
        elif name == "search_code":
            return tool_search_code(args["query"])
        elif name == "get_repo_info":
            return tool_get_repo_info()
        elif name == "publish_article":
            return tool_publish_article(args.get("topic", ""), args.get("chapter", ""))
        elif name == "get_brain_status":
            return tool_get_brain_status()
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool {name} error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS (for Claude)
# ═══════════════════════════════════════════════════════════════════════════════
TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read any file in the GitHub repo by path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root, e.g. 'index.html' or 'itvedas-brain/state/heartbeat.json'"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or update a file in the repo with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to repo root"},
                "content": {"type": "string", "description": "Full file content to write"},
                "message": {"type": "string", "description": "Git commit message"},
            },
            "required": ["path", "content", "message"],
        },
    },
    {
        "name": "delete_file",
        "description": "Delete a file from the repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to delete"},
                "message": {"type": "string", "description": "Git commit message"},
            },
            "required": ["path", "message"],
        },
    },
    {
        "name": "list_files",
        "description": "List files and directories at a given path in the repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (empty string for root)"},
            },
            "required": [],
        },
    },
    {
        "name": "create_branch",
        "description": "Create a new git branch in the repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch_name": {"type": "string", "description": "Name for the new branch"},
                "from_branch": {"type": "string", "description": "Branch to base from (defaults to main)"},
            },
            "required": ["branch_name"],
        },
    },
    {
        "name": "list_branches",
        "description": "List all branches in the repo.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_pull_request",
        "description": "Create a pull request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "PR title"},
                "body": {"type": "string", "description": "PR description/body"},
                "head": {"type": "string", "description": "Source branch name"},
                "base": {"type": "string", "description": "Target branch (defaults to main)"},
            },
            "required": ["title", "body", "head"],
        },
    },
    {
        "name": "merge_pull_request",
        "description": "Merge a pull request by number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer", "description": "PR number to merge"},
                "method": {"type": "string", "enum": ["merge", "squash", "rebase"], "description": "Merge method (default: squash)"},
            },
            "required": ["pr_number"],
        },
    },
    {
        "name": "list_pull_requests",
        "description": "List pull requests, filtered by state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "Filter by state (default: open)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_pull_request",
        "description": "Get details of a specific pull request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer", "description": "PR number"},
            },
            "required": ["pr_number"],
        },
    },
    {
        "name": "create_issue",
        "description": "Create a new GitHub issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body/description"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "List of label names"},
            },
            "required": ["title", "body"],
        },
    },
    {
        "name": "list_issues",
        "description": "List issues in the repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "enum": ["open", "closed", "all"], "description": "Filter by state (default: open)"},
            },
            "required": [],
        },
    },
    {
        "name": "close_issue",
        "description": "Close a GitHub issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number to close"},
            },
            "required": ["issue_number"],
        },
    },
    {
        "name": "add_issue_comment",
        "description": "Add a comment to any GitHub issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number"},
                "body": {"type": "string", "description": "Comment body (markdown supported)"},
            },
            "required": ["issue_number", "body"],
        },
    },
    {
        "name": "trigger_workflow",
        "description": "Trigger a GitHub Actions workflow via workflow_dispatch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_file": {"type": "string", "description": "Workflow filename, e.g. 'brain-bot.yml'"},
                "inputs": {"type": "object", "description": "Workflow input parameters as key-value pairs"},
            },
            "required": ["workflow_file"],
        },
    },
    {
        "name": "list_workflow_runs",
        "description": "List recent runs of a specific workflow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_file": {"type": "string", "description": "Workflow filename, e.g. 'brain-bot.yml'"},
            },
            "required": ["workflow_file"],
        },
    },
    {
        "name": "list_commits",
        "description": "List recent commits on a branch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "Branch name (defaults to main)"},
                "limit": {"type": "integer", "description": "Max commits to return (default: 10)"},
            },
            "required": [],
        },
    },
    {
        "name": "search_code",
        "description": "Search code within the repo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (GitHub code search syntax)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_repo_info",
        "description": "Get repository statistics and metadata.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "publish_article",
        "description": "Trigger the brain bot to write and publish an article. Optionally specify a topic and chapter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Specific topic to write about (optional)"},
                "chapter": {"type": "string", "description": "Chapter/category for the article (optional)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_brain_status",
        "description": "Get the status of the brain bot: last run, articles published, seeds remaining, errors.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
#  CONVERSATION HISTORY FETCHER
# ═══════════════════════════════════════════════════════════════════════════════
def fetch_conversation_history(issue_number: int) -> list[dict]:
    """Fetch all comments on the issue and format as conversation history."""
    try:
        comments = _gh_get(
            f"/repos/{GITHUB_REPO}/issues/{issue_number}/comments",
            {"per_page": 30, "direction": "asc"}
        )
        history = []
        for comment in comments:
            login = comment["user"]["login"]
            body = comment["body"] or ""
            # Skip our own bot responses that haven't been processed yet
            # Identify bot messages
            is_bot = login in ("github-actions[bot]", "itvedas-bot") or body.endswith("— ITVedas Bot 🤖")
            role = "Bot" if is_bot else "User"
            history.append({"role": role, "text": body, "author": login})
        return history
    except Exception as e:
        log("history", f"Could not fetch conversation history: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  ANTHROPIC API — AGENTIC LOOP
# ═══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are the ITVedas GitHub Bot — an autonomous AI agent managing itvedas.com, a free IT education website.

You have full GitHub access: read/write files, create branches, PRs, issues, trigger workflows.
You also manage the content brain bot that publishes articles daily.

You can:
- Answer questions about the codebase, articles, bot status
- Publish new articles on demand
- Create PRs, merge code changes
- Edit any file (HTML pages, bot config, workflows)
- Report on site status, traffic strategy, published articles
- Make code changes and commit them

Be concise and action-oriented. When asked to do something, do it — don't just describe how to do it.
Always confirm what you did with specific details (file paths, PR numbers, URLs).

Site: https://itvedas.com
Repo: itvedas29/itvedas"""


def call_claude(messages: list[dict]) -> dict:
    """Call Claude API with tool_use and return the raw response dict."""
    if not ANTHROPIC_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "tools": TOOL_DEFINITIONS,
        "messages": messages,
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            if attempt == 2:
                raise RuntimeError(f"Anthropic API error {e.code}: {err}") from e
            log("claude", f"Attempt {attempt+1} failed ({e.code}), retrying...")
            time.sleep(8 * (attempt + 1))
        except Exception as e:
            if attempt == 2:
                raise
            log("claude", f"Attempt {attempt+1} error: {e}, retrying...")
            time.sleep(8 * (attempt + 1))

    raise RuntimeError("All Claude API attempts failed")


def run_agentic_loop(initial_user_message: str) -> str:
    """
    Run the agentic loop:
    1. Call Claude with the user message
    2. If Claude returns tool_use blocks, execute tools and feed results back
    3. Repeat until Claude gives a final text response (stop_reason == 'end_turn')
    4. Return the final text
    """
    messages = [{"role": "user", "content": initial_user_message}]

    for iteration in range(MAX_TOOL_ITERATIONS):
        log("loop", f"Iteration {iteration + 1}/{MAX_TOOL_ITERATIONS}")
        response = call_claude(messages)

        stop_reason = response.get("stop_reason", "")
        content = response.get("content", [])

        log("loop", f"Stop reason: {stop_reason}, content blocks: {len(content)}")

        # Extract text blocks (may accompany tool_use)
        text_blocks = [b for b in content if b.get("type") == "text"]
        tool_blocks = [b for b in content if b.get("type") == "tool_use"]

        if stop_reason == "end_turn" or not tool_blocks:
            # Final response — extract all text
            final_text = "\n".join(b.get("text", "") for b in text_blocks).strip()
            if not final_text:
                final_text = "Done."
            return final_text

        # We have tool calls — add the assistant message and process tools
        messages.append({"role": "assistant", "content": content})

        # Execute all tools and collect results
        tool_results = []
        for tool_block in tool_blocks:
            tool_name = tool_block.get("name", "")
            tool_input = tool_block.get("input", {})
            tool_use_id = tool_block.get("id", "")

            result = dispatch_tool(tool_name, tool_input)
            log("tool", f"Result for {tool_name}: {result[:200]}{'...' if len(result) > 200 else ''}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result,
            })

        # Feed tool results back to Claude
        messages.append({"role": "user", "content": tool_results})

    # Max iterations reached
    log("loop", "WARNING: Max tool iterations reached")
    # Try to extract any final text from last response
    last_text = "\n".join(b.get("text", "") for b in text_blocks).strip()
    return last_text or "Reached maximum tool call iterations. Please try a more specific request."


# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD INITIAL PROMPT WITH CONVERSATION HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
def build_initial_message() -> str:
    """Build the full context message for Claude."""
    parts = []

    # Issue context
    parts.append(f"## GitHub Issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    parts.append(f"**Opened by:** {TRIGGERED_BY}")
    parts.append("")

    if ISSUE_BODY:
        parts.append("**Issue description:**")
        parts.append(ISSUE_BODY.strip())
        parts.append("")

    # Fetch and include conversation history
    if ISSUE_NUMBER:
        history = fetch_conversation_history(int(ISSUE_NUMBER))
        if history:
            parts.append("**Previous messages in this issue:**")
            for msg in history:
                prefix = "Bot" if msg["role"] == "Bot" else f"User ({msg['author']})"
                text = msg["text"].strip()
                # Skip bot's own previous responses to avoid confusion
                parts.append(f"\n{prefix}:\n{text}")
            parts.append("")

    # The triggering message (current comment or original issue)
    if COMMENT_BODY:
        # Strip the @itvedas-bot mention
        clean_comment = COMMENT_BODY.replace("@itvedas-bot", "").strip()
        parts.append(f"**Current request from {TRIGGERED_BY}:**")
        parts.append(clean_comment)
    else:
        # No comment — this was triggered by the issue being opened
        parts.append(f"**This issue was just opened by {TRIGGERED_BY}. Please respond helpfully.**")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
#  POST RESPONSE AS GITHUB COMMENT
# ═══════════════════════════════════════════════════════════════════════════════
def post_response(issue_number: int, text: str) -> None:
    """Post the bot's response as a GitHub issue comment."""
    body = f"{text}\n\n— ITVedas Bot 🤖"
    result = tool_add_issue_comment(issue_number, body)
    log("post", result)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main() -> int:
    log("bot", "=" * 64)
    log("bot", f"ITVedas GitHub Bot | Model: {MODEL}")
    log("bot", f"Issue: #{ISSUE_NUMBER} | Triggered by: {TRIGGERED_BY}")
    log("bot", "=" * 64)

    if not ANTHROPIC_KEY:
        log("bot", "ERROR: ANTHROPIC_API_KEY not set")
        if ISSUE_NUMBER:
            tool_add_issue_comment(
                int(ISSUE_NUMBER),
                "❌ Bot error: ANTHROPIC_API_KEY is not configured.\n\n— ITVedas Bot 🤖"
            )
        return 1

    if not GITHUB_TOKEN:
        log("bot", "ERROR: GITHUB_TOKEN not set")
        return 1

    if not ISSUE_NUMBER:
        log("bot", "ERROR: ISSUE_NUMBER not set")
        return 1

    issue_num = int(ISSUE_NUMBER)

    try:
        # Build the context message
        initial_message = build_initial_message()
        log("bot", f"Initial message length: {len(initial_message)} chars")

        # Run the agentic loop
        final_response = run_agentic_loop(initial_message)
        log("bot", f"Final response length: {len(final_response)} chars")

        # Post the response
        post_response(issue_num, final_response)
        log("bot", "Done!")
        return 0

    except Exception as e:
        error_msg = f"❌ Bot encountered an error: `{type(e).__name__}: {e}`\n\nPlease check the Actions logs for details."
        log("bot", f"ERROR: {e}")
        try:
            tool_add_issue_comment(issue_num, f"{error_msg}\n\n— ITVedas Bot 🤖")
        except Exception as post_err:
            log("bot", f"Could not post error comment: {post_err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
