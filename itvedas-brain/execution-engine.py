#!/usr/bin/env python3
"""Phase 4 - Execution Engine.

Turns the Phase 3 daily plan's recommended actions into concrete,
ready-to-hand-off briefs: article briefs, FAQ briefs, course CTA
recommendations, and internal linking recommendations.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import tempfile
from typing import Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_PLAN = REPO_ROOT / "brain" / "daily-plan.json"
DEFAULT_KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DEFAULT_OUTPUT = REPO_ROOT / "brain" / "execution-plan.json"

CAREER_SUFFIX = re.compile(r"\s+Career Path$")
CONTENT_GAP_SUFFIX = re.compile(r"\s+Content Gap$")
EXPANSION_SUFFIX = re.compile(r"\s+Expansion$")
FAQ_SUFFIX = re.compile(r"\s+FAQ$")
LINKS_SUFFIX = re.compile(r"\s+Internal Links$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the ITVedas execution plan from the daily plan.")
    parser.add_argument("--plan", type=pathlib.Path, default=DEFAULT_PLAN)
    parser.add_argument("--knowledge-dir", type=pathlib.Path, default=DEFAULT_KNOWLEDGE_DIR)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json(path: pathlib.Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_items(path: pathlib.Path) -> list[dict[str, Any]]:
    return load_json(path, {"items": []}).get("items", [])


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def subject_for(opportunity: dict[str, Any]) -> str:
    """Strip the type suffix off an opportunity title to get its plain subject."""
    title = opportunity["title"]
    for pattern in (CAREER_SUFFIX, CONTENT_GAP_SUFFIX, EXPANSION_SUFFIX, FAQ_SUFFIX, LINKS_SUFFIX):
        title = pattern.sub("", title)
    return title.strip()


def make_article_task(
    opportunity: dict[str, Any], course: dict[str, Any] | None
) -> dict[str, Any]:
    subject = subject_for(opportunity)
    opp_type = opportunity["type"]

    if opp_type == "career_page":
        title = f"How to Become a {subject} in India"
        keyword = f"how to become a {subject.lower()} in india"
    elif opp_type == "high_value_course":
        title = f"{subject}: The Complete 2026 Guide"
        keyword = f"{subject.lower()} complete guide 2026"
    else:
        title = f"What is {subject}? A Complete Beginner's Guide"
        keyword = f"what is {subject.lower()} beginner guide"

    skills = course.get("skills_taught", []) if course else []
    outline = ["Introduction and why it matters", *[f"Cover: {skill}" for skill in skills[:4]], "Conclusion and next steps"]

    return {
        "type": "article",
        "title": title,
        "brief": {
            "target_keyword": keyword,
            "related_course_id": course["id"] if course else opportunity.get("related_course_id"),
            "related_course_title": course["title"] if course else None,
            "suggested_outline": outline,
            "call_to_action": (
                f"Enroll in the {course['title']}" if course else "Link to the most relevant ITVedas course"
            ),
        },
    }


def make_faq_task(
    opportunity: dict[str, Any], course: dict[str, Any] | None, existing_faqs: list[dict[str, Any]]
) -> dict[str, Any]:
    subject = subject_for(opportunity)
    title = f"{subject} FAQ"

    if opportunity["type"] == "career_page":
        questions = [
            f"What does a {subject} do day to day?",
            f"What skills do I need to become a {subject}?",
            f"Which ITVedas course should I take to become a {subject}?",
            f"Is {subject} a good career path in 2026?",
        ]
    else:
        questions = [
            f"What is {subject}?",
            f"Who should learn {subject}?",
            f"What career paths use {subject} skills?",
            f"Which course covers {subject}?",
        ]

    similar = [faq["question"] for faq in existing_faqs if faq.get("related_course_id") == (course["id"] if course else None)]

    return {
        "type": "faq",
        "title": title,
        "brief": {
            "related_course_id": course["id"] if course else opportunity.get("related_course_id"),
            "suggested_questions": questions,
            "existing_related_faqs": similar[:3],
        },
    }


def make_cta_task(opportunity: dict[str, Any], course: dict[str, Any] | None) -> dict[str, Any]:
    subject = subject_for(opportunity)
    course_title = course["title"] if course else "the relevant ITVedas course"
    placements = course.get("content_paths", []) if course else []

    return {
        "type": "course_cta",
        "title": f"Add {course_title} CTA to {subject} content",
        "brief": {
            "related_course_id": course["id"] if course else opportunity.get("related_course_id"),
            "cta_text": f"Ready to pursue {subject}? Enroll in our {course_title}.",
            "placement_pages": placements,
        },
    }


def make_linking_task(
    opportunity: dict[str, Any], course: dict[str, Any] | None, technologies: list[dict[str, Any]]
) -> dict[str, Any]:
    subject = subject_for(opportunity)
    course_id = course["id"] if course else opportunity.get("related_course_id")
    uncovered = [tech for tech in technologies if tech["related_course_id"] == course_id and not tech.get("content_paths")]
    anchors = [
        {"anchor_text": tech["title"], "target": f"articles/{course_id}/index.html"}
        for tech in uncovered
    ]

    return {
        "type": "internal_linking",
        "title": f"Link {subject} content internally",
        "brief": {
            "related_course_id": course_id,
            "anchor_recommendations": anchors,
        },
    }


ACTION_HANDLERS = {
    "Create article": make_article_task,
    "Create FAQ": make_faq_task,
    "Add course CTA": make_cta_task,
    "Add internal links": make_linking_task,
}


def build_tasks(
    opportunity: dict[str, Any],
    courses_by_id: dict[str, dict[str, Any]],
    existing_faqs: list[dict[str, Any]],
    technologies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    course = courses_by_id.get(opportunity.get("related_course_id"))
    tasks = []
    for action in opportunity.get("actions", []):
        handler = ACTION_HANDLERS.get(action)
        if handler is None:
            continue
        if handler is make_article_task:
            tasks.append(make_article_task(opportunity, course))
        elif handler is make_faq_task:
            tasks.append(make_faq_task(opportunity, course, existing_faqs))
        elif handler is make_cta_task:
            tasks.append(make_cta_task(opportunity, course))
        elif handler is make_linking_task:
            tasks.append(make_linking_task(opportunity, course, technologies))
    return tasks


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
    if plan is None:
        raise SystemExit(f"Daily plan not found: {args.plan}. Run decision-engine.py first.")

    courses_by_id = index_by_id(load_items(args.knowledge_dir / "courses.json"))
    existing_faqs = load_items(args.knowledge_dir / "faq.json")
    technologies = load_items(args.knowledge_dir / "technologies.json")

    opportunities = plan.get("opportunities", [])
    execution_queue = []
    for opportunity in opportunities:
        tasks = build_tasks(opportunity, courses_by_id, existing_faqs, technologies)
        if not tasks:
            continue
        execution_queue.append(
            {
                "priority": opportunity["title"],
                "score": opportunity["score"],
                "type": opportunity["type"],
                "related_course_id": opportunity.get("related_course_id"),
                "reason": opportunity["reason"],
                "tasks": tasks,
            }
        )

    generated_at = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    top = execution_queue[0] if execution_queue else None
    execution_plan = {
        "schema_version": 1,
        "generated_at": generated_at,
        "date": plan.get("date"),
        "priority": top["priority"] if top else None,
        "score": top["score"] if top else 0,
        "tasks": [{"type": task["type"], "title": task["title"]} for task in top["tasks"]] if top else [],
        "execution_queue": execution_queue,
    }

    write_json_atomic(args.output, execution_plan)

    total_tasks = sum(len(item["tasks"]) for item in execution_queue)
    print(f"Built {len(execution_queue)} prioritized work items with {total_tasks} total briefs.")
    if top:
        print(f"Top priority: {top['priority']} (score {top['score']})")
    print(f"Wrote execution plan to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
