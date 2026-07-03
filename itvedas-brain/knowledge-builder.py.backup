#!/usr/bin/env python3
"""Build the permanent ITVedas knowledge base from repository content."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import tempfile
from collections import defaultdict
from html.parser import HTMLParser
from typing import Any, Iterable

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_MEMORY = BASE_DIR / "memory" / "repository.json"
DEFAULT_KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DEFAULT_OUTPUT = BASE_DIR / "repository_knowledge.json"

COURSES = {
    "networking": {
        "title": "Networking Fundamentals Course",
        "description": "Learn how networks move data using DNS, TCP/IP, routing, VPNs, firewalls, and subnetting.",
        "aliases": ["networking", "network", "dns", "tcp/ip", "vpn", "firewall", "subnet"],
        "technologies": ["DNS", "TCP/IP", "VPN", "Firewalls"],
        "skills": ["Network troubleshooting", "Subnetting", "DNS analysis", "Secure network design"],
    },
    "cloud": {
        "title": "Cloud Computing Course",
        "description": "Understand cloud platforms, service models, serverless systems, scaling, and cloud architecture.",
        "aliases": ["cloud", "aws", "azure", "gcp", "serverless", "s3", "ec2"],
        "technologies": ["AWS", "Microsoft Azure", "Google Cloud", "Serverless"],
        "skills": ["Cloud architecture", "Cloud deployment", "Cost awareness", "Cloud security"],
    },
    "security": {
        "title": "Cyber Security Course",
        "description": "Build practical security foundations across threats, authentication, encryption, OWASP, and Zero Trust.",
        "aliases": ["security", "cybersecurity", "hacker", "malware", "owasp", "zero trust", "encryption"],
        "technologies": ["OWASP", "Zero Trust", "TLS", "SIEM"],
        "skills": ["Threat analysis", "Security hardening", "Incident awareness", "Identity protection"],
    },
    "devops": {
        "title": "DevOps and Automation Course",
        "description": "Learn delivery automation with containers, CI/CD, infrastructure as code, and orchestration.",
        "aliases": ["devops", "docker", "kubernetes", "ci/cd", "terraform", "github actions"],
        "technologies": ["Docker", "Kubernetes", "Terraform", "GitHub Actions"],
        "skills": ["CI/CD design", "Container operations", "Infrastructure automation", "Release engineering"],
    },
    "databases": {
        "title": "Database Engineering Course",
        "description": "Learn relational and NoSQL databases, indexing, queries, replication, backup, and scaling.",
        "aliases": ["database", "sql", "nosql", "postgresql", "mongodb", "redis", "indexing"],
        "technologies": ["SQL", "PostgreSQL", "MongoDB", "Redis"],
        "skills": ["Data modeling", "Query optimization", "Database backup", "Database scaling"],
    },
    "linux": {
        "title": "Linux and Systems Administration Course",
        "description": "Build command-line, permissions, process, service, shell, and server administration skills.",
        "aliases": ["linux", "bash", "systemd", "shell", "ubuntu", "ssh", "permissions"],
        "technologies": ["Linux", "Bash", "systemd", "SSH"],
        "skills": ["Shell usage", "Service management", "Access control", "Server hardening"],
    },
    "hardware": {
        "title": "Hardware and Infrastructure Course",
        "description": "Understand CPUs, memory, storage, servers, networking hardware, and data-centre foundations.",
        "aliases": ["hardware", "cpu", "ram", "nvme", "raid", "server", "data centre"],
        "technologies": ["CPU", "RAM", "NVMe", "RAID"],
        "skills": ["Hardware selection", "Storage planning", "Server fundamentals", "Infrastructure troubleshooting"],
    },
    "compliance": {
        "title": "IT Compliance and Risk Course",
        "description": "Learn the purpose and practical controls behind GDPR, HIPAA, SOC 2, PCI DSS, and ISO 27001.",
        "aliases": ["compliance", "gdpr", "hipaa", "soc 2", "pci dss", "iso 27001", "risk"],
        "technologies": ["GDPR", "HIPAA", "SOC 2", "PCI DSS", "ISO 27001"],
        "skills": ["Control mapping", "Risk assessment", "Audit preparation", "Policy interpretation"],
    },
}

CAREER_PATHS = {
    "network_engineer": ("Network Engineer", "networking"),
    "cloud_engineer": ("Cloud Engineer", "cloud"),
    "soc_analyst": ("SOC Analyst", "security"),
    "devops_engineer": ("DevOps Engineer", "devops"),
    "database_administrator": ("Database Administrator", "databases"),
    "linux_system_administrator": ("Linux System Administrator", "linux"),
    "infrastructure_engineer": ("Hardware and Infrastructure Engineer", "hardware"),
    "compliance_analyst": ("IT Compliance Analyst", "compliance"),
}

CERTIFICATIONS = {
    "ccna": ("Cisco Certified Network Associate (CCNA)", ["ccna", "cisco certified network associate"], "networking"),
    "aws_cloud_practitioner": ("AWS Certified Cloud Practitioner", ["aws certified cloud practitioner", "cloud practitioner"], "cloud"),
    "aws_solutions_architect": ("AWS Certified Solutions Architect", ["aws certified solutions architect", "solutions architect associate"], "cloud"),
    "security_plus": ("CompTIA Security+", ["security+", "comptia security"], "security"),
    "ceh": ("Certified Ethical Hacker (CEH)", ["certified ethical hacker", " ceh "], "security"),
    "cissp": ("Certified Information Systems Security Professional (CISSP)", ["cissp", "certified information systems security professional"], "security"),
    "cka": ("Certified Kubernetes Administrator (CKA)", ["certified kubernetes administrator", " cka "], "devops"),
    "rhcsa": ("Red Hat Certified System Administrator (RHCSA)", ["rhcsa", "red hat certified system administrator"], "linux"),
    "comptia_a_plus": ("CompTIA A+", ["comptia a+", "a+ certification"], "hardware"),
    "cisa": ("Certified Information Systems Auditor (CISA)", ["cisa", "certified information systems auditor"], "compliance"),
    "iso_27001": ("ISO/IEC 27001 Certification", ["iso 27001 certification", "iso/iec 27001"], "compliance"),
}

TECHNOLOGIES = {
    "aws": ("AWS", ["aws", "amazon web services"], "cloud"),
    "azure": ("Microsoft Azure", ["azure", "microsoft cloud"], "cloud"),
    "gcp": ("Google Cloud", ["google cloud", "gcp"], "cloud"),
    "docker": ("Docker", ["docker", "container"], "devops"),
    "kubernetes": ("Kubernetes", ["kubernetes", "k8s"], "devops"),
    "terraform": ("Terraform", ["terraform", "infrastructure as code"], "devops"),
    "github_actions": ("GitHub Actions", ["github actions"], "devops"),
    "dns": ("DNS", ["dns", "domain name system"], "networking"),
    "tcp_ip": ("TCP/IP", ["tcp/ip", "tcp", "internet protocol"], "networking"),
    "vpn": ("VPN", ["vpn", "virtual private network"], "networking"),
    "owasp": ("OWASP", ["owasp"], "security"),
    "zero_trust": ("Zero Trust", ["zero trust"], "security"),
    "tls": ("TLS", ["tls", "ssl"], "security"),
    "siem": ("SIEM", ["siem"], "security"),
    "sql": ("SQL", ["sql", "relational database"], "databases"),
    "postgresql": ("PostgreSQL", ["postgresql", "postgres"], "databases"),
    "mongodb": ("MongoDB", ["mongodb"], "databases"),
    "redis": ("Redis", ["redis"], "databases"),
    "linux": ("Linux", ["linux", "ubuntu"], "linux"),
    "bash": ("Bash", ["bash", "shell scripting"], "linux"),
    "systemd": ("systemd", ["systemd"], "linux"),
    "ssh": ("SSH", ["ssh", "secure shell"], "linux"),
    "cpu": ("CPU", ["cpu", "processor"], "hardware"),
    "ram": ("RAM", ["ram", "memory"], "hardware"),
    "nvme": ("NVMe", ["nvme"], "hardware"),
    "raid": ("RAID", ["raid"], "hardware"),
    "gdpr": ("GDPR", ["gdpr"], "compliance"),
    "hipaa": ("HIPAA", ["hipaa"], "compliance"),
    "soc_2": ("SOC 2", ["soc 2", "soc2"], "compliance"),
    "pci_dss": ("PCI DSS", ["pci dss", "pci-dss"], "compliance"),
    "iso_27001": ("ISO 27001", ["iso 27001", "iso/iec 27001"], "compliance"),
}

PERSONAS = {
    "complete_beginner": {
        "title": "Complete IT Beginner",
        "signals": ["beginner", "new to it", "no experience", "start learning"],
        "recommended_courses": ["networking", "linux", "hardware"],
    },
    "career_changer": {
        "title": "IT Career Changer",
        "signals": ["career change", "switching career", "new career", "career path"],
        "recommended_courses": ["cloud", "security", "devops"],
    },
    "student": {
        "title": "Student or Early-Career Learner",
        "signals": ["student", "first job", "junior role", "entry level"],
        "recommended_courses": ["networking", "cloud", "security"],
    },
    "developer": {
        "title": "Developer Expanding Into Operations",
        "signals": ["developer", "software engineer", "deploy", "application"],
        "recommended_courses": ["devops", "cloud", "databases"],
    },
    "it_professional": {
        "title": "Working IT Professional",
        "signals": ["it professional", "administrator", "engineer", "specialize"],
        "recommended_courses": ["security", "devops", "compliance"],
    },
    "business_owner": {
        "title": "Business Owner or Technology Decision Maker",
        "signals": ["business", "company", "organization", "risk"],
        "recommended_courses": ["security", "cloud", "compliance"],
    },
}


class ContentExtractor(HTMLParser):
    BLOCK_TAGS = {"title", "h1", "h2", "h3", "h4", "p", "li", "blockquote"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.active_tag: str | None = None
        self.buffer: list[str] = []
        self.blocks: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.BLOCK_TAGS:
            self._flush()
            self.active_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag == self.active_tag:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self.active_tag:
            self.buffer.append(data)

    def _flush(self) -> None:
        if self.active_tag and self.buffer:
            text = normalize_text(" ".join(self.buffer))
            if text:
                self.blocks.append((self.active_tag, text))
        self.active_tag = None
        self.buffer = []


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ITVedas repository knowledge.")
    parser.add_argument("--memory", type=pathlib.Path, default=DEFAULT_MEMORY)
    parser.add_argument("--knowledge-dir", type=pathlib.Path, default=DEFAULT_KNOWLEDGE_DIR)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def safe_repository_path(repository_root: pathlib.Path, relative_path: str) -> pathlib.Path:
    target = (repository_root / relative_path).resolve()
    if repository_root != target and repository_root not in target.parents:
        raise ValueError(f"Unsafe repository path: {relative_path}")
    return target


def read_source(repository_root: pathlib.Path, path: str) -> dict[str, Any] | None:
    target = safe_repository_path(repository_root, path)
    if not target.is_file():
        return None

    raw = target.read_text(encoding="utf-8", errors="replace")
    suffix = target.suffix.lower()
    if suffix == ".html":
        parser = ContentExtractor()
        parser.feed(raw)
        blocks = parser.blocks
        text = normalize_text(" ".join(value for _, value in blocks))
    else:
        blocks = []
        text = normalize_text(raw)

    return {
        "path": path,
        "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "text": text,
        "blocks": blocks,
    }


def select_source_paths(memory: dict[str, Any]) -> list[str]:
    identified = memory.get("identified", {})
    selected: set[str] = set()
    for category in ("articles", "article_indexes", "news_pages", "career_pages", "apis"):
        selected.update(identified.get(category, []))

    for item in memory.get("inventory", {}).get("files", []):
        path = item.get("path", "")
        if pathlib.PurePosixPath(path).suffix.lower() == ".md":
            selected.add(path)

    return sorted(selected)


def contains_alias(text: str, aliases: Iterable[str]) -> bool:
    padded = f" {text.lower()} "
    return any(alias.lower() in padded for alias in aliases)


def course_for_source(source: dict[str, Any]) -> str | None:
    text = source["text"].lower()
    path = source["path"].lower()
    scores: dict[str, int] = {}
    for course_id, course in COURSES.items():
        score = sum(text.count(alias.lower()) for alias in course["aliases"])
        if f"/{course_id}/" in f"/{path}" or f"-{course_id}" in path:
            score += 20
        scores[course_id] = score
    course_id, score = max(scores.items(), key=lambda item: item[1])
    return course_id if score else None


def extract_faqs(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    faqs: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source in sources:
        blocks = source["blocks"]
        for index, (tag, value) in enumerate(blocks):
            if tag not in {"h2", "h3", "h4"} or not value.endswith("?"):
                continue
            answer = ""
            for next_tag, next_value in blocks[index + 1 : index + 5]:
                if next_tag in {"h2", "h3", "h4"}:
                    break
                if next_tag in {"p", "li", "blockquote"}:
                    answer = next_value
                    break
            if not answer:
                continue
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            course_id = course_for_source(source)
            faqs.append(
                {
                    "id": stable_id("faq", value),
                    "question": value,
                    "answer": answer,
                    "source_path": source["path"],
                    "related_course_id": course_id,
                }
            )
    return faqs


def build_courses(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    related: dict[str, list[str]] = defaultdict(list)
    for source in sources:
        course_id = course_for_source(source)
        if course_id and source["path"].lower().endswith((".html", ".md")):
            related[course_id].append(source["path"])

    items = []
    for course_id, course in COURSES.items():
        items.append(
            {
                "id": course_id,
                "title": course["title"],
                "chapter": course_id,
                "description": course["description"],
                "technologies": course["technologies"],
                "skills_taught": course["skills"],
                "content_paths": sorted(set(related[course_id])),
                "recommended_career_paths": [
                    path_id
                    for path_id, (_, linked_course) in CAREER_PATHS.items()
                    if linked_course == course_id
                ],
            }
        )
    return items


def build_certifications(all_text: str) -> list[dict[str, Any]]:
    items = []
    for cert_id, (title, aliases, course_id) in CERTIFICATIONS.items():
        if contains_alias(all_text, aliases):
            items.append(
                {
                    "id": cert_id,
                    "title": title,
                    "related_course_id": course_id,
                    "relationship": "supported_by_course",
                }
            )
    return items


def build_technologies(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for tech_id, (title, aliases, course_id) in TECHNOLOGIES.items():
        paths = [
            source["path"]
            for source in sources
            if contains_alias(source["text"], aliases)
        ]
        if paths:
            items.append(
                {
                    "id": tech_id,
                    "title": title,
                    "related_course_id": course_id,
                    "content_paths": sorted(paths),
                }
            )
    return items


def build_career_paths(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    career_sources = [
        source for source in sources if source["path"] in {"career-paths.html", "career-navigator.html"}
    ]
    items = []
    for path_id, (title, course_id) in CAREER_PATHS.items():
        aliases = [title, title.replace(" and ", " & ")]
        paths = [
            source["path"]
            for source in career_sources
            if contains_alias(source["text"], aliases)
        ]
        items.append(
            {
                "id": path_id,
                "title": title,
                "recommended_course_id": course_id,
                "recommended_course_title": COURSES[course_id]["title"],
                "skills": COURSES[course_id]["skills"],
                "source_paths": sorted(paths),
            }
        )
    return items


def build_personas(all_text: str) -> list[dict[str, Any]]:
    items = []
    for persona_id, persona in PERSONAS.items():
        evidence = [
            signal for signal in persona["signals"] if signal in all_text.lower()
        ]
        items.append(
            {
                "id": persona_id,
                "title": persona["title"],
                "signals": persona["signals"],
                "matched_signals": evidence,
                "recommended_course_ids": persona["recommended_courses"],
            }
        )
    return items


def build_relationships(
    courses: list[dict[str, Any]],
    certifications: list[dict[str, Any]],
    career_paths: list[dict[str, Any]],
    technologies: list[dict[str, Any]],
    personas: list[dict[str, Any]],
    faqs: list[dict[str, Any]],
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []

    def add(source_type: str, source_id: str, relation: str, target_type: str, target_id: str) -> None:
        edges.append(
            {
                "source_type": source_type,
                "source_id": source_id,
                "relationship": relation,
                "target_type": target_type,
                "target_id": target_id,
            }
        )

    for path in career_paths:
        add("career_path", path["id"], "recommended_course", "course", path["recommended_course_id"])
    for cert in certifications:
        add("certification", cert["id"], "supported_by", "course", cert["related_course_id"])
    for technology in technologies:
        add("technology", technology["id"], "taught_in", "course", technology["related_course_id"])
    for persona in personas:
        for course_id in persona["recommended_course_ids"]:
            add("student_persona", persona["id"], "recommended_course", "course", course_id)
    for course in courses:
        for path in course["content_paths"]:
            add("course", course["id"], "includes_content", "repository_file", path)
    for faq in faqs:
        if faq["related_course_id"]:
            add("faq", faq["id"], "answered_by", "course", faq["related_course_id"])

    return sorted(
        edges,
        key=lambda edge: (
            edge["source_type"],
            edge["source_id"],
            edge["relationship"],
            edge["target_id"],
        ),
    )


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
    memory_path = args.memory.resolve()
    if not memory_path.is_file():
        raise SystemExit(
            f"Repository memory not found: {memory_path}. Run repo-scanner.py first."
        )

    memory = json.loads(memory_path.read_text(encoding="utf-8"))
    repository_root = BASE_DIR.parent
    source_paths = select_source_paths(memory)
    sources = [
        source
        for path in source_paths
        if (source := read_source(repository_root, path)) is not None
    ]
    all_text = " ".join(source["text"] for source in sources)
    generated_at = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    courses = build_courses(sources)
    certifications = build_certifications(all_text)
    career_paths = build_career_paths(sources)
    technologies = build_technologies(sources)
    personas = build_personas(all_text)
    faqs = extract_faqs(sources)
    relationships = build_relationships(
        courses, certifications, career_paths, technologies, personas, faqs
    )

    collections = {
        "courses.json": courses,
        "certifications.json": certifications,
        "career_paths.json": career_paths,
        "technologies.json": technologies,
        "student_personas.json": personas,
        "faq.json": faqs,
    }

    for filename, items in collections.items():
        write_json_atomic(
            args.knowledge_dir / filename,
            {
                "schema_version": 1,
                "generated_at": generated_at,
                "source_repository": memory["source"]["repository"],
                "items": items,
            },
        )

    source_manifest = [
        {"path": source["path"], "sha256": source["sha256"]} for source in sources
    ]
    knowledge_base = {
        "schema_version": 1,
        "generated_at": generated_at,
        "name": "ITVedas Repository Knowledge Base",
        "source": memory["source"],
        "summary": {
            "sources_scanned": len(sources),
            "courses": len(courses),
            "certifications": len(certifications),
            "career_paths": len(career_paths),
            "technologies": len(technologies),
            "student_personas": len(personas),
            "faqs": len(faqs),
            "relationships": len(relationships),
        },
        "collections": {
            "courses": "knowledge/courses.json",
            "certifications": "knowledge/certifications.json",
            "career_paths": "knowledge/career_paths.json",
            "technologies": "knowledge/technologies.json",
            "student_personas": "knowledge/student_personas.json",
            "faq": "knowledge/faq.json",
        },
        "course_recommendations": [
            {
                "career_path_id": path["id"],
                "career_path": path["title"],
                "course_id": path["recommended_course_id"],
                "course": path["recommended_course_title"],
            }
            for path in career_paths
        ],
        "skills_taught": {
            course["id"]: course["skills_taught"] for course in courses
        },
        "relationships": relationships,
        "source_manifest": source_manifest,
    }
    write_json_atomic(args.output, knowledge_base)

    print(
        f"Scanned {len(sources)} content sources and generated "
        f"{len(collections)} collections with {len(relationships)} relationships."
    )
    print(f"Wrote permanent knowledge base to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
