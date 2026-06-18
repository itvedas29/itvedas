#!/usr/bin/env python3
"""Phase 3 - Decision Engine.

Reads the Phase 2 knowledge base plus the live autopilot state and turns
them into a scored, ranked daily content-priority plan.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import tempfile
from typing import Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DEFAULT_REPOSITORY_KNOWLEDGE = BASE_DIR / "repository_knowledge.json"
DEFAULT_ARTICLE_STATE = REPO_ROOT / "brain" / "state.json"
DEFAULT_NEWS_STATE = REPO_ROOT / "brain" / "news_state.json"
DEFAULT_OUTPUT = REPO_ROOT / "brain" / "daily-plan.json"

# Scoring weights (must sum to 1.0).
WEIGHTS = {
    "course_relevance": 0.40,
    "content_gap_severity": 0.25,
    "student_demand": 0.20,
    "seo_opportunity": 0.10,
    "competition": 0.05,
}

# Maps a course id to the topic label used by the article/news agents.
COURSE_TOPIC_LABELS = {
    "networking": "Networking",
    "cloud": "Cloud",
    "security": "Security",
    "devops": "DevOps",
    "databases": "Databases",
    "linux": "Linux",
    "hardware": "Hardware",
    "compliance": "Compliance",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the ITVedas daily content priority plan.")
    parser.add_argument("--knowledge-dir", type=pathlib.Path, default=DEFAULT_KNOWLEDGE_DIR)
    parser.add_argument("--repository-knowledge", type=pathlib.Path, default=DEFAULT_REPOSITORY_KNOWLEDGE)
    parser.add_argument("--article-state", type=pathlib.Path, default=DEFAULT_ARTICLE_STATE)
    parser.add_argument("--news-state", type=pathlib.Path, default=DEFAULT_NEWS_STATE)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json(path: pathlib.Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_items(path: pathlib.Path) -> list[dict[str, Any]]:
    data = load_json(path, {"items": []})
    return data.get("items", [])


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0 if value <= low else 100.0
    pct = (value - low) / (high - low) * 100
    return max(0.0, min(100.0, pct))


def round_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def build_course_profiles(
    courses: list[dict[str, Any]],
    career_paths: list[dict[str, Any]],
    certifications: list[dict[str, Any]],
    technologies: list[dict[str, Any]],
    personas: list[dict[str, Any]],
    faqs: list[dict[str, Any]],
    article_topic_counts: dict[str, int],
    news_topic_counts: dict[str, int],
) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}

    for course in courses:
        course_id = course["id"]
        career_count = sum(1 for path in career_paths if path["recommended_course_id"] == course_id)
        cert_count = sum(1 for cert in certifications if cert["related_course_id"] == course_id)
        tech_for_course = [tech for tech in technologies if tech["related_course_id"] == course_id]
        persona_count = sum(
            1 for persona in personas if course_id in persona.get("recommended_course_ids", [])
        )
        faq_count = sum(1 for faq in faqs if faq.get("related_course_id") == course_id)
        content_paths_count = len(course.get("content_paths", []))
        topic_label = COURSE_TOPIC_LABELS.get(course_id, course.get("title", course_id))
        article_count = article_topic_counts.get(topic_label, 0)
        news_count = news_topic_counts.get(topic_label, 0)
        uncovered_terms = [tech for tech in tech_for_course if not tech.get("content_paths")]
        uncovered_certs = [
            cert for cert in certifications
            if cert["related_course_id"] == course_id
        ]

        profiles[course_id] = {
            "course": course,
            "career_count": career_count,
            "cert_count": cert_count,
            "tech_count": len(tech_for_course),
            "tech_for_course": tech_for_course,
            "persona_count": persona_count,
            "faq_count": faq_count,
            "content_paths_count": content_paths_count,
            "article_count": article_count,
            "news_count": news_count,
            "uncovered_technologies": uncovered_terms,
            "certs_for_course": uncovered_certs,
        }

    relevance_raw = {
        cid: profile["career_count"] * 3 + profile["cert_count"] * 2 + profile["tech_count"] + profile["persona_count"] * 2
        for cid, profile in profiles.items()
    }
    demand_raw = {
        cid: profile["persona_count"] * 3 + profile["faq_count"] * 2 + profile["news_count"] + profile["article_count"] * 0.5
        for cid, profile in profiles.items()
    }

    rel_values = list(relevance_raw.values()) or [0]
    dem_values = list(demand_raw.values()) or [0]

    for course_id, profile in profiles.items():
        profile["relevance_score"] = normalize(relevance_raw[course_id], min(rel_values), max(rel_values))
        profile["demand_score"] = normalize(demand_raw[course_id], min(dem_values), max(dem_values))
        content_gap_raw = 100.0 if profile["content_paths_count"] == 0 else max(
            0.0, 100.0 - profile["content_paths_count"] * 15.0
        )
        profile["content_gap_score"] = content_gap_raw
        seo_raw = len(profile["uncovered_technologies"]) * 25.0
        profile["seo_score"] = min(100.0, seo_raw)
        competition_raw = 100.0 - min(100.0, profile["news_count"] * 5.0)
        profile["competition_score"] = competition_raw
        profile["composite_score"] = (
            WEIGHTS["course_relevance"] * profile["relevance_score"]
            + WEIGHTS["content_gap_severity"] * profile["content_gap_score"]
            + WEIGHTS["student_demand"] * profile["demand_score"]
            + WEIGHTS["seo_opportunity"] * profile["seo_score"]
            + WEIGHTS["competition"] * profile["competition_score"]
        )

    return profiles


def score_opportunity(
    relevance: float, content_gap: float, demand: float, seo: float, competition: float
) -> int:
    composite = (
        WEIGHTS["course_relevance"] * relevance
        + WEIGHTS["content_gap_severity"] * content_gap
        + WEIGHTS["student_demand"] * demand
        + WEIGHTS["seo_opportunity"] * seo
        + WEIGHTS["competition"] * competition
    )
    return round_score(composite)


def find_content_gaps(profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    opportunities = []
    for course_id, profile in profiles.items():
        if profile["content_gap_score"] <= 0:
            continue
        course = profile["course"]
        score = score_opportunity(
            profile["relevance_score"],
            profile["content_gap_score"],
            profile["demand_score"],
            profile["seo_score"],
            profile["competition_score"],
        )
        opportunities.append(
            {
                "type": "content_gap",
                "title": f"{course['title']} Content Gap",
                "score": score,
                "reason": (
                    f"Course exists but only {profile['content_paths_count']} supporting page(s) "
                    "cover it; demand and relevance outpace coverage."
                ),
                "actions": ["Create article", "Add course CTA", "Add internal links"],
                "related_course_id": course_id,
            }
        )
    return opportunities


def find_missing_career_pages(
    profiles: dict[str, dict[str, Any]], career_paths: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    opportunities = []
    for path in career_paths:
        if path.get("source_paths"):
            continue
        course_id = path["recommended_course_id"]
        profile = profiles.get(course_id)
        if profile is None:
            continue
        score = score_opportunity(
            profile["relevance_score"],
            100.0,  # zero dedicated career-path content is treated as a full gap
            profile["demand_score"],
            profile["seo_score"],
            profile["competition_score"],
        )
        opportunities.append(
            {
                "type": "career_page",
                "title": f"{path['title']} Career Path",
                "score": score,
                "reason": (
                    f"Course exists ({path['recommended_course_title']}) but no dedicated "
                    f"{path['title']} career page or article was found."
                ),
                "actions": ["Create article", "Create FAQ", "Add course CTA"],
                "related_course_id": course_id,
            }
        )
    return opportunities


def find_missing_faq_pages(profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    opportunities = []
    for course_id, profile in profiles.items():
        if profile["faq_count"] > 0:
            continue
        course = profile["course"]
        score = score_opportunity(
            profile["relevance_score"],
            max(profile["content_gap_score"], 60.0),
            profile["demand_score"],
            profile["seo_score"],
            profile["competition_score"],
        )
        opportunities.append(
            {
                "type": "faq_gap",
                "title": f"{course['title']} FAQ",
                "score": score,
                "reason": (
                    f"{course['title']} has no extracted FAQ content; student questions "
                    "about this topic are currently unanswered on-site."
                ),
                "actions": ["Create FAQ", "Add internal links"],
                "related_course_id": course_id,
            }
        )
    return opportunities


def find_high_value_courses(profiles: dict[str, dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    candidates = [
        profile for profile in profiles.values() if profile["content_paths_count"] <= 2
    ]
    candidates.sort(key=lambda profile: profile["composite_score"], reverse=True)
    opportunities = []
    for profile in candidates[:limit]:
        course = profile["course"]
        score = round_score(profile["composite_score"])
        opportunities.append(
            {
                "type": "high_value_course",
                "title": f"{course['title']} Expansion",
                "score": score,
                "reason": (
                    f"High relevance ({profile['career_count']} career path(s), "
                    f"{profile['cert_count']} certification(s)) with only "
                    f"{profile['content_paths_count']} supporting page(s) published."
                ),
                "actions": ["Create article", "Create FAQ", "Add course CTA"],
                "related_course_id": profile["course"]["id"],
            }
        )
    return opportunities


def find_internal_linking_gaps(profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    opportunities = []
    for course_id, profile in profiles.items():
        uncovered = profile["uncovered_technologies"]
        if not uncovered:
            continue
        course = profile["course"]
        names = ", ".join(tech["title"] for tech in uncovered[:4])
        score = score_opportunity(
            profile["relevance_score"],
            min(100.0, len(uncovered) * 20.0),
            profile["demand_score"],
            profile["seo_score"],
            profile["competition_score"],
        )
        opportunities.append(
            {
                "type": "internal_linking",
                "title": f"{course['title']} Internal Links",
                "score": score,
                "reason": (
                    f"{len(uncovered)} technology term(s) tied to this course "
                    f"({names}) appear in no content page and are not internally linked."
                ),
                "actions": ["Add internal links", "Add course CTA"],
                "related_course_id": course_id,
            }
        )
    return opportunities


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

    courses = load_items(args.knowledge_dir / "courses.json")
    career_paths = load_items(args.knowledge_dir / "career_paths.json")
    certifications = load_items(args.knowledge_dir / "certifications.json")
    technologies = load_items(args.knowledge_dir / "technologies.json")
    personas = load_items(args.knowledge_dir / "student_personas.json")
    faqs = load_items(args.knowledge_dir / "faq.json")
    repository_knowledge = load_json(args.repository_knowledge, {})
    article_state = load_json(args.article_state, {})
    news_state = load_json(args.news_state, [])

    if not courses:
        raise SystemExit(
            f"No courses found under {args.knowledge_dir}. Run knowledge-builder.py first."
        )

    article_topic_counts = article_state.get("topic_counts", {})
    news_topic_counts: dict[str, int] = {}
    for record in news_state:
        topic = record.get("topic", "General")
        news_topic_counts[topic] = news_topic_counts.get(topic, 0) + 1

    profiles = build_course_profiles(
        courses, career_paths, certifications, technologies, personas, faqs,
        article_topic_counts, news_topic_counts,
    )

    opportunities: list[dict[str, Any]] = []
    opportunities += find_content_gaps(profiles)
    opportunities += find_missing_career_pages(profiles, career_paths)
    opportunities += find_missing_faq_pages(profiles)
    opportunities += find_high_value_courses(profiles)
    opportunities += find_internal_linking_gaps(profiles)

    opportunities.sort(key=lambda item: item["score"], reverse=True)

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    generated_at = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    if opportunities:
        top = opportunities[0]
        top_priority = {
            "date": today,
            "top_priority": top["title"],
            "score": top["score"],
            "reason": top["reason"],
            "actions": top["actions"],
        }
    else:
        top_priority = {
            "date": today,
            "top_priority": None,
            "score": 0,
            "reason": "No actionable content opportunities were found.",
            "actions": [],
        }

    plan = {
        "schema_version": 1,
        "generated_at": generated_at,
        "date": today,
        "weights": WEIGHTS,
        "source_repository": repository_knowledge.get("source", {}).get("repository"),
        **top_priority,
        "summary": {
            "total_opportunities": len(opportunities),
            "by_type": {
                opp_type: sum(1 for opp in opportunities if opp["type"] == opp_type)
                for opp_type in sorted({opp["type"] for opp in opportunities})
            },
        },
        "opportunities": opportunities,
    }

    write_json_atomic(args.output, plan)

    print(f"Evaluated {len(opportunities)} opportunities across 5 objectives.")
    if opportunities:
        print(f"Top priority: {opportunities[0]['title']} (score {opportunities[0]['score']})")
    print(f"Wrote daily plan to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
