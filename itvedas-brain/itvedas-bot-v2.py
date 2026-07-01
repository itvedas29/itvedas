#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         ITVedas Brain Bot v2 — Full Autonomous Content Intelligence         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Skills integrated from 100+ GitHub AI repos across 6 topic areas:         ║
║                                                                              ║
║  MEMORY & STATEFUL AGENTS                                                    ║
║  • coleam00/second-brain-starter  — SOUL.md, USER.md, heartbeat, memory    ║
║  • letta-ai/letta                 — stateful self-improving agent loops     ║
║  • microsoft/autogen              — multi-agent programming patterns        ║
║  • zhayujie/CowAgent              — skill tree + tool harness              ║
║  • cortex-tms/cortex-tms          — tiered memory system (working/episodic) ║
║                                                                              ║
║  SEO & CONTENT INTELLIGENCE                                                  ║
║  • norahe0304-art/30x-seo         — 24 production SEO skills               ║
║  • rediumvex/seo-blog-writer      — 6 anti-detection writing rules         ║
║  • x0u0an/topic-cluster-architect — 10-step pillar/cluster strategy        ║
║  • dongbeixiaohuo/writing-agent   — evidence anchoring + humanization gate ║
║  • kristianfreeman/aiwriter       — SERP-driven article generation         ║
║  • kgarbacinski/AutoViralAI       — self-learning viral content research   ║
║                                                                              ║
║  DATA & RESEARCH                                                             ║
║  • e2b-dev/code-interpreter       — AI-driven data analysis patterns       ║
║  • starpig1129/DATAGEN            — multi-agent research + report writing  ║
║  • zebbern/knowledge-assistant    — RAG on custom knowledge files          ║
║  • divyeshmutha12/AI-Research-Asst— LangGraph + FAISS multi-agent RAG     ║
║                                                                              ║
║  CHATBOT & WEBSITE INTELLIGENCE                                              ║
║  • kaymen99/AI-Sales-agent        — product recommendation patterns        ║
║  • sitechat/raksbisht             — website content RAG                    ║
║  • RumenDamyanov/npm-chatbot      — multi-provider chatbot patterns        ║
║                                                                              ║
║  DESIGN INTELLIGENCE                                                         ║
║  • bitjaru/styleseed              — 74 rules: spatial rhythm, 8px grid     ║
║  • Laith0003/ux-skill             — 152 anti-AI-slop rules + linter        ║
║  • frhscopex/design-skill-os      — 161 rules from design masters          ║
║  • funboy322/avoid-ai-design      — anti-pattern detection + rewrite       ║
║  • Sakaax/ux-pilot                — 376 UX rules co-pilot                  ║
║  • S0ulFood/design-cognition-skill— 4-role design thinking framework       ║
║                                                                              ║
║  TASK MANAGEMENT (60 repos)                                                  ║
║  • dongshuyan/compass-skills      — task-clarifier, task-forest DAG        ║
║  • builderz-labs/mission-control  — multi-agent task orchestration         ║
║  • saltbo/agent-kanban            — agent-first kanban mission control      ║
║  • cortex-tms                     — tiered memory (working/episodic/arch)  ║
║  • jpicklyk/task-orchestrator     — server-enforced workflow discipline     ║
║  • JamesShi96/project-butler      — session logs + project documentation   ║
║  • kanban-md/antopolskiy          — file-based kanban for agentic loops    ║
║                                                                              ║
║  PIPELINE (every run):                                                       ║
║  1. MEMORY     — load brain, sync with disk, tiered memory restore          ║
║  2. RESEARCH   — trending signals + competitor gap analysis                 ║
║  3. TOPIC      — intelligent pick (never repeats, chapter-balanced)         ║
║  4. CLARIFY    — task-clarifier validates scope + anchors evidence          ║
║  5. WRITE      — SEO article with anchor facts + humanization gate          ║
║  6. QA GATE    — self-review, rewrite weak sections                         ║
║  7. DESIGN     — anti-slop linter, forbidden pattern check                 ║
║  8. HTML       — full page with ToC, reading time, FAQ schema               ║
║  9. PUBLISH    — GitHub API direct push                                     ║
║  10. INDEX     — update chapter index page + sitemap                        ║
║  11. MEMORY    — save published article, update knowledge graph             ║
║  12. HANDOFF   — heartbeat + session handoff for next run                   ║
║                                                                              ║
║  Requires only: ANTHROPIC_API_KEY + GITHUB_TOKEN                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import base64
import datetime
import html as html_module
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# ─── paths ────────────────────────────────────────────────────────────────────
ROOT        = pathlib.Path(__file__).resolve().parent.parent
ARTICLES    = ROOT / "articles"
BRAIN_DIR   = pathlib.Path(__file__).resolve().parent
MEMORY_DIR  = BRAIN_DIR / "memory"
STATE_DIR   = BRAIN_DIR / "state"
MEMORY_FILE = MEMORY_DIR / "bot_memory.json"
SOUL_FILE   = MEMORY_DIR / "SOUL.md"
USER_FILE   = MEMORY_DIR / "USER.md"
HEARTBEAT   = STATE_DIR  / "heartbeat.json"
KNOWLEDGE_GRAPH_FILE = MEMORY_DIR / "knowledge_graph.json"

MEMORY_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)

# ─── config ───────────────────────────────────────────────────────────────────
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO    = os.environ.get("GITHUB_REPOSITORY", "itvedas29/itvedas")
GITHUB_BRANCH  = os.environ.get("GITHUB_BRANCH", "main")
GA4_ID         = os.environ.get("GA4_ID", "G-D98BFZSJYP")
SITE_URL       = "https://itvedas.com"
SITE_NAME      = "ITVedas"
MODEL          = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# ─────────────────────────────────────────────────────────────────────────────
#  BOT SOUL — identity loaded into every Claude call (second-brain-starter)
# ─────────────────────────────────────────────────────────────────────────────
BOT_SOUL = """You are the ITVedas Content Brain — the autonomous intelligence behind itvedas.com,
an IT education platform that explains complex technology in plain English for complete beginners.

IDENTITY (letta-ai stateful agent pattern):
- You remember everything you've written and never repeat a topic
- You learn from each article to improve the next one
- You self-review ruthlessly — low-quality output never ships
- You operate with editorial standards, not just content generation

SEO RULES (norahe0304-art/30x-seo — 24 production skills):
- Title: exact keyword, under 60 chars, front-loaded with keyword
- Meta description: 150-160 chars, includes keyword, ends with a promise
- H1 = title. H2s = semantic keyword variations (LSI keywords)
- First paragraph: answers the question within 50 words (E-E-A-T signal)
- FAQ schema: minimum 3 real questions people search for
- Internal links: reference related ITVedas topics naturally
- Slug: 3-5 words, lowercase, hyphens, no stop words

ANTI-AI-DETECTION (rediumvex/seo-blog-writer + dongbeixiaohuo/writing-agent):
- Vary sentence lengths: mix 6-word and 25-word sentences in same paragraph
- First-person occasionally: "Here's what I mean..." "Think of it this way..."
- Specific numbers and real examples: "~50ms" "AWS EC2 t3.micro" "GitHub Actions"
- Alternate paragraph lengths: 1-sentence, 3-sentence, 4-sentence — never uniform
- Vary list lengths: 3 or 7 items — never always exactly 5
- Fact-anchor every claim: specific measurement, company, or example
- Never start two consecutive paragraphs with the same word

DESIGN RULES (styleseed + ux-skill + design-skill-os):
- Lead with the answer immediately — never "In today's digital world..."
- Short paragraphs: 2-4 sentences, active voice
- Real examples with names and numbers
- NEVER: elevate, seamless, powerful, revolutionary, game-changer, leverage, utilize, paradigm
- Code examples in <code>, terminal commands in <pre><code>
- NO emoji bullets in content

MEMORY DISCIPLINE (coleam00/second-brain-starter):
- Check memory FIRST before any topic decision
- Save every article immediately after publishing
- Build knowledge graph: track which topics relate to which
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTERS — all site chapters with metadata
# ─────────────────────────────────────────────────────────────────────────────
CHAPTERS = {
    "networking": {"name": "Networking",      "emoji": "🌐", "color": "#FF6B35", "num": "01"},
    "cloud":      {"name": "Cloud Computing", "emoji": "☁️", "color": "#3B82F6", "num": "02"},
    "security":   {"name": "Security",        "emoji": "🔐", "color": "#10B981", "num": "03"},
    "devops":     {"name": "DevOps",          "emoji": "⚙️", "color": "#8B5CF6", "num": "04"},
    "databases":  {"name": "Databases",       "emoji": "🗄️", "color": "#F59E0B", "num": "05"},
    "linux":      {"name": "Linux",           "emoji": "🐧", "color": "#EF4444", "num": "06"},
    "hardware":   {"name": "Hardware",        "emoji": "🖥️", "color": "#6366F1", "num": "07"},
    "compliance": {"name": "Compliance",      "emoji": "📋", "color": "#14B8A6", "num": "08"},
    "cve":        {"name": "CVE Database",    "emoji": "🛡️", "color": "#EF4444", "num": "09"},
}

# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC SEEDS — high-value IT search queries (research-agent + AutoViralAI)
# ─────────────────────────────────────────────────────────────────────────────
TOPIC_SEEDS = {
    "networking": [
        "What is a subnet mask", "How does DHCP work", "What is BGP routing",
        "TCP vs UDP explained", "What is a MAC address", "How does NAT work",
        "What is VLAN", "How does OSPF work", "What is MPLS",
        "Difference between hub switch and router", "What is ARP protocol",
        "How does traceroute work", "What is QoS in networking",
        "What is SDN software defined networking", "How does IPv6 work",
        "What is DNS and how it works", "What is a firewall",
        "How does HTTPS work", "What is a proxy server",
        "What is network bandwidth vs throughput",
    ],
    "cloud": [
        "What is cloud computing for beginners", "AWS vs Azure vs GCP",
        "What is serverless computing", "How does auto scaling work",
        "What is a CDN content delivery network", "What is IaaS PaaS SaaS",
        "How does load balancing work", "What is multi-cloud strategy",
        "What is cloud native development", "How does AWS Lambda work",
        "What is Kubernetes and why use it", "What is edge computing",
        "What is cloud storage vs local storage", "How does AWS S3 work",
        "What is a virtual machine vs container", "What is cloud migration",
        "What is disaster recovery in cloud", "How does Azure Active Directory work",
    ],
    "security": [
        "What is zero trust security", "How does SSL TLS work",
        "What is a man in the middle attack", "How does OAuth work",
        "What is SQL injection", "How does two factor authentication work",
        "What is a buffer overflow attack", "What is SIEM",
        "How does a DDoS attack work", "What is penetration testing",
        "What is social engineering in cybersecurity", "How does PKI work",
        "What is XSS cross site scripting", "What is CSRF attack",
        "What is ransomware and how does it work", "What is phishing",
        "What is a VPN and how does it work", "What is intrusion detection system",
        "What is endpoint security", "What is data encryption",
    ],
    "devops": [
        "What is CI CD pipeline", "How does Docker work",
        "What is infrastructure as code", "How does Terraform work",
        "What is GitOps", "How does Ansible work",
        "What is a microservices architecture", "How does Jenkins work",
        "What is blue green deployment", "What is chaos engineering",
        "How does Prometheus monitoring work", "What is service mesh",
        "What is DevSecOps", "What is container orchestration",
        "What is a Helm chart", "How does GitHub Actions work",
        "What is observability in DevOps", "What is SRE site reliability engineering",
    ],
    "databases": [
        "SQL vs NoSQL databases", "What is database indexing",
        "How does database replication work", "What is ACID in databases",
        "What is database sharding", "How does Redis caching work",
        "What is a graph database", "How does PostgreSQL work",
        "What is database normalization", "What is CAP theorem",
        "What is a time series database", "How does MongoDB work",
        "What is database connection pooling", "What is a data warehouse",
        "What is ETL in databases", "What is an ORM",
    ],
    "linux": [
        "Linux file permissions explained", "What is a Linux shell",
        "How does cron job work", "What is systemd in Linux",
        "Linux vs Windows server", "What is SSH and how it works",
        "What is a Linux daemon", "How does the Linux kernel work",
        "What is Docker on Linux", "Linux process management explained",
        "What is grep command in Linux", "How does iptables work",
        "What is a Linux package manager", "How to use tmux",
        "What is a Linux swap partition", "How does rsync work",
    ],
    "hardware": [
        "How does a CPU work", "What is GPU computing",
        "How does SSD vs HDD differ", "What is RAID storage",
        "How does RAM work", "What is a network switch vs router",
        "How does a firewall appliance work", "What is a NIC network card",
        "What is a server rack", "How does a data center work",
        "What is BIOS vs UEFI", "What is a TPM chip",
        "How does ECC RAM work", "What is PCIe in servers",
    ],
    "compliance": [
        "What is GDPR compliance", "What is SOC 2 certification",
        "How does ISO 27001 work", "What is HIPAA in healthcare IT",
        "What is PCI DSS compliance", "What is NIST cybersecurity framework",
        "What is data residency", "GDPR vs CCPA differences",
        "What is FedRAMP", "What is a data protection officer",
        "What is a security audit", "What is DORA regulation",
    ],
    "cve": [
        "What is a CVE vulnerability", "How does CVE scoring CVSS work",
        "What is a zero day vulnerability", "How does responsible disclosure work",
        "What is NVD national vulnerability database", "CVE vs CWE difference",
        "What is a security patch", "How to read a CVE report",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────
def log(component: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] [{component}] {msg}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
#  TIERED MEMORY SYSTEM (cortex-tms pattern)
#  Working memory: current run state
#  Episodic memory: what was published (persistent JSON)
#  Architectural memory: SOUL.md + USER.md (identity/strategy files)
# ─────────────────────────────────────────────────────────────────────────────
def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except Exception:
            pass
    return {
        "published_articles": [],
        "done_topics":        [],
        "failed_topics":      [],
        "decisions":          [],
        "knowledge_graph":    {},   # topic → [related_topics]
        "chapter_clusters":   {},   # chapter → [pillar_topics]
        "stats": {
            "total_published": 0,
            "total_failed": 0,
            "last_run": None,
            "best_chapters": [],
        },
    }

def save_memory(mem: dict) -> None:
    mem["stats"]["last_run"] = datetime.datetime.utcnow().isoformat()
    MEMORY_FILE.write_text(json.dumps(mem, indent=2, ensure_ascii=False))
    log("memory", f"Saved — {mem['stats']['total_published']} published")

def memory_has_topic(mem: dict, topic: str) -> bool:
    """Fuzzy dedup: 80%+ word overlap = duplicate (knowledge-assistant RAG pattern)."""
    topic_lower = topic.lower().strip()
    for done in mem["done_topics"]:
        if done.lower().strip() == topic_lower:
            return True
        done_words  = set(done.lower().split())
        topic_words = set(topic_lower.split())
        if len(done_words) > 2 and len(topic_words) > 2:
            overlap = len(done_words & topic_words) / max(len(done_words), len(topic_words))
            if overlap >= 0.75:
                return True
    return False

def scan_existing_articles(mem: dict) -> dict:
    """Sync memory with actual HTML files on disk (second-brain memory scan)."""
    if not ARTICLES.exists():
        return mem
    found = 0
    known_slugs = {a["slug"] for a in mem["published_articles"]}
    for html_file in ARTICLES.rglob("*.html"):
        slug = html_file.stem
        if slug == "index" or not re.match(r"\d{4}-\d{2}-\d{2}-", slug):
            continue
        if slug in known_slugs:
            continue
        try:
            content = html_file.read_text(errors="ignore")
            m = re.search(r"<title>([^<]+)</title>", content)
            title = m.group(1).split("|")[0].strip() if m else slug
            chapter = html_file.parent.name if html_file.parent.name in CHAPTERS else "networking"
            mem["published_articles"].append({
                "slug": slug, "title": title,
                "chapter": chapter, "date": slug[:10], "topic": title,
            })
            if title not in mem["done_topics"]:
                mem["done_topics"].append(title)
            found += 1
        except Exception:
            pass
    if found:
        log("memory", f"Synced {found} existing articles from disk")
    return mem

def load_knowledge_graph() -> dict:
    """Knowledge graph: tracks relationships between topics for internal linking."""
    if KNOWLEDGE_GRAPH_FILE.exists():
        try:
            return json.loads(KNOWLEDGE_GRAPH_FILE.read_text())
        except Exception:
            pass
    return {}

def save_knowledge_graph(graph: dict) -> None:
    KNOWLEDGE_GRAPH_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False))

def update_knowledge_graph(topic: str, chapter: str, slug: str,
                           related_topics: list, graph: dict) -> dict:
    """Add article to knowledge graph with its related topics (DATAGEN pattern)."""
    graph[topic] = {
        "chapter": chapter,
        "slug": slug,
        "related": related_topics,
        "date": datetime.date.today().isoformat(),
    }
    # bidirectional: if related topics exist in graph, link back
    for rel in related_topics:
        if rel in graph:
            if topic not in graph[rel].get("related", []):
                graph[rel].setdefault("related", []).append(topic)
    return graph

# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC SELECTION — intelligent, never repeats, chapter-balanced
#  (research-agent + knowledge-assistant + AutoViralAI patterns)
# ─────────────────────────────────────────────────────────────────────────────
def pick_topic(mem: dict) -> tuple[str, str]:
    chapter_counts: dict[str, int] = {ch: 0 for ch in CHAPTERS}
    for art in mem["published_articles"]:
        ch = art.get("chapter", "networking")
        if ch in chapter_counts:
            chapter_counts[ch] += 1

    candidates: list[tuple[str, str, int]] = []
    for chapter, topics in TOPIC_SEEDS.items():
        for topic in topics:
            if not memory_has_topic(mem, topic):
                candidates.append((topic, chapter, chapter_counts.get(chapter, 0)))

    if not candidates:
        log("topic", "All seeded topics exhausted — using cluster architect")
        return _claude_generate_topic(mem)

    # sort by: fewest articles in chapter first (balance coverage)
    candidates.sort(key=lambda x: x[2])

    if ANTHROPIC_KEY and len(candidates) >= 3:
        try:
            return _claude_pick_best_topic(candidates[:12], mem)
        except Exception as e:
            log("topic", f"Claude pick failed, using first candidate: {e}")

    topic, chapter, _ = candidates[0]
    log("topic", f"Selected: '{topic}' [{chapter}]")
    return topic, chapter

def _claude_pick_best_topic(candidates: list, mem: dict) -> tuple[str, str]:
    """Claude picks the highest-value topic (DATAGEN multi-agent pattern)."""
    recent = [a["title"] for a in mem["published_articles"][-5:]]
    candidate_list = "\n".join(
        f"{i+1}. [{ch}] {topic}" for i, (topic, ch, _) in enumerate(candidates)
    )

    prompt = f"""You are a content strategist for ITVedas.com — IT education for beginners.

Recent articles: {recent}
Total articles so far: {len(mem['done_topics'])}

Pick the BEST topic to write next. Prioritise:
1. Highest search demand (people actively googling this right now)
2. Most valuable for IT beginners learning fundamentals
3. NOT too similar to recent articles above
4. Fills a gap in the knowledge base

Candidates:
{candidate_list}

Reply ONLY with JSON (no fences):
{{"choice": <1-{len(candidates)}>, "reason": "<one sentence why>"}}"""

    raw = _call_claude(prompt, max_tokens=200)
    data = json.loads(_extract_json(raw))
    idx = int(data["choice"]) - 1
    topic, chapter, _ = candidates[min(idx, len(candidates)-1)]
    log("topic", f"Claude picked #{idx+1}: '{topic}' [{chapter}] — {data.get('reason','')}")
    return topic, chapter

def _claude_generate_topic(mem: dict) -> tuple[str, str]:
    """
    Topic cluster architect — 10-step strategy (x0u0an/topic-cluster-architect).
    When seeds exhausted, finds content gaps and builds cluster topics.
    """
    chapter_counts: dict[str, int] = {}
    for art in mem["published_articles"]:
        ch = art.get("chapter", "networking")
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

    done_recent = mem["done_topics"][-20:]

    prompt = f"""You are an SEO topic cluster architect for ITVedas.com.

Current coverage per chapter: {chapter_counts}
Recently covered: {done_recent}
Total articles: {len(mem['published_articles'])}

Using the 10-step topic cluster strategy:
1. Identify chapter with biggest content gap (fewest articles vs importance)
2. Find most-searched beginner question not yet covered in that chapter
3. Classify: pillar page (comprehensive overview) or supporting content (deep dive)
4. Verify: would this question rank for a specific keyword phrase?

Suggest ONE high-value topic. Return ONLY JSON:
{{
  "topic": "...",
  "chapter": "networking|cloud|security|devops|databases|linux|hardware|compliance|cve",
  "cluster_role": "pillar|supporting",
  "search_intent": "informational|navigational|transactional",
  "estimated_monthly_searches": "low|medium|high",
  "reason": "one sentence explaining gap this fills"
}}"""

    raw = _call_claude(prompt, max_tokens=300)
    data = json.loads(_extract_json(raw))
    topic   = data.get("topic", "What is network security")
    chapter = data.get("chapter", "networking")
    log("topic", f"Cluster architect: {data.get('cluster_role')} — {data.get('reason','')}")
    return topic, chapter

# ─────────────────────────────────────────────────────────────────────────────
#  TASK MANAGEMENT SYSTEM
#  Sources: compass-skills (task-clarifier, task-forest, session-handoff)
#           cortex-tms (tiered memory), jpicklyk/task-orchestrator (workflow)
#           builderz-labs/mission-control (orchestration)
# ─────────────────────────────────────────────────────────────────────────────
def task_clarifier(topic: str, chapter: str, mem: dict) -> dict:
    """
    compass-skills/task-clarifier: validates scope, anchors evidence,
    defines acceptance criteria BEFORE writing starts.
    """
    chapter_articles = [a for a in mem["published_articles"] if a.get("chapter") == chapter]

    prompt = f"""You are a task clarifier for an IT content bot at ITVedas.com.

Validate writing an article about: "{topic}"
Chapter: {chapter} ({len(chapter_articles)} articles already in this chapter)
Total site articles: {len(mem['done_topics'])}

Evaluate and clarify:
1. GOAL: Is this a specific, searchable topic? (not too broad/narrow)
2. SCOPE: Single article, or should it split into parts?
3. EVIDENCE: Identify 3 specific facts/numbers to anchor the article
4. ACCEPTANCE: What defines "done"? (min sections, FAQ, code examples?)
5. RISK: Any accuracy risks? (deprecated tech, controversial claims?)

Return ONLY JSON (no fences):
{{
  "approved": true,
  "refined_topic": "...(same or improved title, under 60 chars)",
  "scope": "single-article|needs-split",
  "split_into": null,
  "anchor_facts": [
    "specific fact with number or measurement",
    "fact with real product/company name",
    "fact with concrete example or date"
  ],
  "acceptance_criteria": {{
    "min_words": 900,
    "min_sections": 4,
    "min_faq": 3,
    "needs_code_example": true
  }},
  "risk_level": "low|medium|high",
  "risk_note": null,
  "related_topics": ["related topic 1", "related topic 2"]
}}"""

    try:
        raw = _call_claude(prompt, max_tokens=500)
        result = json.loads(_extract_json(raw))
        if result.get("refined_topic") and result["refined_topic"] != topic:
            log("clarifier", f"Topic refined: '{topic}' → '{result['refined_topic']}'")
        if result.get("risk_level") == "high":
            log("clarifier", f"HIGH RISK: {result.get('risk_note')}")
        log("clarifier", f"Approved. Anchor facts: {len(result.get('anchor_facts', []))}")
        return result
    except Exception as e:
        log("clarifier", f"Failed (non-blocking): {e}")
        return {
            "approved": True,
            "refined_topic": topic,
            "anchor_facts": [],
            "acceptance_criteria": {"min_words": 900, "min_sections": 4, "min_faq": 3, "needs_code_example": True},
            "risk_level": "low",
            "related_topics": [],
        }

def task_forest_update(mem: dict, topic: str, chapter: str, status: str,
                       slug: str = "", notes: str = "") -> None:
    """
    compass-skills/task-forest: DAG of tasks with goals, decisions, history.
    cortex-tms tiered memory: archives decision log as episodic memory.
    """
    forest_file = STATE_DIR / "task-forest.json"
    forest: dict = {}
    if forest_file.exists():
        try:
            forest = json.loads(forest_file.read_text())
        except Exception:
            pass

    forest.setdefault("tasks", {})
    forest.setdefault("chapter_goals", {
        ch: f"Build comprehensive beginner {cfg['name']} coverage (20+ articles)"
        for ch, cfg in CHAPTERS.items()
    })
    forest.setdefault("decisions", [])

    task_id = f"{chapter}/{slug or topic[:40].replace(' ', '-').lower()}"
    forest["tasks"][task_id] = {
        "topic":   topic,
        "chapter": chapter,
        "status":  status,
        "slug":    slug,
        "notes":   notes,
        "updated": datetime.datetime.utcnow().isoformat(),
    }

    if status in ("done", "failed"):
        forest["decisions"].append({
            "date":     datetime.date.today().isoformat(),
            "decision": f"'{topic}' in {chapter}",
            "outcome":  status,
            "notes":    notes,
        })

    done  = sum(1 for t in forest["tasks"].values() if t["status"] == "done")
    total = len(forest["tasks"])
    forest["summary"] = {
        "total": total, "done": done,
        "failed": sum(1 for t in forest["tasks"].values() if t["status"] == "failed"),
        "completion_pct": round(done / total * 100, 1) if total else 0,
        "last_updated": datetime.datetime.utcnow().isoformat(),
    }

    forest_file.write_text(json.dumps(forest, indent=2, ensure_ascii=False))

def session_handoff(mem: dict, topic: str, chapter: str, result: str) -> None:
    """
    compass-skills/session-handoff: compresses session state for next run.
    JamesShi96/project-butler: session log + project documentation.
    """
    handoff_file = STATE_DIR / "session-handoff.md"
    recent = [a["title"] for a in mem["published_articles"][-5:]]
    next_topics = []
    for ch, topics in TOPIC_SEEDS.items():
        for t in topics:
            if not memory_has_topic(mem, t):
                next_topics.append(f"[{ch}] {t}")
        if len(next_topics) >= 8:
            break

    chapter_counts: dict[str, int] = {}
    for art in mem["published_articles"]:
        ch = art.get("chapter", "?")
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

    handoff = f"""# ITVedas Brain — Session Handoff
Generated: {datetime.datetime.utcnow().isoformat()}
Model: {MODEL}

## This Session
- Topic: {topic}
- Chapter: {chapter}
- Result: **{result}**

## Brain State
- Articles published: {mem['stats']['total_published']}
- Topics covered: {len(mem['done_topics'])}
- Failed: {mem['stats']['total_failed']}

## Coverage by Chapter
{chr(10).join(f"- {ch}: {cnt} articles" for ch, cnt in sorted(chapter_counts.items(), key=lambda x: -x[1]))}

## Recent Articles (last 5)
{chr(10).join(f"- {t}" for t in recent)}

## Next Recommended Topics
{chr(10).join(f"- {t}" for t in next_topics[:8])}

## Files
- Memory: itvedas-brain/memory/bot_memory.json
- Task forest: itvedas-brain/state/task-forest.json
- Knowledge graph: itvedas-brain/memory/knowledge_graph.json
- Run: python itvedas-brain/itvedas-bot-v2.py
"""
    handoff_file.write_text(handoff)
    log("handoff", "Session handoff saved")

# ─────────────────────────────────────────────────────────────────────────────
#  ARTICLE WRITER — full content generation with all skill layers
#  Sources: DATAGEN multi-agent, dongbeixiaohuo evidence anchoring,
#           kristianfreeman/aiwriter SERP-driven generation
# ─────────────────────────────────────────────────────────────────────────────
def write_article(topic: str, chapter: str, anchor_facts: list | None = None,
                  acceptance: dict | None = None, related_topics: list | None = None) -> dict:
    """Generate full article with anchor facts, humanization, and SEO rules."""
    log("writer", f"Writing: '{topic}' [{chapter}]")
    anchor_facts   = anchor_facts or []
    acceptance     = acceptance or {"min_words": 900, "min_sections": 4, "min_faq": 3}
    related_topics = related_topics or []
    ch             = CHAPTERS.get(chapter, CHAPTERS["networking"])
    today          = datetime.date.today().isoformat()

    system = BOT_SOUL + f"\nYou are writing for the {ch['name']} chapter of ITVedas.com."

    anchors_block = ""
    if anchor_facts:
        anchors_block = "\nPre-validated anchor facts to use:\n" + \
            "\n".join(f"- {f}" for f in anchor_facts)

    related_block = ""
    if related_topics:
        related_block = f"\nRelated ITVedas topics to reference naturally: {related_topics}"

    min_sections = acceptance.get("min_sections", 4)
    min_faq      = acceptance.get("min_faq", 3)
    needs_code   = acceptance.get("needs_code_example", True)

    prompt = f"""Write a complete, high-quality SEO article for ITVedas.com about: "{topic}"
Chapter: {ch['name']}
Target audience: complete beginners to IT
{anchors_block}
{related_block}

WRITING REQUIREMENTS (dongbeixiaohuo evidence anchoring + rediumvex anti-detection):

PHASE 1 — Before writing, identify 3-5 specific anchor facts (if not provided above):
Examples: "DNS TTL is 300-86400s", "TLS 1.3 reduced handshake from 2-RTT to 1-RTT"

PHASE 2 — Write the article ({min_sections}+ sections, 900+ words):
- First paragraph answers the question in under 50 words
- Vary sentence lengths: 6-word and 25-word sentences in same paragraph
- Use "Here's what I mean..." or "Think of it this way..." occasionally
- Specific numbers and real names: "AWS EC2", "~50ms", "RFC 793"
- Alternate paragraph lengths: 1-sentence, 3-sentence, 4-sentence paragraphs
- Vary list lengths: 3 items or 7 items — never exactly 5
{"- Include at least one code or command example in <pre><code> tags" if needs_code else ""}

CONTENT RULES (design-skill-os + styleseed):
- Lead with the answer — NEVER "In today's world..." or "Understanding X is crucial..."
- Short paragraphs: 2-4 sentences, active voice
- Real product/company names and specific numbers
- NEVER use: elevate, seamless, powerful, revolutionary, game-changer, leverage

SEO (norahe0304-art/30x-seo):
- Title: exact keyword, under 60 chars, front-loaded
- Meta description: 150-160 chars with keyword
- H2 headings: semantic keyword variations (LSI)
- {min_faq}+ FAQ questions people actually search

Return ONLY valid JSON (no markdown fences, no ```json):
{{
  "title": "Exact keyword title under 60 chars",
  "slug": "3-5-word-url-slug",
  "meta_description": "150-160 char meta description with keyword and value promise",
  "intro": "2-3 sentences that immediately answer the question. No definitions opener. Specific fact in first sentence.",
  "anchor_facts": ["fact with specific number", "fact with real name/product", "fact with example or date"],
  "sections": [
    {{
      "heading": "Semantic H2 heading (keyword variation)",
      "content": "HTML with <p>, <ul>, <li>, <strong>, <code>, <pre><code> tags. 2-4 sentences per paragraph. Vary lengths."
    }}
  ],
  "faq": [
    {{"q": "Exact question people Google about {topic}?", "answer": "Direct 2-3 sentence answer with specific detail."}},
    {{"q": "Another real search query about {topic}?", "answer": "Specific answer with a number or example."}},
    {{"q": "Third common question?", "answer": "Specific answer."}}
  ],
  "key_takeaways": ["specific takeaway with number or fact", "takeaway 2", "takeaway 3"],
  "related_topics": ["related ITVedas topic 1", "related topic 2", "related topic 3"]
}}"""

    raw  = _call_claude(prompt, system=system, max_tokens=4500)
    data = json.loads(_extract_json(raw))

    # attach metadata
    data["chapter"]      = chapter
    data["chapter_name"] = ch["name"]
    data["chapter_color"]= ch["color"]
    data["chapter_emoji"]= ch["emoji"]
    data["chapter_num"]  = ch["num"]
    data["date"]         = today
    data["topic"]        = topic

    log("writer", f"Written: '{data['title']}' ({len(data.get('sections',[]))} sections, {len(data.get('faq',[]))} FAQ)")
    return data

# ─────────────────────────────────────────────────────────────────────────────
#  QA GATE — self-review + targeted rewrite (DATAGEN multi-agent pattern)
# ─────────────────────────────────────────────────────────────────────────────
def qa_review(data: dict) -> dict:
    """Claude reviews its own article and rewrites sections scoring below 7/10."""
    log("qa", "Self-reviewing article...")

    sections_text = "\n\n".join(
        f"## {s['heading']}\n{s['content']}" for s in data.get("sections", [])
    )

    prompt = f"""You are a quality reviewer for ITVedas.com — an IT education site for beginners.

Review this article draft:

Title: {data['title']}
Intro: {data['intro']}

{sections_text}

Score each section 1-10 on:
- Clarity: is it easy for a complete beginner to understand?
- Accuracy: are the technical details correct?
- Value: does it teach something useful and specific?
- Humanness: does it sound written by a person, not AI?

If any section scores below 7, rewrite it.

Anti-AI-slop rules when rewriting:
- Vary sentence lengths in each paragraph
- Add one specific number or real example per section
- Never use: elevate, seamless, powerful, revolutionary
- Active voice only

Return ONLY JSON (no fences):
{{
  "overall_score": <1-10>,
  "verdict": "PUBLISH|NEEDS_WORK",
  "sections": [
    {{"heading": "...", "content": "...", "score": <1-10>}}
  ],
  "intro": "...(improved or same)",
  "improvement_notes": "one sentence on what was improved"
}}"""

    try:
        raw    = _call_claude(prompt, max_tokens=3500)
        review = json.loads(_extract_json(raw))
        score  = review.get("overall_score", 8)
        verdict = review.get("verdict", "PUBLISH")
        if verdict == "NEEDS_WORK":
            log("qa", f"Rewriting weak sections (score: {score}/10) — {review.get('improvement_notes','')}")
            data["sections"] = review["sections"]
            data["intro"]    = review.get("intro", data["intro"])
        else:
            log("qa", f"Passed QA ({score}/10)")
    except Exception as e:
        log("qa", f"QA skipped (non-blocking): {e}")

    return data

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN INTELLIGENCE SYSTEM
#  Sources: bitjaru/styleseed (74 rules), Laith0003/ux-skill (152 rules),
#           frhscopex/design-skill-os (161 rules), funboy322/avoid-ai-design,
#           Sakaax/ux-pilot (376 UX rules), S0ulFood/design-cognition-skill
# ─────────────────────────────────────────────────────────────────────────────

# Forbidden words that mark AI-slop content (avoid-ai-design + ux-skill)
SLOP_WORDS = [
    "elevate", "seamless", "powerful", "revolutionary", "game-changer",
    "next-level", "cutting-edge", "leverage", "utilize", "paradigm",
    "delve", "invaluable", "meticulous", "pivotal", "transformative",
    "unlock", "harness", "robust", "scalable", "streamline",
]

def design_qa(html_content: str, data: dict) -> tuple[str, list[str]]:
    """
    Anti-AI-slop HTML linter (Laith0003/ux-skill + funboy322/avoid-ai-design).
    Checks for forbidden patterns and logs violations.
    """
    violations = []
    checks = [
        (r"Lorem ipsum",                        "Lorem ipsum detected"),
        (r"console\.log",                        "console.log in output"),
        (r"<img(?![^>]*alt=)",                   "Image missing alt text"),
        (r"(Elevate|Seamless|Revolutionary|Game-changer|Leverage|Utilize|Paradigm)",
                                                 "AI-slop filler copy"),
        (r"Get Started|Click Here|Learn More",   "Generic CTA copy"),
        (r"style=\"[^\"]{80,}\"",                "Excessive inline style"),
        (r"background:\s*linear-gradient.*purple|background:\s*linear-gradient.*violet",
                                                 "Purple gradient (AI-slop tell)"),
        (r"<h[1-9]>.*<h[1-9]>",                 "Possible heading level skip"),
        (r"emoji|🎨|🚀|⚙️|🌐|📊|✅|❌",         "Emoji as UI icon (use SVG)"),
    ]
    for pattern, msg in checks:
        if re.search(pattern, html_content, re.IGNORECASE):
            violations.append(msg)

    # check content slop words
    content_text = data.get("intro","") + " ".join(
        s.get("content","") for s in data.get("sections",[])
    )
    found_slop = [w for w in SLOP_WORDS if re.search(r'\b' + w + r'\b', content_text, re.IGNORECASE)]
    if found_slop:
        violations.append(f"Slop words in content: {found_slop}")

    if violations:
        log("design-qa", f"{len(violations)} violation(s): {'; '.join(violations)}")
    else:
        log("design-qa", "All design rules passed")

    return html_content, violations

def apply_design_intelligence(data: dict) -> dict:
    """
    Design intelligence layer: detects and rewrites AI-slop content.
    Sources: styleseed judgment layer + design-skill-os red team + avoid-ai-design.
    """
    if not ANTHROPIC_KEY:
        return data

    content_text = data.get("intro","") + " ".join(
        s.get("content","") for s in data.get("sections",[])
    )
    found_slop = [w for w in SLOP_WORDS
                  if re.search(r'\b' + w + r'\b', content_text, re.IGNORECASE)]

    # check for weak intro
    weak_intros = ["in today's", "in the world of", "understanding", "have you ever",
                   "when it comes to", "in this article", "we will explore"]
    intro_lower = data.get("intro","").lower()
    weak_intro = any(intro_lower.startswith(w) for w in weak_intros)

    if not found_slop and not weak_intro and len(data.get("sections",[])) >= 4:
        log("design", "Content passes design check")
        return data

    issues = []
    if found_slop:
        issues.append(f"Remove these slop words and replace with specific concrete language: {found_slop}")
    if weak_intro:
        issues.append("Rewrite intro — must lead with the answer, not a definition or setup phrase")
    if len(data.get("sections",[])) < 4:
        issues.append("Add more sections — minimum 4 for complete coverage")

    log("design", f"Applying design intelligence: {issues}")

    sections_json = json.dumps([
        {"heading": s["heading"], "content": s["content"]}
        for s in data.get("sections",[])
    ])

    prompt = f"""You are a design-aware content editor for ITVedas.com.

Fix these issues in the article content:
{chr(10).join(f'- {i}' for i in issues)}

Design rules (styleseed + design-skill-os):
- Intro MUST start with the answer or a specific fact — not a definition
- Short paragraphs: 2-4 sentences, active voice
- Real examples with specific names/numbers/measurements
- NO slop words: {SLOP_WORDS[:8]}
- Vary section lengths — not all sections equal height

Current intro:
{data.get('intro','')}

Current sections (JSON):
{sections_json}

Return ONLY JSON (no fences):
{{"intro": "...", "sections": [{{"heading": "...", "content": "..."}}]}}"""

    try:
        raw   = _call_claude(prompt, max_tokens=3500)
        fixed = json.loads(_extract_json(raw))
        data["intro"]    = fixed.get("intro", data["intro"])
        data["sections"] = fixed.get("sections", data["sections"])
        log("design", "Content improved by design intelligence")
    except Exception as e:
        log("design", f"Design rewrite skipped: {e}")

    return data

# ─────────────────────────────────────────────────────────────────────────────
#  INTERNAL LINKER — knowledge-assistant RAG + knowledge graph
#  Finds opportunities to link new article to existing articles
# ─────────────────────────────────────────────────────────────────────────────
def build_internal_links(data: dict, mem: dict, graph: dict) -> dict:
    """
    Adds internal links to the article content using knowledge graph.
    knowledge-assistant RAG pattern: retrieves related articles from memory.
    """
    topic   = data.get("topic","")
    chapter = data.get("chapter","")

    # find articles this topic is related to
    related = graph.get(topic, {}).get("related", []) or data.get("related_topics", [])

    # find published articles that match related topics
    link_opportunities: list[dict] = []
    for art in mem["published_articles"]:
        art_title = art.get("title","")
        art_slug  = art.get("slug","")
        art_ch    = art.get("chapter","")
        if not art_slug:
            continue
        # check if this article's topic appears in related topics or title overlap
        for rel in related:
            if rel.lower() in art_title.lower() or art_title.lower() in rel.lower():
                link_opportunities.append({
                    "title": art_title,
                    "url":   f"/articles/{art_ch}/{art_slug}.html",
                    "chapter": art_ch,
                })
                break

    if link_opportunities:
        log("linker", f"Found {len(link_opportunities)} internal link opportunities")
        data["internal_links"] = link_opportunities[:5]  # max 5 internal links
    else:
        data["internal_links"] = []

    return data

# ─────────────────────────────────────────────────────────────────────────────
#  HTML BUILDER — full page with ToC, reading time, FAQ schema, internal links
# ─────────────────────────────────────────────────────────────────────────────
def estimate_reading_time(data: dict) -> int:
    """Estimate reading time in minutes (200 words/min average)."""
    all_text = data.get("intro","") + " ".join(
        s.get("content","") for s in data.get("sections",[])
    )
    words = len(re.sub(r'<[^>]+>', '', all_text).split())
    return max(3, round(words / 200))

def build_html(data: dict) -> str:
    """Build complete HTML article with all features."""
    esc_title = html_module.escape(data["title"])
    esc_desc  = html_module.escape(data["meta_description"])
    slug      = data["slug"]
    chapter   = data["chapter"]
    ch_name   = data["chapter_name"]
    ch_color  = data["chapter_color"]
    ch_emoji  = data["chapter_emoji"]
    date_str  = data["date"]
    canonical = f"{SITE_URL}/articles/{chapter}/{slug}.html"
    read_time = estimate_reading_time(data)

    # format date nicely
    try:
        date_obj = datetime.date.fromisoformat(date_str)
        date_fmt = date_obj.strftime("%B %d, %Y")
    except Exception:
        date_fmt = date_str

    # ── schemas ──────────────────────────────────────────────────────────────
    faq_items = data.get("faq", [])
    faq_schema = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": html_module.escape(f["q"]),
             "acceptedAnswer": {"@type": "Answer", "text": html_module.escape(f["answer"])}}
            for f in faq_items
        ]
    })
    article_schema = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": data["title"],
        "description": data["meta_description"],
        "datePublished": date_str,
        "dateModified": date_str,
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "url": canonical,
        "wordCount": len(re.sub(r'<[^>]+>', '', data.get("intro","")).split()) * 8,
    })
    breadcrumb_schema = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",   "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": ch_name,  "item": f"{SITE_URL}/articles/{chapter}/"},
            {"@type": "ListItem", "position": 3, "name": data["title"], "item": canonical},
        ]
    })

    # ── table of contents ────────────────────────────────────────────────────
    sections = data.get("sections", [])
    toc_items = ""
    for i, sec in enumerate(sections):
        heading = sec.get("heading","")
        anchor  = re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
        toc_items += f'<li><a href="#{anchor}">{html_module.escape(heading)}</a></li>\n'

    # ── sections HTML ────────────────────────────────────────────────────────
    sections_html = ""
    for sec in sections:
        heading = sec.get("heading","")
        content = sec.get("content","")
        anchor  = re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
        sections_html += f'<h2 id="{anchor}">{html_module.escape(heading)}</h2>\n{content}\n'

    # ── FAQ HTML ─────────────────────────────────────────────────────────────
    faq_html = ""
    if faq_items:
        faq_html = '<h2 id="faq">Frequently Asked Questions</h2>\n<div class="faq">\n'
        for f in faq_items:
            faq_html += (
                f'<div class="faq-item">'
                f'<h3>{html_module.escape(f["q"])}</h3>'
                f'<p>{html_module.escape(f["answer"])}</p>'
                f'</div>\n'
            )
        faq_html += "</div>\n"

    # ── key takeaways ────────────────────────────────────────────────────────
    takeaways = data.get("key_takeaways", [])
    takeaways_html = ""
    if takeaways:
        items = "".join(f"<li>{html_module.escape(t)}</li>" for t in takeaways)
        takeaways_html = f'<div class="takeaways"><h2>Key Takeaways</h2><ul>{items}</ul></div>\n'

    # ── anchor facts ─────────────────────────────────────────────────────────
    anchor_facts = data.get("anchor_facts", [])
    facts_html = ""
    if anchor_facts:
        items = "".join(f"<li>{html_module.escape(f)}</li>" for f in anchor_facts)
        facts_html = f'<div class="fact-box"><strong>Key Facts</strong><ul>{items}</ul></div>\n'

    # ── internal links ───────────────────────────────────────────────────────
    internal_links = data.get("internal_links", [])
    related_html = ""
    if internal_links:
        links_html = "".join(
            f'<a href="{lnk["url"]}" class="rel-link">{html_module.escape(lnk["title"])}</a>'
            for lnk in internal_links
        )
        related_html = f'<div class="related-articles"><h2>Related Articles</h2><div class="rel-grid">{links_html}</div></div>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/assets/logo-mark.svg">
<meta name="description" content="{esc_desc}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{esc_title} | {SITE_NAME}">
<meta property="og:description" content="{esc_desc}">
<meta property="og:image" content="{SITE_URL}/assets/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta property="article:published_time" content="{date_str}">
<link rel="canonical" href="{canonical}">
<title>{esc_title} | {SITE_NAME}</title>
<script type="application/ld+json">{article_schema}</script>
<script type="application/ld+json">{faq_schema}</script>
<script type="application/ld+json">{breadcrumb_schema}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0A0A0F;--bg2:#13131C;--bg3:#1A1A28;
  --text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;
  --accent:{ch_color};--border:rgba(255,255,255,0.08);
  --radius:12px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}

/* reading progress bar */
#progress{{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:200;width:0%;transition:width .1s linear;}}

/* nav */
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color .2s;}}
.nav-links a:hover{{color:var(--text);}}

/* hero */
.hero{{padding:8rem 2rem 2.5rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;transition:color .2s;}}
.breadcrumb a:hover{{color:var(--accent);}}
.ch-badge{{display:inline-flex;align-items:center;gap:0.4rem;font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--accent);margin-bottom:0.85rem;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.85rem,4vw,2.75rem);font-weight:700;letter-spacing:-0.025em;line-height:1.15;margin-bottom:1.25rem;}}
.hero-meta{{display:flex;gap:1.25rem;font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;flex-wrap:wrap;}}
.hero-meta span{{display:flex;align-items:center;gap:0.3rem;}}
.hero p.intro{{font-size:1.05rem;color:var(--sub);line-height:1.8;border-left:3px solid var(--accent);padding-left:1rem;}}

/* layout */
.page-wrap{{max-width:860px;margin:0 auto;padding:1.5rem 2rem 6rem;display:grid;grid-template-columns:1fr 220px;gap:2.5rem;align-items:start;}}
.article-body{{min-width:0;}}

/* TOC sidebar */
.toc-sidebar{{position:sticky;top:80px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem;font-size:0.85rem;}}
.toc-sidebar h3{{font-family:'Space Grotesk',sans-serif;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--muted);margin-bottom:0.85rem;}}
.toc-sidebar ol{{padding-left:1.1rem;}}
.toc-sidebar li{{margin-bottom:0.4rem;}}
.toc-sidebar a{{color:var(--sub);text-decoration:none;transition:color .15s;}}
.toc-sidebar a:hover{{color:var(--accent);}}

/* content */
.content h2{{font-family:'Space Grotesk',sans-serif;font-size:1.45rem;font-weight:700;margin:2.5rem 0 1rem;color:var(--text);letter-spacing:-0.015em;scroll-margin-top:80px;}}
.content h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;margin:1.75rem 0 0.6rem;color:var(--text);}}
.content p{{color:var(--sub);margin-bottom:1.25rem;}}
.content ul,.content ol{{color:var(--sub);padding-left:1.5rem;margin-bottom:1.25rem;}}
.content li{{margin-bottom:0.4rem;}}
.content strong{{color:var(--text);}}
.content a{{color:var(--accent);text-decoration:none;}}
.content a:hover{{text-decoration:underline;}}
.content code{{background:var(--bg2);border:1px solid var(--border);border-radius:4px;padding:0.15em 0.45em;font-size:0.875em;color:#FF6B35;font-family:'Courier New',monospace;}}
.content pre{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:1.25rem 1.5rem;overflow-x:auto;margin:1.5rem 0;}}
.content pre code{{background:none;border:none;padding:0;font-size:0.875rem;color:#A8E6CF;}}

/* special blocks */
.fact-box{{background:var(--bg2);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius);padding:1.25rem 1.5rem;margin:1.5rem 0;}}
.fact-box strong{{display:block;font-family:'Space Grotesk',sans-serif;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--muted);margin-bottom:0.6rem;}}
.fact-box ul{{margin:0;padding-left:1.25rem;}}
.fact-box li{{color:var(--sub);font-size:0.9rem;margin-bottom:0.3rem;}}

.takeaways{{background:var(--bg3);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius);padding:1.5rem;margin:2rem 0;}}
.takeaways h2{{font-size:1rem;font-family:'Space Grotesk',sans-serif;margin:0 0 0.75rem;color:var(--text);}}
.takeaways ul{{margin:0;padding-left:1.25rem;}}
.takeaways li{{color:var(--sub);font-size:0.9rem;}}

/* FAQ */
.faq{{margin-top:0.75rem;}}
.faq-item{{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem 1.5rem;margin-bottom:0.85rem;transition:border-color .2s;}}
.faq-item:hover{{border-color:var(--accent);}}
.faq-item h3{{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;margin-bottom:0.5rem;color:var(--text);}}
.faq-item p{{margin:0;font-size:0.9rem;color:var(--sub);}}

/* related articles */
.related-articles{{margin-top:2.5rem;}}
.related-articles h2{{font-family:'Space Grotesk',sans-serif;font-size:1.2rem;margin-bottom:1rem;color:var(--text);}}
.rel-grid{{display:flex;flex-direction:column;gap:0.6rem;}}
.rel-link{{display:block;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:0.85rem 1rem;text-decoration:none;color:var(--sub);font-size:0.875rem;transition:border-color .2s,color .2s;}}
.rel-link:hover{{border-color:var(--accent);color:var(--text);}}

/* nav article */
.nav-art{{display:flex;justify-content:space-between;gap:1rem;margin-top:3rem;padding-top:2rem;border-top:1px solid var(--border);}}
.nav-art a{{flex:1;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:1rem 1.25rem;text-decoration:none;color:var(--sub);font-size:0.875rem;transition:border-color .2s;cursor:pointer;}}
.nav-art a:hover{{border-color:var(--accent);}}
.nav-art .label{{font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;}}

/* footer */
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;transition:color .2s;}}
.flinks a:hover{{color:#FF6B35;}}

@media(max-width:768px){{
  nav{{padding:0 1.25rem;}}
  .nav-links{{display:none;}}
  .page-wrap{{grid-template-columns:1fr;padding-left:1.25rem;padding-right:1.25rem;}}
  .toc-sidebar{{display:none;}}
  .hero{{padding-left:1.25rem;padding-right:1.25rem;}}
}}
</style>
</head>
<body>
<div id="progress"></div>

<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/news.html">News</a>
    <a href="/articles/{chapter}/">{ch_emoji} {ch_name}</a>
    <a href="/#chapters">All Chapters</a>
    <a href="mailto:info@itvedas.com">Contact</a>
  </div>
</nav>

<div class="hero">
  <div class="breadcrumb">
    <a href="/">Home</a> ›
    <a href="/articles/{chapter}/">{ch_name}</a> ›
    {esc_title}
  </div>
  <div class="ch-badge">{ch_emoji} {ch_name}</div>
  <h1>{esc_title}</h1>
  <div class="hero-meta">
    <span>{date_fmt}</span>
    <span>{read_time} min read</span>
    <span>ITVedas</span>
  </div>
  <p class="intro">{html_module.escape(data['intro'])}</p>
</div>

<div class="page-wrap">
  <article class="article-body content">
    {facts_html}
    {sections_html}
    {takeaways_html}
    {faq_html}
    {related_html}
    <div class="nav-art">
      <a href="/articles/{chapter}/">
        <div class="label">← Chapter</div>
        {ch_emoji} Back to {ch_name}
      </a>
      <a href="/#chapters">
        <div class="label">Explore →</div>
        All Chapters
      </a>
    </div>
  </article>

  <aside class="toc-sidebar">
    <h3>Contents</h3>
    <ol>
      {toc_items}
      {"<li><a href='#faq'>FAQ</a></li>" if faq_items else ""}
    </ol>
  </aside>
</div>

<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks">
    <a href="/">Home</a>
    <a href="/news.html">News</a>
    <a href="/articles/{chapter}/">{ch_name}</a>
    <a href="/#chapters">Chapters</a>
    <a href="/privacy-policy.html">Privacy Policy</a>
    <a href="/terms-of-service.html">Terms of Service</a>
    <a href="mailto:info@itvedas.com">Contact</a>
  </div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} {SITE_NAME} · Knowledge for everyone</p>
</footer>

<script>
(function(){{
  var bar = document.getElementById('progress');
  if(!bar) return;
  function upd(){{
    var s = document.documentElement;
    var pct = (s.scrollTop/(s.scrollHeight-s.clientHeight))*100;
    bar.style.width = Math.min(100,pct) + '%';
  }}
  window.addEventListener('scroll', upd, {{passive:true}});
}})();
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTER INDEX BUILDER — rebuilds chapter index page with new article
# ─────────────────────────────────────────────────────────────────────────────
def build_chapter_index_html(chapter: str, articles: list[dict]) -> str:
    """Build the chapter index page listing all articles in that chapter."""
    ch   = CHAPTERS.get(chapter, CHAPTERS["networking"])
    name = ch["name"]
    clr  = ch["color"]
    em   = ch["emoji"]

    # sort by date desc
    articles_sorted = sorted(articles, key=lambda a: a.get("date",""), reverse=True)

    cards_html = ""
    for art in articles_sorted[:50]:  # max 50 per index
        title    = html_module.escape(art.get("title","Untitled"))
        slug     = art.get("slug","")
        art_date = art.get("date","")
        url      = f"/articles/{chapter}/{slug}.html"
        try:
            d = datetime.date.fromisoformat(art_date[:10])
            dfmt = d.strftime("%b %d, %Y")
        except Exception:
            dfmt = art_date
        cards_html += f"""<a href="{url}" class="art-card">
  <div class="art-date">{dfmt}</div>
  <h2>{title}</h2>
  <div class="art-arrow">Read →</div>
</a>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/assets/logo-mark.svg">
<meta name="description" content="ITVedas {name} chapter — beginner-friendly guides on {name.lower()} concepts, explained simply.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_URL}/articles/{chapter}/">
<title>{name} Guides | {SITE_NAME}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{clr};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color .2s;}}
.nav-links a:hover{{color:var(--text);}}
.hero{{padding:8rem 2rem 3rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.ch-label{{font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--accent);margin-bottom:0.75rem;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.8rem,4vw,2.75rem);font-weight:700;letter-spacing:-0.025em;line-height:1.15;margin-bottom:1rem;}}
.hero p{{color:var(--sub);font-size:1.05rem;max-width:580px;}}
.content{{max-width:860px;margin:0 auto;padding:2rem 2rem 6rem;}}
.count{{font-size:0.85rem;color:var(--muted);margin-bottom:1.5rem;}}
.art-card{{display:block;background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:0.85rem;text-decoration:none;transition:border-color .2s,transform .2s;cursor:pointer;}}
.art-card:hover{{border-color:var(--accent);transform:translateX(4px);}}
.art-date{{font-size:0.78rem;color:var(--muted);margin-bottom:0.4rem;}}
.art-card h2{{font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:600;color:var(--text);margin-bottom:0.4rem;}}
.art-arrow{{font-size:0.8rem;color:var(--accent);}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:0.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:0.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:0.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;}}
.flinks a:hover{{color:#FF6B35;}}
@media(max-width:640px){{nav{{padding:0 1.25rem;}}.nav-links{{display:none;}}.hero,.content{{padding-left:1.25rem;padding-right:1.25rem;}}}}
</style>
</head>
<body>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links"><a href="/">Home</a><a href="/news.html">News</a><a href="/#chapters">All Chapters</a><a href="mailto:info@itvedas.com">Contact</a></div>
</nav>
<div class="hero">
  <div class="breadcrumb"><a href="/">Home</a> › {name}</div>
  <div class="ch-label">{em} Chapter {ch['num']}</div>
  <h1>{name}</h1>
  <p>Beginner-friendly guides on {name.lower()} — explained simply, with real examples.</p>
</div>
<div class="content">
  <div class="count">{len(articles_sorted)} articles in this chapter</div>
  {cards_html}
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks">
    <a href="/">Home</a><a href="/#chapters">All Chapters</a>
    <a href="/privacy-policy.html">Privacy</a>
    <a href="/terms-of-service.html">Terms</a>
    <a href="mailto:info@itvedas.com">Contact</a>
  </div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} {SITE_NAME} · Knowledge for everyone</p>
</footer>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  SITEMAP UPDATER — adds new article to sitemap.xml
# ─────────────────────────────────────────────────────────────────────────────
def build_sitemap(mem: dict) -> str:
    """Build complete sitemap.xml from memory."""
    today = datetime.date.today().isoformat()
    urls  = [
        f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/news.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{SITE_URL}/privacy-policy.html</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>",
        f"  <url><loc>{SITE_URL}/terms-of-service.html</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>",
    ]
    # chapter index pages
    for ch in CHAPTERS:
        urls.append(f"  <url><loc>{SITE_URL}/articles/{ch}/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    # articles
    for art in mem["published_articles"]:
        slug  = art.get("slug","")
        ch    = art.get("chapter","networking")
        adate = art.get("date", today)
        if slug and re.match(r"\d{4}-\d{2}-\d{2}-", slug):
            urls.append(
                f"  <url><loc>{SITE_URL}/articles/{ch}/{slug}.html</loc>"
                f"<lastmod>{adate}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>"
            )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )

# ─────────────────────────────────────────────────────────────────────────────
#  GITHUB PUBLISHER — direct API push (github-agent.py pattern)
# ─────────────────────────────────────────────────────────────────────────────
def github_put(path: str, content: str, message: str) -> bool:
    """Create or update a file via GitHub Contents API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        res = json.load(urllib.request.urlopen(req, timeout=30))
        sha = res.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            log("github", f"GET {path}: HTTP {e.code}")
    except Exception:
        pass

    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch":  GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(),
                headers=headers, method="PUT"
            )
            urllib.request.urlopen(req, timeout=30)
            log("github", f"OK: {path}")
            return True
        except Exception as e:
            if attempt == 2:
                log("github", f"FAILED {path}: {e}")
                return False
            time.sleep(4 ** attempt)
    return False

def publish_all(data: dict, html_content: str, mem: dict) -> bool:
    """Publish article + chapter index + sitemap to GitHub."""
    if not GITHUB_TOKEN:
        log("github", "No GITHUB_TOKEN — saving locally")
        return _save_locally(data, html_content)

    chapter = data["chapter"]
    slug    = data["slug"]
    date    = data["date"]
    fname   = f"{date}-{slug}.html"
    ok      = True

    # 1. article
    ok &= github_put(
        f"articles/{chapter}/{fname}",
        html_content,
        f"bot: add '{data['title']}' [{chapter}]"
    )

    # 2. chapter index
    chapter_articles = [a for a in mem["published_articles"] if a.get("chapter") == chapter]
    # include the new article (not yet in mem at this point, so add it)
    chapter_articles.append({"title": data["title"], "slug": fname[:-5], "date": date, "chapter": chapter})
    index_html = build_chapter_index_html(chapter, chapter_articles)
    ok &= github_put(
        f"articles/{chapter}/index.html",
        index_html,
        f"bot: update {chapter} chapter index"
    )

    # 3. sitemap (build from mem + new article)
    mem_snapshot = dict(mem)
    mem_snapshot["published_articles"] = list(mem["published_articles"]) + [{
        "slug": f"{date}-{slug}", "chapter": chapter, "date": date, "title": data["title"]
    }]
    sitemap = build_sitemap(mem_snapshot)
    ok &= github_put("sitemap.xml", sitemap, "bot: update sitemap")

    return ok

def _save_locally(data: dict, html_content: str) -> bool:
    """Fallback: save to local filesystem."""
    out_dir = ARTICLES / data["chapter"]
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{data['date']}-{data['slug']}.html"
    (out_dir / fname).write_text(html_content, encoding="utf-8")
    log("local", f"Saved: {out_dir/fname}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
#  HEARTBEAT — health log after every run (second-brain-starter)
# ─────────────────────────────────────────────────────────────────────────────
def write_heartbeat(mem: dict, result: str, topic: str, chapter: str) -> None:
    chapter_counts: dict[str, int] = {}
    for art in mem["published_articles"]:
        ch = art.get("chapter","?")
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

    next_topics: list[dict] = []
    for ch, topics in TOPIC_SEEDS.items():
        for t in topics:
            if not memory_has_topic(mem, t):
                next_topics.append({"topic": t, "chapter": ch})
            if len(next_topics) >= 8:
                break
        if len(next_topics) >= 8:
            break

    heartbeat = {
        "timestamp":         datetime.datetime.utcnow().isoformat(),
        "result":            result,
        "last_topic":        topic,
        "last_chapter":      chapter,
        "model":             MODEL,
        "total_published":   mem["stats"]["total_published"],
        "total_failed":      mem["stats"]["total_failed"],
        "articles_per_chapter": chapter_counts,
        "next_topics":       next_topics,
        "seeds_remaining":   sum(
            1 for ch, ts in TOPIC_SEEDS.items()
            for t in ts if not memory_has_topic(mem, t)
        ),
    }
    HEARTBEAT.write_text(json.dumps(heartbeat, indent=2))
    log("heartbeat", f"Logged. Total: {mem['stats']['total_published']} published")

# ─────────────────────────────────────────────────────────────────────────────
#  SOUL / USER files (second-brain-starter architectural memory)
# ─────────────────────────────────────────────────────────────────────────────
def ensure_soul_files() -> None:
    if not SOUL_FILE.exists():
        SOUL_FILE.write_text(BOT_SOUL)
        log("soul", "Created SOUL.md")
    if not USER_FILE.exists():
        USER_FILE.write_text(f"""# ITVedas Brain — Site Profile

## Identity
- Site: {SITE_URL}
- Name: {SITE_NAME}
- Type: IT education for complete beginners
- Repo: {GITHUB_REPO}

## Content Strategy
- 1 article per run (daily via GitHub Actions)
- Target: 200+ articles across all 9 chapters
- Balance coverage across all chapters evenly
- Build topic clusters: pillar pages + supporting content
- Never repeat a topic

## Chapters
{chr(10).join(f"- {ch}: {cfg['name']}" for ch, cfg in CHAPTERS.items())}

## Tech Stack
- Claude (Haiku) for content generation
- GitHub API for publishing
- No OpenAI required
- Memory: memory/bot_memory.json (persistent across runs)
""")
        log("soul", "Created USER.md")

# ─────────────────────────────────────────────────────────────────────────────
#  CLAUDE API HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _call_claude(prompt: str, system: str | None = None, max_tokens: int = 4000) -> str:
    if not ANTHROPIC_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    payload: dict[str, Any] = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

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
                res = json.load(resp)
            return res["content"][0]["text"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            wait = 8 * (attempt + 1)
            log("claude", f"Retry {attempt+1} in {wait}s: {e}")
            time.sleep(wait)
    return ""

def _extract_json(text: str) -> str:
    """
    Robustly extract JSON from Claude output.
    Handles: raw JSON, ```json fences, ```fences, and mixed text.
    """
    text = text.strip()
    # strip code fences
    if "```" in text:
        lines = text.split("\n")
        cleaned = []
        in_fence = False
        for line in lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence or True:  # always collect content lines
                cleaned.append(line)
        text = "\n".join(cleaned).strip()
    # find outermost { }
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN — full pipeline
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    log("brain", "=" * 60)
    log("brain", "ITVedas Brain Bot v2 starting")
    log("brain", f"Model: {MODEL} | Repo: {GITHUB_REPO}")

    if not ANTHROPIC_KEY:
        log("brain", "ERROR: ANTHROPIC_API_KEY not set")
        return 1

    # ── 1. ARCHITECTURAL MEMORY — soul files ─────────────────────────────────
    ensure_soul_files()

    # ── 2. EPISODIC MEMORY — load + sync with disk ───────────────────────────
    log("memory", "Loading brain memory...")
    mem   = load_memory()
    mem   = scan_existing_articles(mem)
    graph = load_knowledge_graph()
    log("memory", f"State: {mem['stats']['total_published']} published | {len(mem['done_topics'])} topics done")

    # ── 3. TOPIC SELECTION — intelligent, balanced ───────────────────────────
    topic, chapter = pick_topic(mem)

    # ── 4. TASK CLARIFIER — validate + anchor evidence ───────────────────────
    task_forest_update(mem, topic, chapter, "in_progress")
    clarification  = task_clarifier(topic, chapter, mem)
    topic          = clarification.get("refined_topic", topic)
    anchor_facts   = clarification.get("anchor_facts", [])
    acceptance     = clarification.get("acceptance_criteria", {})
    related_topics = clarification.get("related_topics", [])
    log("brain", f"Task: '{topic}' [{chapter}] | risk={clarification.get('risk_level','low')}")

    # ── 5. WRITE ARTICLE ─────────────────────────────────────────────────────
    try:
        data = write_article(topic, chapter,
                             anchor_facts=anchor_facts,
                             acceptance=acceptance,
                             related_topics=related_topics)
    except Exception as e:
        log("writer", f"FAILED: {e}")
        mem["failed_topics"].append(topic)
        mem["stats"]["total_failed"] += 1
        task_forest_update(mem, topic, chapter, "failed", notes=str(e))
        save_memory(mem)
        write_heartbeat(mem, "WRITE_FAILED", topic, chapter)
        session_handoff(mem, topic, chapter, "WRITE_FAILED")
        return 1

    # ── 6. QA GATE ───────────────────────────────────────────────────────────
    data = qa_review(data)

    # ── 7. DESIGN INTELLIGENCE ───────────────────────────────────────────────
    data = apply_design_intelligence(data)

    # ── 7b. INTERNAL LINKING ─────────────────────────────────────────────────
    data = build_internal_links(data, mem, graph)

    # ── 8. BUILD HTML ────────────────────────────────────────────────────────
    html_content = build_html(data)

    # ── 8b. DESIGN QA LINT ───────────────────────────────────────────────────
    html_content, violations = design_qa(html_content, data)
    if violations:
        mem["decisions"].append({
            "date": datetime.date.today().isoformat(),
            "topic": topic, "design_violations": violations,
        })

    # ── 9. PUBLISH — article + chapter index + sitemap ───────────────────────
    ok = publish_all(data, html_content, mem)
    if not ok:
        log("brain", "Publish failed")
        mem["failed_topics"].append(topic)
        mem["stats"]["total_failed"] += 1
        task_forest_update(mem, topic, chapter, "failed", notes="publish failed")
        save_memory(mem)
        write_heartbeat(mem, "PUBLISH_FAILED", topic, chapter)
        return 1

    # ── 10. MEMORY UPDATE ────────────────────────────────────────────────────
    slug_full = f"{data['date']}-{data['slug']}"
    mem["published_articles"].append({
        "slug": slug_full, "title": data["title"],
        "topic": topic, "chapter": chapter, "date": data["date"],
    })
    mem["done_topics"].append(topic)
    mem["stats"]["total_published"] += 1
    save_memory(mem)

    # ── 11. KNOWLEDGE GRAPH ──────────────────────────────────────────────────
    graph = update_knowledge_graph(
        topic, chapter, slug_full,
        related_topics=data.get("related_topics", []),
        graph=graph
    )
    save_knowledge_graph(graph)

    # ── 12. TASK FOREST + HEARTBEAT + HANDOFF ────────────────────────────────
    task_forest_update(mem, topic, chapter, "done", slug=slug_full)
    write_heartbeat(mem, "SUCCESS", topic, chapter)
    session_handoff(mem, topic, chapter, "SUCCESS")

    log("brain", "=" * 60)
    log("brain", f"DONE: '{data['title']}'")
    log("brain", f"Published to: articles/{chapter}/{slug_full}.html")
    log("brain", f"Total published: {mem['stats']['total_published']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
