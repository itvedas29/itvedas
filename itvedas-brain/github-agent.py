#!/usr/bin/env python3
"""Phase 5 - GitHub Agent.

Reads the Phase 3/4 daily and execution plans, groups the approved
backlog into GitHub-ready issues (Content / SEO / Career Pages / FAQ
Pages), generates issue and pull-request templates, and writes
brain/github-actions.json.

This script never pushes to `main`. Every suggested branch name uses
one of the allowed prefixes (feature/, ai/, content/) and every issue
instructs the implementer to open a pull request rather than commit
directly to the default branch. Real issue creation against GitHub is
opt-in (--create-issues) and requires GITHUB_TOKEN; without that flag
the script only produces the JSON plan, which is safe to run in CI on
every refresh.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import tempfile
import urllib.error
import urllib.request
from typing import Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_PLAN = REPO_ROOT / "brain" / "daily-plan.json"
DEFAULT_EXECUTION = REPO_ROOT / "brain" / "execution-plan.json"
DEFAULT_OUTPUT = REPO_ROOT / "brain" / "github-actions.json"
DEFAULT_REPOSITORY = "itvedas29/itvedas"
API_ROOT = "https://api.github.com"

ALLOWED_BRANCH_PREFIXES = ["feature/", "ai/", "content/"]
PROTECTED_BRANCHES = ["main"]

# Maps a task type (and, for "article", the originating opportunity type)
# to one of the four required buckets and a branch prefix.
CATEGORY_RULES = {
    ("article", "career_page"): ("Career Pages", "ai/"),
    ("article", "content_gap"): ("Content", "content/"),
    ("article", "high_value_course"): ("Content", "content/"),
    ("faq", None): ("FAQ Pages", "content/"),
    ("course_cta", None): ("SEO", "feature/"),
    ("internal_linking", None): ("SEO", "feature/"),
}

CAREER_SUFFIX = re.compile(r"\s+Career Path$")
CONTENT_GAP_SUFFIX = re.compile(r"\s+Content Gap$")
EXPANSION_SUFFIX = re.compile(r"\s+Expansion$")
FAQ_SUFFIX = re.compile(r"\s+FAQ$")
LINKS_SUFFIX = re.compile(r"\s+Internal Links$")

ISSUE_TEMPLATE = """## Objective
{objective}

## Why this matters
{reason}

**Category:** {category}
**Priority:** {priority} (score {score}/100)
**Related course:** {course}

## Brief
{brief_markdown}

## Branch
Create your work on a branch named:

    {branch}

Allowed prefixes only: `feature/*`, `ai/*`, `content/*`. Direct pushes to
`main` (or any protected branch) are not permitted under any circumstance.

## Acceptance criteria
- [ ] Content/CTA/links described above are implemented
- [ ] Internal links to the related course are present
- [ ] Changes are opened as a pull request against `main`, not pushed directly
- [ ] Pull request follows the ITVedas PR template

---
_This issue was generated automatically by `itvedas-brain/github-agent.py` from `brain/daily-plan.json` and `brain/execution-plan.json`._
"""

PULL_REQUEST_TEMPLATE = """## Summary
<!-- What does this PR add or change, and which issue does it close? -->

Closes #<issue-number>

## Category
- [ ] Content
- [ ] SEO
- [ ] Career Pages
- [ ] FAQ Pages

## Branch policy
- [ ] This branch name starts with `feature/`, `ai/`, or `content/`
- [ ] This PR targets `main` and was never pushed directly to `main`

## Checklist
- [ ] Content matches the linked issue's brief
- [ ] Internal links to the related course/page are present
- [ ] No leaked draft/AI scaffolding (TODOs, placeholder text) remains
- [ ] Sitemap / search index / chapter indexes updated if applicable
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate GitHub-ready issue/PR plan from the daily and execution plans.")
    parser.add_argument("--plan", type=pathlib.Path, default=DEFAULT_PLAN)
    parser.add_argument("--execution", type=pathlib.Path, default=DEFAULT_EXECUTION)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--min-score", type=int, default=0, help="Skip opportunities scoring below this threshold.")
    parser.add_argument("--create-issues", action="store_true", help="Actually create issues via the GitHub API (requires GITHUB_TOKEN).")
    return parser.parse_args()


def load_json(path: pathlib.Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def subject_for(title: str) -> str:
    for pattern in (CAREER_SUFFIX, CONTENT_GAP_SUFFIX, EXPANSION_SUFFIX, FAQ_SUFFIX, LINKS_SUFFIX):
        title = pattern.sub("", title)
    return title.strip()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "task"


def priority_label(score: int) -> str:
    if score >= 85:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def category_and_prefix(task_type: str, opportunity_type: str) -> tuple[str, str]:
    key = (task_type, opportunity_type if (task_type, opportunity_type) in CATEGORY_RULES else None)
    return CATEGORY_RULES.get(key, ("Content", "content/"))


def issue_title_for(task: dict[str, Any], category: str, subject: str) -> str:
    task_type = task["type"]
    if category == "Career Pages":
        return f"Create {subject} Career Page"
    if task_type == "faq":
        return f"Create {subject} FAQ Page"
    if task_type == "course_cta":
        return f"Add Course CTA: {subject}"
    if task_type == "internal_linking":
        return f"Add Internal Links: {subject}"
    return f"Create Article: {task['title']}"


def brief_to_markdown(brief: dict[str, Any]) -> str:
    lines = []
    for key, value in brief.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            if not value:
                continue
            lines.append(f"**{label}:**")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"- {json.dumps(item, ensure_ascii=True)}")
                else:
                    lines.append(f"- {item}")
        elif value:
            lines.append(f"**{label}:** {value}")
    return "\n".join(lines) if lines else "_No additional brief details._"


def build_issues(
    plan: dict[str, Any], execution: dict[str, Any], min_score: int
) -> list[dict[str, Any]]:
    opportunities_by_title = {opp["title"]: opp for opp in plan.get("opportunities", [])}
    issues = []

    for queue_item in execution.get("execution_queue", []):
        score = queue_item.get("score", 0)
        if score < min_score:
            continue
        opportunity_title = queue_item["priority"]
        opportunity = opportunities_by_title.get(opportunity_title, {})
        opportunity_type = queue_item.get("type") or opportunity.get("type", "content_gap")
        subject = subject_for(opportunity_title)
        course_id = queue_item.get("related_course_id")

        for task in queue_item.get("tasks", []):
            category, prefix = category_and_prefix(task["type"], opportunity_type)
            title = issue_title_for(task, category, subject)
            branch = f"{prefix}{slugify(title)}"
            objective = task["title"]
            body = ISSUE_TEMPLATE.format(
                objective=objective,
                reason=queue_item.get("reason", opportunity.get("reason", "")),
                category=category,
                priority=priority_label(score),
                score=score,
                course=course_id or "n/a",
                brief_markdown=brief_to_markdown(task.get("brief", {})),
                branch=branch,
            )

            issues.append(
                {
                    "title": title,
                    "priority": priority_label(score),
                    "category": category,
                    "score": score,
                    "task_type": task["type"],
                    "related_course_id": course_id,
                    "source_priority": opportunity_title,
                    "branch": branch,
                    "labels": ["ai-generated", category.lower().replace(" ", "-"), f"priority-{priority_label(score).lower()}"],
                    "body": body,
                }
            )

    issues.sort(key=lambda item: item["score"], reverse=True)
    return issues


def group_issues(issues: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {"Content": [], "SEO": [], "Career Pages": [], "FAQ Pages": []}
    for issue in issues:
        groups.setdefault(issue["category"], []).append(issue["title"])
    return groups


def github_request(method: str, path: str, token: str, payload: dict[str, Any] | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "itvedas-github-agent/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if data:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{API_ROOT}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"GitHub API returned {error.code}: {detail}") from error


def existing_open_issue_titles(repository: str, token: str) -> set[str]:
    owner, name = repository.split("/", 1)
    titles: set[str] = set()
    page = 1
    while True:
        items = github_request(
            "GET", f"/repos/{owner}/{name}/issues?state=open&labels=ai-generated&per_page=100&page={page}", token
        )
        if not items:
            break
        titles.update(item["title"] for item in items if "pull_request" not in item)
        if len(items) < 100:
            break
        page += 1
    return titles


def create_issues_on_github(repository: str, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    if not token:
        raise SystemExit("--create-issues requires GITHUB_TOKEN (or GH_TOKEN) to be set.")

    owner, name = repository.split("/", 1)
    already_open = existing_open_issue_titles(repository, token)
    created = []
    for issue in issues:
        if issue["title"] in already_open:
            created.append({"title": issue["title"], "status": "skipped_duplicate"})
            continue
        response = github_request(
            "POST",
            f"/repos/{owner}/{name}/issues",
            token,
            {"title": issue["title"], "body": issue["body"], "labels": issue["labels"]},
        )
        created.append({"title": issue["title"], "status": "created", "url": response.get("html_url")})
    return created


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


def main() -> int:
    args = parse_args()

    plan = load_json(args.plan, None)
    execution = load_json(args.execution, None)
    if plan is None:
        raise SystemExit(f"Daily plan not found: {args.plan}. Run decision-engine.py first.")
    if execution is None:
        raise SystemExit(f"Execution plan not found: {args.execution}. Run execution-engine.py first.")

    issues = build_issues(plan, execution, args.min_score)
    groups = group_issues(issues)

    generated_at = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    output = {
        "schema_version": 1,
        "generated_at": generated_at,
        "date": plan.get("date"),
        "repository": args.repository,
        "branch_policy": {
            "allowed_prefixes": ALLOWED_BRANCH_PREFIXES,
            "protected_branches": PROTECTED_BRANCHES,
            "rule": "Never push directly to a protected branch. All work happens on feature/*, ai/*, or content/* and merges via pull request.",
        },
        "issue_template": ISSUE_TEMPLATE,
        "pull_request_template": PULL_REQUEST_TEMPLATE,
        "groups": groups,
        "summary": {
            "total_issues": len(issues),
            "by_category": {category: len(titles) for category, titles in groups.items()},
            "by_priority": {
                label: sum(1 for issue in issues if issue["priority"] == label)
                for label in ("High", "Medium", "Low")
            },
        },
        "issues": issues,
    }

    if args.create_issues:
        output["github_creation_result"] = create_issues_on_github(args.repository, issues)

    write_json_atomic(args.output, output)

    print(f"Generated {len(issues)} issue(s) across {len([g for g in groups.values() if g])} categories.")
    print(f"Wrote GitHub action plan to {args.output}.")
    if args.create_issues:
        print("Issue creation against GitHub was attempted (see github_creation_result in the output file).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
