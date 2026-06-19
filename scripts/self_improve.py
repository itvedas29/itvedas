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

import os, json, time, pathlib, datetime, subprocess, urllib.request

API_KEY      = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
MODEL        = "claude-haiku-4-5-20251001"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

ROOT      = pathlib.Path(".")
BRAIN_DIR = ROOT / "itvedas-brain" / "state"
LOG_FILE  = BRAIN_DIR / "self_improve.log"

# Only these files may ever be rewritten by this job. Keeps the blast
# radius away from auth, the API server, infra/CI, and secrets handling.
TARGET_FILES = [
    "scripts/brain.py",
    "scripts/news_agent_v2.py",
    "dashboard/frontend/src/App.css",
]


def log(msg):
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def claude(prompt, system=None, max_tokens=2000):
    payload = {"model": MODEL, "max_tokens": max_tokens,
               "messages": [{"role": "user", "content": prompt}]}
    if system:
        payload["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=90))
            return res["content"][0]["text"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            log(f"Claude retry {attempt+1}: {e}")
            time.sleep(8)


def openai_chat(prompt, system=None, max_tokens=6000):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": OPENAI_MODEL, "max_tokens": max_tokens, "messages": messages}
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {OPENAI_KEY}",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=90))
            return res["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            log(f"OpenAI retry {attempt+1}: {e}")
            time.sleep(8)


def strip_code_fence(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def decide_target():
    recent_log = ""
    for name in ("activity.log",):
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
