"""
═══════════════════════════════════════════════════════════════════
 ITVedas Self-Improve — Daily Autonomous Code Update
═══════════════════════════════════════════════════════════════════
 Runs once a day on GitHub Actions. No human approval required.

 What it does each run:
   1. Claude (primary)  reviews recent activity logs + state and decides
      ONE small, concrete improvement to make to the codebase, scoped to
      a single target file from an allowed list.
   2. OpenAI (secondary) writes the new full contents of that file.
   3. The change is applied, syntax/build-checked, and if (and only if)
      the check passes, committed and pushed directly to main.
   4. If the check fails, the change is discarded and nothing is pushed.

 This script intentionally limits which files it may touch (TARGET_FILES)
 so a bad LLM decision can't take down auth, the API server, or CI itself.

 Config via environment variables (GitHub Secrets):
   ANTHROPIC_API_KEY   (required) — decides what to change
   OPENAI_API_KEY      (required) — writes the new file contents
   OPENAI_MODEL        (optional, defaults to gpt-4o-mini)
═══════════════════════════════════════════════════════════════════
"""

import os, json, time, pathlib, datetime, subprocess, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from core.llm import claude as _core_claude, openai_chat as _core_openai_chat, strip_code_fence
from core.log import log as _core_log

API_KEY      = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
MODEL        = "claude-haiku-4-5-20251001"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

ROOT      = pathlib.Path(".")
BRAIN_DIR = ROOT / "itvedas-brain" / "state"

COMPONENT = "self-improve"

# Only these files may ever be rewritten by this job. Keeps the blast
# radius away from auth, the API server, infra/CI, and secrets handling.
TARGET_FILES = [
    "itvedas-brain/content-writer.py",
    "itvedas-brain/news-agent.py",
    "dashboard/frontend/src/App.css",
]


def log(msg):
    _core_log(COMPONENT, msg)


def claude(prompt, system=None, max_tokens=2000):
    return _core_claude(prompt, system=system, max_tokens=max_tokens,
                         api_key=API_KEY, model=MODEL, log_fn=log)


def openai_chat(prompt, system=None, max_tokens=6000):
    return _core_openai_chat(prompt, system=system, max_tokens=max_tokens,
                              api_key=OPENAI_KEY, model=OPENAI_MODEL, log_fn=log)


def decide_target():
    recent_log = ""
    for name in ("brain.log",):
        p = BRAIN_DIR / name
        if p.exists():
            recent_log = p.read_text()[-4000:]
    prompt = f"""You are the lead decision-maker for an autonomous SEO/content
bot (ITVedas). Pick exactly ONE of these files to improve today, and describe
ONE small, concrete, safe improvement to make to it. Do not propose anything
that changes authentication, API contracts, or file paths used elsewhere.

Allowed files:
{chr(10).join("- " + f for f in TARGET_FILES)}

Recent activity log (may be empty):
{recent_log or "(no recent log)"}

Reply with exactly two lines:
FILE: <one of the allowed file paths>
CHANGE: <one sentence describing the improvement>
"""
    reply = claude(prompt)
    file_path, change = None, None
    for line in reply.splitlines():
        if line.startswith("FILE:"):
            file_path = line.split(":", 1)[1].strip()
        elif line.startswith("CHANGE:"):
            change = line.split(":", 1)[1].strip()
    if file_path not in TARGET_FILES:
        raise SystemExit(f"Claude picked a disallowed/unparsable file: {file_path!r}")
    return file_path, change or "Minor improvement"


def write_new_version(file_path, change):
    current = (ROOT / file_path).read_text()
    prompt = f"""Here is the current full contents of {file_path}:

-----
{current}
-----

Apply this improvement: {change}

Rules:
- Keep all existing function/endpoint names, signatures, and file structure intact
  unless the improvement specifically requires changing internal logic.
- Do not remove functionality.
- Output the COMPLETE new file contents only, no explanation, no markdown fences.
"""
    new_content = openai_chat(prompt, max_tokens=6000)
    return strip_code_fence(new_content)


def check_passes(file_path):
    if file_path.endswith(".py"):
        result = subprocess.run(["python3", "-m", "py_compile", file_path],
                                 capture_output=True, text=True)
        return result.returncode == 0, result.stderr
    if file_path.endswith((".css", ".jsx", ".js")):
        frontend = ROOT / "dashboard" / "frontend"
        result = subprocess.run(["npm", "run", "build"], cwd=frontend,
                                 capture_output=True, text=True)
        return result.returncode == 0, result.stderr
    return True, ""


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def main():
    if not API_KEY:
        raise SystemExit("FATAL: ANTHROPIC_API_KEY not set")
    if not OPENAI_KEY:
        raise SystemExit("FATAL: OPENAI_API_KEY not set")

    file_path, change = decide_target()
    log(f"Decided target: {file_path} — {change}")

    target = ROOT / file_path
    original = target.read_text()
    try:
        new_content = write_new_version(file_path, change)
    except Exception as e:
        log(f"OpenAI generation failed, aborting: {e}")
        return

    if not new_content.strip():
        log("Generated content was empty, aborting.")
        return

    target.write_text(new_content)
    ok, err = check_passes(file_path)
    if not ok:
        log(f"Check failed for {file_path}, reverting. Error: {err[:2000]}")
        target.write_text(original)
        return

    log(f"Check passed for {file_path}. Committing.")
    git("config", "user.name", "ITVedas Bot")
    git("config", "user.email", "bot@itvedas.com")
    git("add", file_path)
    commit = git("commit", "-m", f"Self-improve: {change}")
    if commit.returncode != 0:
        log(f"Nothing to commit or commit failed: {commit.stderr}")
        return
    push = git("push", "origin", "HEAD:main")
    if push.returncode != 0:
        log(f"Push failed: {push.stderr}")
    else:
        log("Pushed self-improvement to main.")


if __name__ == "__main__":
    main()
