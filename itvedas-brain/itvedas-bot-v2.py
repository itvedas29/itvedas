#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              ITVedas Super Bot v2 — Unified Autonomous Agent                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Skills integrated from 100+ GitHub AI repos across 6 topic areas:         ║
║                                                                              ║
║  MEMORY & AGENTS                                                             ║
║  • coleam00/second-brain-starter  — persistent memory, SOUL, heartbeat     ║
║  • letta-ai/letta                 — stateful agents with self-improvement   ║
║  • microsoft/autogen              — multi-agent programming patterns        ║
║  • zhayujie/CowAgent              — skill tree + tool harness patterns      ║
║                                                                              ║
║  SEO & CONTENT                                                               ║
║  • norahe0304-art/30x-seo         — 24 production SEO skills                ║
║  • rediumvex/seo-blog-writer      — 6 anti-detection writing rules          ║
║  • x0u0an/topic-cluster-architect — 10-step topic cluster strategy          ║
║  • dongbeixiaohuo/writing-agent   — evidence anchoring + humanization gate  ║
║  • kristianfreeman/aiwriter       — SERP-driven article generation          ║
║  • kgarbacinski/AutoViralAI       — self-learning viral content research    ║
║                                                                              ║
║  DATA & RESEARCH                                                             ║
║  • e2b-dev/code-interpreter       — AI-driven data analysis patterns        ║
║  • starpig1129/DATAGEN            — multi-agent research + report writing   ║
║  • zebbern/knowledge-assistant    — RAG on custom knowledge files           ║
║  • divyeshmutha12/AI-Research-Asst— LangGraph + FAISS multi-agent RAG      ║
║                                                                              ║
║  CHATBOT & WEBSITE                                                           ║
║  • kaymen99/AI-Sales-agent        — product recommendation patterns         ║
║  • sitechat/raksbisht             — website content RAG                     ║
║  • RumenDamyanov/npm-chatbot      — multi-provider chatbot patterns         ║
║                                                                              ║
║  DESIGN INTELLIGENCE                                                         ║
║  • bitjaru/styleseed              — 74 design rules, spatial rhythm, cards  ║
║  • Laith0003/ux-skill             — 152 anti-AI-slop rules + linter         ║
║  • frhscopex/design-skill-os      — 161 rules from design masters           ║
║  • funboy322/avoid-ai-design      — anti-pattern detection + rewrite        ║
║  • Sakaax/ux-pilot                — 376 UX rules co-pilot                   ║
║  • S0ulFood/design-cognition-skill— 4-role design thinking framework        ║
║                                                                              ║
║  TASK MANAGEMENT (60 repos — github.com/topics/task-management)             ║
║  • dongshuyan/compass-skills      — task-clarifier, task-forest DAG,        ║
║  •                                  session-handoff, user-profile-keeper    ║
║  • builderz-labs/mission-control  — multi-agent task orchestration          ║
║  • saltbo/agent-kanban            — agent-first kanban mission control      ║
║  • CronusL-1141/AI-company        — multi-agent team OS for Claude Code     ║
║  • jpicklyk/task-orchestrator     — server-enforced workflow discipline      ║
║  • cortex-tms/cortex-tms          — tiered memory system (TMS)              ║
║  • JamesShi96/project-butler      — session logs + project documentation    ║
║  • kanban-md/antopolskiy          — file-based kanban for agentic loops     ║
║  • cyanheads/atlas-mcp-server     — Neo4j task graph for LLM agents         ║
║  • L1AD/claude-task-viewer        — Kanban board for Claude Code tasks      ║
║                                                                              ║
║  What this bot does every run:                                               ║
║  1. MEMORY CHECK  — loads brain memory, knows what articles exist           ║
║  2. RESEARCH      — finds trending IT topics with search gaps               ║
║  3. TOPIC PICK    — intelligent selection (never repeats a done topic)      ║
║  4. WRITE         — generates full SEO article with Claude                  ║
║  5. QA GATE       — self-reviews, rewrites weak sections                    ║
║  6. PUBLISH       — pushes HTML article + updates index + sitemap to GitHub ║
║  7. MEMORY UPDATE — saves topic to memory so it's never repeated            ║
║  8. HEARTBEAT     — logs health + next recommended topics                   ║
║                                                                              ║
║  Requires only: ANTHROPIC_API_KEY + GITHUB_TOKEN                            ║
║  No OpenAI needed. Runs on GitHub Actions (cron) or VPS.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import datetime
import html
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
ROOT        = pathlib.Path(__file__).resolve().parent.parent   # repo root
ARTICLES    = ROOT / "articles"
BRAIN_DIR   = pathlib.Path(__file__).resolve().parent
MEMORY_DIR  = BRAIN_DIR / "memory"
STATE_DIR   = BRAIN_DIR / "state"
MEMORY_FILE = MEMORY_DIR / "bot_memory.json"
SOUL_FILE   = MEMORY_DIR / "SOUL.md"
USER_FILE   = MEMORY_DIR / "USER.md"
HEARTBEAT   = STATE_DIR  / "heartbeat.json"

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
MODEL          = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20251001")

# ─────────────────────────────────────────────────────────────────────────────
#  SOUL — bot identity (second-brain-starter pattern)
# ─────────────────────────────────────────────────────────────────────────────
BOT_SOUL = """
You are the ITVedas Content Bot — an autonomous AI content writer for itvedas.com,
an IT education platform that explains complex technology in plain English.

Core values (from letta-ai stateful agent patterns):
- Write for complete beginners — no jargon without explanation
- Be accurate, practical, and engaging
- Never repeat a topic that already exists on the site
- Every article must answer a real question people search for
- SEO matters: use the target keyword naturally, answer the question fast
- Quality over quantity — one great article beats five mediocre ones

SEO rules (from norahe0304-art/30x-seo — 24 production SEO skills):
- Title must include exact keyword + be under 60 chars
- Meta description: 150-160 chars, includes keyword, ends with value promise
- H1 = title (exact keyword). H2s = semantic variations of keyword
- First paragraph answers the question within 50 words (E-E-A-T signal)
- Include FAQ schema — minimum 3 questions people actually search
- Internal link opportunities: mention related ITVedas topics
- Image alt text must describe the image + include keyword where natural
- URL slug: lowercase, hyphens, no stop words, 3-5 words max

Anti-AI-detection rules (from rediumvex/seo-blog-writer + dongbeixiaohuo/writing-agent):
- Vary sentence lengths — mix 6-word and 25-word sentences in same paragraph
- Add first-person perspective occasionally: "Here's what I mean..."
- Use specific numbers and named examples, never vague: "45ms" not "fast"
- Alternate paragraph lengths: short (1 sentence), medium (3), long (4-5)
- Vary list lengths: sometimes 3 items, sometimes 7 — never always 5
- Hunt for "scenarios, costs, specific details" — lived experience elements
- Fact-anchor all claims: "DNS resolves in ~50ms on a fast connection"
- Never start two consecutive paragraphs with the same word

Design intelligence (styleseed + ux-skill + design-skill-os):
- Lead with the answer — never open with "In today's digital world..."
- Short paragraphs: 2-4 sentences max, active voice only
- Specific examples with real product/company names and numbers
- NEVER use: elevate, seamless, powerful, revolutionary, game-changer, leverage, utilize, paradigm
- Vary section lengths — density increases through the article (sparse → detailed)
- Code examples in <code> tags, terminal commands in <pre><code> blocks
- NO emoji bullets in content lists — use plain <ul>/<li> instead

Memory discipline (from coleam00/second-brain-starter):
- ALWAYS check existing articles before picking a topic
- Store every published article in memory immediately after publishing
- Never generate an article if the topic is already covered
- Search memory FIRST before any content decision
"""

# ─────────────────────────────────────────────────────────────────────────────
#  CHAPTERS config
# ─────────────────────────────────────────────────────────────────────────────
CHAPTERS = {
    "networking": {"name": "Networking", "emoji": "🌐", "color": "#FF6B35", "num": "01"},
    "cloud":      {"name": "Cloud Computing", "emoji": "☁️", "color": "#3B82F6", "num": "02"},
    "security":   {"name": "Security", "emoji": "🔐", "color": "#10B981", "num": "03"},
    "devops":     {"name": "DevOps", "emoji": "⚙️", "color": "#8B5CF6", "num": "04"},
    "databases":  {"name": "Databases", "emoji": "🗄️", "color": "#F59E0B", "num": "05"},
    "linux":      {"name": "Linux", "emoji": "🐧", "color": "#EF4444", "num": "06"},
    "hardware":   {"name": "Hardware", "emoji": "🖥️", "color": "#6366F1", "num": "07"},
    "compliance": {"name": "Compliance", "emoji": "📋", "color": "#14B8A6", "num": "08"},
    "cve":        {"name": "CVE Database", "emoji": "🛡️", "color": "#EF4444", "num": "09"},
}

# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC SEEDS — high-value IT search queries (research-agent pattern)
# ─────────────────────────────────────────────────────────────────────────────
TOPIC_SEEDS = {
    "networking": [
        "What is a subnet mask", "How does DHCP work", "What is BGP routing",
        "TCP vs UDP explained", "What is a MAC address", "How does NAT work",
        "What is VLAN", "How does OSPF work", "What is MPLS",
        "Difference between hub switch and router", "What is ARP protocol",
        "How does traceroute work", "What is QoS in networking",
        "What is SDN software defined networking", "How does IPv6 work",
    ],
    "cloud": [
        "What is cloud computing for beginners", "AWS vs Azure vs GCP",
        "What is serverless computing", "How does auto scaling work",
        "What is a CDN content delivery network", "What is IaaS PaaS SaaS",
        "How does load balancing work", "What is multi-cloud strategy",
        "What is cloud native development", "How does AWS Lambda work",
        "What is Kubernetes and why use it", "What is edge computing",
    ],
    "security": [
        "What is zero trust security", "How does SSL TLS work",
        "What is a man in the middle attack", "How does OAuth work",
        "What is SQL injection", "How does two factor authentication work",
        "What is a buffer overflow attack", "What is SIEM",
        "How does a DDoS attack work", "What is penetration testing",
        "What is social engineering in cybersecurity", "How does PKI work",
        "What is XSS cross site scripting", "What is CSRF attack",
    ],
    "devops": [
        "What is CI CD pipeline", "How does Docker work",
        "What is infrastructure as code", "How does Terraform work",
        "What is GitOps", "How does Ansible work",
        "What is a microservices architecture", "How does Jenkins work",
        "What is blue green deployment", "What is chaos engineering",
        "How does Prometheus monitoring work", "What is service mesh",
    ],
    "databases": [
        "SQL vs NoSQL databases", "What is database indexing",
        "How does database replication work", "What is ACID in databases",
        "What is database sharding", "How does Redis caching work",
        "What is a graph database", "How does PostgreSQL work",
        "What is database normalization", "What is CAP theorem",
    ],
    "linux": [
        "Linux file permissions explained", "What is a Linux shell",
        "How does cron job work", "What is systemd in Linux",
        "Linux vs Windows server", "What is SSH and how it works",
        "What is a Linux daemon", "How does the Linux kernel work",
        "What is Docker on Linux", "Linux process management explained",
    ],
    "hardware": [
        "How does a CPU work", "What is GPU computing",
        "How does SSD vs HDD differ", "What is RAID storage",
        "How does RAM work", "What is a network switch vs router",
        "How does a firewall appliance work", "What is a NIC network card",
    ],
    "compliance": [
        "What is GDPR compliance", "What is SOC 2 certification",
        "How does ISO 27001 work", "What is HIPAA in healthcare IT",
        "What is PCI DSS compliance", "What is NIST cybersecurity framework",
        "What is data residency", "GDPR vs CCPA differences",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────
def log(component: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] [{component}] {msg}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
#  MEMORY SYSTEM (second-brain-starter pattern)
#  Persistent across runs — stores published articles, topics, decisions
# ─────────────────────────────────────────────────────────────────────────────
def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except Exception:
            pass
    return {
        "published_articles": [],   # list of {slug, title, topic, chapter, date}
        "done_topics": [],          # flat list of topic strings already covered
        "failed_topics": [],        # topics that failed (skip for now)
        "decisions": [],            # important bot decisions log
        "stats": {"total_published": 0, "total_failed": 0, "last_run": None},
    }

def save_memory(mem: dict) -> None:
    mem["stats"]["last_run"] = datetime.datetime.utcnow().isoformat()
    MEMORY_FILE.write_text(json.dumps(mem, indent=2, ensure_ascii=False))
    log("memory", f"Saved. Published: {mem['stats']['total_published']} articles")

def memory_has_topic(mem: dict, topic: str) -> bool:
    """Check if topic (or very similar) already exists — prevents repetition."""
    topic_lower = topic.lower().strip()
    for done in mem["done_topics"]:
        if done.lower().strip() == topic_lower:
            return True
        # fuzzy: if 80%+ words overlap, consider it duplicate
        done_words = set(done.lower().split())
        topic_words = set(topic_lower.split())
        if len(done_words) > 2 and len(topic_words) > 2:
            overlap = len(done_words & topic_words) / max(len(done_words), len(topic_words))
            if overlap >= 0.8:
                return True
    return False

def scan_existing_articles(mem: dict) -> dict:
    """Scan /articles/ directory and sync memory with actual files on disk."""
    found = 0
    for html_file in ARTICLES.rglob("*.html"):
        slug = html_file.stem
        # skip index files and chapter pages
        if slug == "index" or not re.match(r"\d{4}-\d{2}-\d{2}-", slug):
            continue
        # check if already in memory
        known_slugs = {a["slug"] for a in mem["published_articles"]}
        if slug not in known_slugs:
            # extract title from file
            try:
                content = html_file.read_text(errors="ignore")
                m = re.search(r"<title>([^<]+)</title>", content)
                title = m.group(1).split("|")[0].strip() if m else slug
                # extract chapter from path
                chapter = html_file.parent.name if html_file.parent.name in CHAPTERS else "networking"
                mem["published_articles"].append({
                    "slug": slug, "title": title,
                    "chapter": chapter, "date": slug[:10],
                    "topic": title,
                })
                if title not in mem["done_topics"]:
                    mem["done_topics"].append(title)
                found += 1
            except Exception:
                pass
    if found:
        log("memory", f"Discovered {found} existing articles not in memory")
    return mem

# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC SELECTION (research-agent + knowledge-assistant patterns)
#  Picks best topic based on: not done, chapter balance, keyword value
# ─────────────────────────────────────────────────────────────────────────────
def pick_topic(mem: dict) -> tuple[str, str]:
    """Returns (topic, chapter). Uses Claude to pick intelligently if possible."""
    # count articles per chapter
    chapter_counts: dict[str, int] = {ch: 0 for ch in CHAPTERS}
    for art in mem["published_articles"]:
        ch = art.get("chapter", "networking")
        if ch in chapter_counts:
            chapter_counts[ch] += 1

    # build candidate list — prefer chapters with fewer articles
    candidates: list[tuple[str, str, int]] = []  # (topic, chapter, chapter_count)
    for chapter, topics in TOPIC_SEEDS.items():
        for topic in topics:
            if not memory_has_topic(mem, topic):
                candidates.append((topic, chapter, chapter_counts.get(chapter, 0)))

    if not candidates:
        log("topic", "All seeded topics done! Using Claude to generate new topic...")
        return _claude_generate_topic(mem)

    # sort by chapter count (fewest articles first) to balance coverage
    candidates.sort(key=lambda x: x[2])

    # use Claude to pick the best from top 10 candidates (DATAGEN multi-agent pattern)
    top_candidates = candidates[:10]
    if ANTHROPIC_KEY:
        try:
            return _claude_pick_best_topic(top_candidates, mem)
        except Exception as e:
            log("topic", f"Claude topic pick failed, using first candidate: {e}")

    topic, chapter, _ = candidates[0]
    log("topic", f"Selected: '{topic}' (chapter: {chapter})")
    return topic, chapter

def _claude_pick_best_topic(candidates: list, mem: dict) -> tuple[str, str]:
    """Use Claude to pick the highest-value topic from candidates."""
    done_count = len(mem["done_topics"])
    candidate_list = "\n".join(
        f"{i+1}. [{ch}] {topic}" for i, (topic, ch, _) in enumerate(candidates)
    )
    recent = [a["title"] for a in mem["published_articles"][-5:]]

    prompt = f"""You are a content strategist for ITVedas.com — an IT education site for beginners.

Recent articles published: {recent}
Total articles so far: {done_count}

Pick the BEST topic from this list to write next. Consider:
- Which has the highest search demand (people actively googling this)
- Which provides the most value to IT beginners
- Which is NOT too similar to recent articles

Candidates:
{candidate_list}

Reply with ONLY a JSON object:
{{"choice": <number 1-{len(candidates)}>, "reason": "<one sentence why>"}}"""

    raw = _call_claude(prompt, max_tokens=200)
    raw = _extract_json(raw)
    data = json.loads(raw)
    idx = int(data["choice"]) - 1
    topic, chapter, _ = candidates[idx]
    log("topic", f"Claude picked: '{topic}' ({chapter}) — {data.get('reason','')}")
    return topic, chapter

def _claude_generate_topic(mem: dict) -> tuple[str, str]:
    """
    Generate new topic using topic-cluster-architect 10-step strategy.
    When seeds exhausted, builds pillar→supporting content clusters.
    """
    done = mem["done_topics"][-30:]
    published_per_chapter = {}
    for art in mem["published_articles"]:
        ch = art.get("chapter", "networking")
        published_per_chapter[ch] = published_per_chapter.get(ch, 0) + 1

    prompt = f"""You are an SEO topic cluster architect for ITVedas.com (IT education for beginners).

Site diagnosis: Educational IT content site at early growth stage (~{len(mem['published_articles'])} articles).
Growth goal: Authority-building through comprehensive chapter coverage.

Articles per chapter so far: {published_per_chapter}
Recently covered topics: {done}

Using the topic-cluster-architect 10-step strategy:
1. Identify which chapter has the biggest content gap (fewest articles)
2. For that chapter, identify the most-searched beginner question not yet covered
3. Ensure it fits a pillar→supporting content cluster structure

Suggest ONE new IT topic that:
- Fills the biggest content gap
- Has high search demand (people actively Google this)
- Is beginner-friendly
- Is NOT similar to recently covered topics
- Would work as either a pillar page or supporting content

Reply with ONLY JSON:
{{
  "topic": "...",
  "chapter": "<one of: networking|cloud|security|devops|databases|linux|hardware|compliance>",
  "cluster_role": "pillar or supporting",
  "search_intent": "informational or navigational",
  "reason": "one sentence why this has high value"
}}"""

    raw = _call_claude(prompt, max_tokens=250)
    raw = _extract_json(raw)
    data = json.loads(raw)
    log("topic", f"Cluster architect: {data.get('cluster_role')} page — {data.get('reason','')}")
    return data["topic"], data.get("chapter", "networking")

# ─────────────────────────────────────────────────────────────────────────────
#  ARTICLE WRITER (content-writer.py + DATAGEN multi-agent pattern)
# ─────────────────────────────────────────────────────────────────────────────
def write_article(topic: str, chapter: str, anchor_facts: list | None = None) -> dict:
    """Generate full article. Returns structured data dict."""
    log("writer", f"Writing: '{topic}' [{chapter}]")
    anchor_facts = anchor_facts or []

    ch = CHAPTERS.get(chapter, CHAPTERS["networking"])
    today = datetime.date.today().isoformat()

    system = BOT_SOUL + f"""
You write articles for the {ch['name']} chapter of ITVedas.com.
Target audience: complete beginners to IT.
Writing style: friendly teacher, clear examples, no jargon without explanation.
"""

    pre_anchored = f"\nPre-validated anchor facts (use these):\n" + \
        "\n".join(f"- {f}" for f in anchor_facts) if anchor_facts else ""

    prompt = f"""Write a complete, high-quality SEO article about: "{topic}"
{pre_anchored}

PHASE 1 — EVIDENCE ANCHORING (from dongbeixiaohuo/writing-agent):
Before writing, identify 3-5 specific facts, numbers, or real examples that anchor this article.
(e.g. "DNS TTL is typically 300-86400 seconds", "Heartbleed affected OpenSSL 1.0.1 through 1.0.1f")

PHASE 2 — ARTICLE (800-1200 words, human-sounding):
Apply these rules from rediumvex/seo-blog-writer:
- Vary sentence lengths: mix 6-word and 25-word sentences in same paragraph
- Add first-person occasionally: "Here's what I mean..." or "Think of it this way..."
- Use specific numbers and named examples — never vague ("~50ms", "AWS EC2", "GitHub Actions")
- Alternate paragraph lengths: 1-sentence, 3-sentence, 4-sentence — never uniform
- Vary list lengths: 3 items or 7 items — never always exactly 5

SEO requirements (from norahe0304-art/30x-seo):
- Title: exact keyword + under 60 chars
- First paragraph: answers the question within 50 words
- H2 headings: semantic keyword variations
- Minimum 3 FAQ questions people actually search
- Include at least 1 code or command example if relevant

Return ONLY a valid JSON object — no markdown, no code fences:
{{
  "title": "Exact keyword in title, under 60 chars",
  "slug": "3-5-word-url-slug",
  "meta_description": "150-160 char description with keyword and value promise",
  "intro": "2-3 sentence answer to the question — leads with the answer, NOT a definition",
  "anchor_facts": ["specific fact 1 with number/source", "specific fact 2", "specific fact 3"],
  "sections": [
    {{
      "heading": "Semantic H2 heading (keyword variation)",
      "content": "HTML content using <p>, <ul>, <li>, <strong>, <code>, <pre> tags. Vary paragraph lengths."
    }}
  ],
  "faq": [
    {{"q": "Exact question people Google?", "answer": "Direct 2-3 sentence answer with specific detail."}},
    {{"q": "Another real search query?", "answer": "Specific answer."}},
    {{"q": "Third common question?", "answer": "Specific answer."}}
  ],
  "key_takeaways": ["specific takeaway with number/fact", "takeaway 2", "takeaway 3"],
  "related_topics": ["related ITVedas topic 1", "related topic 2"]
}}

    raw = _call_claude(prompt, system=system, max_tokens=4000)
    raw = _extract_json(raw)
    data = json.loads(raw)

    # add metadata
    data["chapter"] = chapter
    data["chapter_name"] = ch["name"]
    data["chapter_color"] = ch["color"]
    data["chapter_emoji"] = ch["emoji"]
    data["chapter_num"] = ch["num"]
    data["date"] = today
    data["topic"] = topic

    log("writer", f"Article written: '{data['title']}'")
    return data

# ─────────────────────────────────────────────────────────────────────────────
#  QA GATE (self-review from content-writer.py, DATAGEN pattern)
# ─────────────────────────────────────────────────────────────────────────────
def qa_review(data: dict) -> dict:
    """Claude reviews its own article and rewrites weak sections."""
    log("qa", "Self-reviewing article quality...")

    sections_text = "\n\n".join(
        f"## {s['heading']}\n{s['content']}" for s in data.get("sections", [])
    )

    prompt = f"""Review this IT article draft for quality:

Title: {data['title']}
Intro: {data['intro']}

{sections_text}

Score each section 1-10 on: clarity, accuracy, beginner-friendliness, value.
If any section scores below 7, rewrite it.

Return ONLY JSON:
{{
  "overall_score": <1-10>,
  "verdict": "PUBLISH" or "NEEDS_WORK",
  "sections": [
    {{"heading": "...", "content": "...(improved or same)", "score": <1-10>}}
  ],
  "intro": "...(improved or same)"
}}"""

    try:
        raw = _call_claude(prompt, max_tokens=3000)
        raw = _extract_json(raw)
        review = json.loads(raw)
        if review.get("verdict") == "NEEDS_WORK":
            log("qa", f"Rewriting weak sections (score: {review.get('overall_score')})")
            data["sections"] = review["sections"]
            data["intro"] = review.get("intro", data["intro"])
        else:
            log("qa", f"Article passed QA (score: {review.get('overall_score')}/10)")
    except Exception as e:
        log("qa", f"QA review failed (publishing anyway): {e}")

    return data

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN INTELLIGENCE SYSTEM
#  Sources: bitjaru/styleseed, Laith0003/ux-skill, frhscopex/design-skill-os,
#           funboy322/avoid-ai-design, rohitg00/awesome-claude-design
# ─────────────────────────────────────────────────────────────────────────────

DESIGN_RULES = """
=== ITVedas Design Intelligence (from ai-design repos) ===

TYPOGRAPHY RULES (styleseed + design-skill-os):
- Use Space Grotesk for headings ONLY — not body text (avoid Inter as display font)
- Body text: Inter at 16px min, line-height 1.7 (golden ratio: 1.618)
- Heading scale uses modular scale (1.25x ratio): h1→2.75rem, h2→1.45rem, h3→1.15rem
- Negative letter-spacing on headings: -0.025em (tight, intentional)
- Max line length: 70 characters (860px max-width container)
- Tabular numbers for stats/dates to prevent width jitter

COLOR RULES (styleseed + ux-skill 60-30-10 rule):
- 60% background: #0A0A0F (near-black, NOT pure #000 — refined black)
- 30% surface: #13131C (cards, panels)
- 10% accent: chapter color (single accent per page, everything else grayscale)
- Muted text: #8888A8 (never use gray-400 or lighter — contrast violation)
- Sub text: #D0D0E8 (body copy — passes 4.5:1 contrast ratio)
- NO purple-to-blue gradients (AI-slop tell #1)
- NO gradient text with bg-clip-text (AI-slop tell #2)
- Status/severity only for color — normal states stay neutral

SPATIAL RHYTHM (styleseed 8px grid):
- All spacing multiples of 8px: 8, 16, 24, 32, 48, 64, 80, 96
- Group gaps matter MORE than interior padding
- Information density increases downward (hero: sparse, content: dense)
- Never repeat same section type consecutively — alternate tall + compact
- Inner border-radius = outer radius minus padding (nested-radius law)

CARD RULES (styleseed):
- All content lives in cards with consistent border: 1px solid rgba(255,255,255,0.08)
- One corner radius personality per design: 12-14px for cards, 6px for inline
- Layered box-shadow at ≤8% opacity, lit from single direction (top-left)
- Cards must VARY in presentation — never 3 or 4 identical cards in a row
- Hover: translateY(-4px) + accent border-color (no scale transforms)

FORBIDDEN PATTERNS (ux-skill 152 rules + avoid-ai-design):
- NO emoji as UI icons — use text/unicode sparingly, SVG preferred
- NO pure emoji bullets in content lists
- NO "rounded-2xl shadow-lg" applied uniformly to everything
- NO reflexive glassmorphism (backdrop-blur for decoration only)
- NO generic CTAs: "Get Started", "Learn More", "Click Here"
- NO filler copy: "Elevate", "Seamless", "Powerful", "Revolutionary"
- NO Lorem ipsum anywhere
- NO bouncing arrow animations on CTAs
- NO default 300ms timing on all transitions — vary: 150ms micro, 250ms standard
- NO four identical KPI/feature cards in a row
- NO centered hero + three equal feature cards (the template tell)
- NO inline styles in output HTML
- NO console.log in scripts
- MUST have alt text on images
- MUST have aria-labels on icon-only buttons
- MUST NOT skip heading levels (h1 → h2 → h3, no jumps)
- MUST use cursor:pointer on all interactive elements

CONTENT QUALITY (design-skill-os + avoid-ai-design):
- Lead with the answer, not a definition ("DNS is..." not "In today's world...")
- Real examples with specific names/numbers — no vague "some companies"
- Code examples in <code> tags, terminal commands in <pre><code>
- Short paragraphs: 2-4 sentences max
- Vary section lengths — not all sections equal height
- Active voice: "DNS resolves names" not "names are resolved by DNS"
- Specificity beats generality: "saves 200ms" beats "saves time"

ACCESSIBILITY (ux-skill a11y rules):
- All images need alt text
- All interactive elements keyboard-navigable
- Focus rings visible (outline on :focus-visible)
- Color is never the ONLY indicator of meaning
- WCAG 2.1 AA minimum: 4.5:1 for normal text, 3:1 for large text
"""

def design_qa(html_content: str, data: dict) -> tuple[str, list[str]]:
    """
    Anti-AI-slop linter inspired by Laith0003/ux-skill.
    Checks for forbidden patterns and logs violations.
    Does NOT modify HTML — just reports issues for the record.
    """
    violations = []

    checks = [
        (r"#000000|#000(?![0-9a-fA-F])", "Pure black color used — use #2A2A2A or #0A0A0F instead"),
        (r"Lorem ipsum", "Lorem ipsum placeholder text detected"),
        (r"rounded-full.*rounded-full.*rounded-full", "Excessive rounded-full usage"),
        (r"console\.log", "console.log detected in output"),
        (r"(Elevate|Seamless|Powerful|Revolutionary|Game-changer|Next-level)", "AI-slop filler copy detected"),
        (r"Get Started|Click Here|Learn More", "Generic CTA copy detected"),
        (r"<img(?![^>]*alt=)", "Image missing alt text"),
        (r"style=\"[^\"]{50,}\"", "Long inline style detected — use CSS classes"),
        (r"background:\s*linear-gradient.*purple.*blue|background:\s*linear-gradient.*#[89abcdef].*#[34567]", "Purple-to-blue gradient (AI-slop tell)"),
    ]

    for pattern, msg in checks:
        if re.search(pattern, html_content, re.IGNORECASE):
            violations.append(msg)

    if violations:
        log("design-qa", f"{len(violations)} violation(s): {'; '.join(violations)}")
    else:
        log("design-qa", "All design rules passed")

    return html_content, violations


def apply_design_intelligence(data: dict) -> dict:
    """
    Uses Claude to apply design rules to article content before HTML generation.
    Inspired by styleseed judgment layer + design-skill-os red team audit.
    """
    if not ANTHROPIC_KEY:
        return data

    intro = data.get("intro", "")
    sections = data.get("sections", [])

    # Check for AI-slop tells in content
    slop_words = ["elevate", "seamless", "powerful", "revolutionary", "game-changer",
                  "next-level", "cutting-edge", "leverage", "utilize", "paradigm"]
    content_text = intro + " ".join(s.get("content","") for s in sections)
    found_slop = [w for w in slop_words if w.lower() in content_text.lower()]

    if not found_slop and len(sections) >= 3:
        log("design", "Content passes design check — no rewrite needed")
        return data

    log("design", f"Applying design intelligence (slop words found: {found_slop})")

    # Build a targeted prompt to fix only the issues found
    issues = []
    if found_slop:
        issues.append(f"Remove filler words: {found_slop}. Replace with specific, concrete language.")
    if len(sections) < 3:
        issues.append("Add more sections — minimum 4 for a complete article.")

    sections_json = json.dumps([{"heading": s["heading"], "content": s["content"]} for s in sections])

    prompt = f"""You are a design-aware content editor. Fix these issues in the article content:

Issues to fix:
{chr(10).join(f'- {i}' for i in issues)}

Design rules to follow:
- Lead with the answer immediately — no "In today's digital world..." intros
- Short paragraphs: 2-4 sentences max
- Active voice only
- Specific examples with real names/numbers
- NO filler words: elevate, seamless, powerful, revolutionary, game-changer
- Vary section lengths — not all equal

Current intro: {intro}

Current sections (JSON):
{sections_json}

Return ONLY JSON with fixed content:
{{"intro": "...", "sections": [{{"heading": "...", "content": "..."}}]}}"""

    try:
        raw = _call_claude(prompt, max_tokens=3000)
        raw = _extract_json(raw)
        fixed = json.loads(raw)
        data["intro"] = fixed.get("intro", intro)
        data["sections"] = fixed.get("sections", sections)
        log("design", "Content improved by design intelligence layer")
    except Exception as e:
        log("design", f"Design rewrite skipped: {e}")

    return data


# ─────────────────────────────────────────────────────────────────────────────
#  HTML BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_html(data: dict) -> str:
    """Build a complete, styled HTML article page."""
    esc_title = html.escape(data["title"])
    esc_desc  = html.escape(data["meta_description"])
    slug      = data["slug"]
    chapter   = data["chapter"]
    ch_name   = data["chapter_name"]
    ch_color  = data["chapter_color"]
    ch_emoji  = data["chapter_emoji"]
    date_str  = data["date"]
    canonical = f"{SITE_URL}/articles/{chapter}/{slug}.html"

    # FAQ schema
    faq_items = data.get("faq", [])
    faq_schema_entities = [
        {"@type": "Question", "name": html.escape(f["q"]),
         "acceptedAnswer": {"@type": "Answer", "text": html.escape(f["answer"])}}
        for f in faq_items
    ]
    faq_schema = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": faq_schema_entities
    }, ensure_ascii=True)

    article_schema = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": data["title"],
        "description": data["meta_description"],
        "datePublished": date_str,
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "url": canonical,
    }, ensure_ascii=True)

    breadcrumb_schema = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": ch_name, "item": f"{SITE_URL}/articles/{chapter}/"},
            {"@type": "ListItem", "position": 3, "name": data["title"], "item": canonical},
        ]
    }, ensure_ascii=True)

    # build sections HTML
    sections_html = ""
    for sec in data.get("sections", []):
        heading = html.escape(sec.get("heading", ""))
        content = sec.get("content", "")
        sections_html += f'<h2>{heading}</h2>\n{content}\n'

    # build FAQ HTML
    faq_html = ""
    if faq_items:
        faq_html = '<h2>Frequently Asked Questions</h2>\n<div class="faq">\n'
        for f in faq_items:
            faq_html += f'<div class="faq-item"><h3>{html.escape(f["q"])}</h3><p>{html.escape(f["answer"])}</p></div>\n'
        faq_html += "</div>\n"

    # key takeaways
    takeaways = data.get("key_takeaways", [])
    takeaways_html = ""
    if takeaways:
        items = "".join(f"<li>{html.escape(t)}</li>" for t in takeaways)
        takeaways_html = f'<div class="takeaways"><h2>Key Takeaways</h2><ul>{items}</ul></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/assets/logo-mark.svg">
<meta name="description" content="{esc_desc}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{esc_title} | {SITE_NAME}">
<meta property="og:description" content="{esc_desc}">
<meta property="og:image" content="{SITE_URL}/assets/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
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
:root{{--bg:#0A0A0F;--bg2:#13131C;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{ch_color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:0.875rem;transition:color .2s;}}
.nav-links a:hover{{color:var(--text);}}
.hero{{padding:8rem 2rem 3rem;max-width:860px;margin:0 auto;position:relative;}}
.breadcrumb{{font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.ch-badge{{display:inline-flex;align-items:center;gap:0.4rem;font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--accent);margin-bottom:1rem;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.8rem,4vw,2.75rem);font-weight:700;letter-spacing:-0.025em;line-height:1.15;margin-bottom:1.25rem;}}
.hero-meta{{display:flex;gap:1rem;font-size:0.8rem;color:var(--muted);margin-bottom:1.5rem;flex-wrap:wrap;}}
.hero p.intro{{font-size:1.1rem;color:var(--sub);line-height:1.75;}}
.content{{max-width:860px;margin:0 auto;padding:2rem 2rem 6rem;}}
.content h2{{font-family:'Space Grotesk',sans-serif;font-size:1.45rem;font-weight:700;margin:2.5rem 0 1rem;color:var(--text);letter-spacing:-0.015em;}}
.content h3{{font-family:'Space Grotesk',sans-serif;font-size:1.15rem;font-weight:600;margin:1.75rem 0 0.75rem;color:var(--text);}}
.content p{{color:var(--sub);margin-bottom:1.25rem;}}
.content ul,.content ol{{color:var(--sub);padding-left:1.5rem;margin-bottom:1.25rem;}}
.content li{{margin-bottom:0.4rem;}}
.content strong{{color:var(--text);}}
.content code{{background:var(--bg2);border:1px solid var(--border);border-radius:4px;padding:0.15em 0.45em;font-size:0.88em;color:#FF6B35;font-family:monospace;}}
.content pre{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:1.25rem;overflow-x:auto;margin-bottom:1.5rem;}}
.takeaways{{background:var(--bg2);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:12px;padding:1.5rem;margin:2rem 0;}}
.takeaways h2{{margin-top:0;font-size:1.1rem;}}
.takeaways ul{{margin-bottom:0;}}
.faq{{margin-top:1rem;}}
.faq-item{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:0.85rem;}}
.faq-item h3{{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;margin-bottom:0.5rem;color:var(--text);}}
.faq-item p{{margin:0;font-size:0.9rem;}}
.nav-art{{display:flex;justify-content:space-between;gap:1rem;margin-top:3rem;padding-top:2rem;border-top:1px solid var(--border);}}
.nav-art a{{flex:1;background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1rem 1.25rem;text-decoration:none;color:var(--sub);font-size:0.875rem;transition:border-color .2s;}}
.nav-art a:hover{{border-color:var(--accent);}}
.nav-art .label{{font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem;}}
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
  <div class="nav-links"><a href="/">Home</a><a href="/news.html">News</a><a href="/articles/{chapter}/">{ch_emoji} {ch_name}</a><a href="/#chapters">All Chapters</a><a href="mailto:info@itvedas.com">Contact</a></div>
</nav>
<div class="hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/articles/{chapter}/">{ch_name}</a> › {esc_title}</div>
  <div class="ch-badge">{ch_emoji} {ch_name}</div>
  <h1>{esc_title}</h1>
  <div class="hero-meta"><span>📅 {date_str}</span><span>✍️ ITVedas Bot v2</span><span>⏱️ 5 min read</span></div>
  <p class="intro">{html.escape(data['intro'])}</p>
</div>
<div class="content">
{sections_html}
{takeaways_html}
{faq_html}
  <div class="nav-art">
    <a href="/articles/{chapter}/"><div class="label">← Chapter</div>{ch_emoji} Back to {ch_name}</a>
    <a href="/#chapters"><div class="label">Explore →</div>All Chapters</a>
  </div>
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks"><a href="/">Home</a><a href="/news.html">News</a><a href="/articles/{chapter}/">{ch_name}</a><a href="/#chapters">Chapters</a><a href="mailto:info@itvedas.com">Contact</a></div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} ITVedas · Knowledge for everyone</p>
</footer>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  GITHUB PUBLISHER (github-agent.py pattern — pushes directly via API)
# ─────────────────────────────────────────────────────────────────────────────
def github_put(path: str, content: str, message: str) -> bool:
    """Create or update a file in the GitHub repo via API."""
    import base64
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    # get existing SHA if file exists
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        res = json.load(urllib.request.urlopen(req, timeout=30))
        sha = res.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            log("github", f"GET {path} failed: {e}")
    except Exception:
        pass

    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers=headers, method="PUT"
        )
        urllib.request.urlopen(req, timeout=30)
        log("github", f"Published: {path}")
        return True
    except Exception as e:
        log("github", f"PUT {path} failed: {e}")
        return False

def publish_to_github(data: dict, html_content: str) -> bool:
    """Push article HTML to GitHub."""
    if not GITHUB_TOKEN:
        log("github", "No GITHUB_TOKEN — saving locally only")
        return _save_locally(data, html_content)

    chapter = data["chapter"]
    slug    = data["slug"]
    date    = data["date"]
    fname   = f"{date}-{slug}.html"
    path    = f"articles/{chapter}/{fname}"
    message = f"bot: add article '{data['title']}' [{chapter}]"

    return github_put(path, html_content, message)

def _save_locally(data: dict, html_content: str) -> bool:
    """Fallback: save to local filesystem."""
    chapter = data["chapter"]
    slug    = data["slug"]
    date    = data["date"]
    fname   = f"{date}-{slug}.html"
    out_dir = ARTICLES / chapter
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / fname
    out_path.write_text(html_content, encoding="utf-8")
    log("local", f"Saved: {out_path}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
#  HEARTBEAT (second-brain-starter heartbeat pattern)
#  Logs health + next recommended topics after every run
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#  TASK MANAGEMENT SYSTEM
#  Sources: dongshuyan/compass-skills, cortex-tms, jpicklyk/task-orchestrator,
#           saltbo/agent-kanban, builderz-labs/mission-control
# ─────────────────────────────────────────────────────────────────────────────

def task_clarifier(topic: str, chapter: str, mem: dict) -> dict:
    """
    compass-skills/task-clarifier pattern:
    Aligns goals, scope, evidence, acceptance criteria, and risk boundaries
    BEFORE writing — prevents wasted generation on bad topic choices.
    """
    done_count = len(mem["done_topics"])
    chapter_articles = [a for a in mem["published_articles"] if a.get("chapter") == chapter]

    prompt = f"""You are a task clarifier for an IT education content bot.

Before writing an article about "{topic}" for the {chapter} chapter of ITVedas.com,
clarify and validate this task. The site has {done_count} articles total,
{len(chapter_articles)} in the {chapter} chapter.

Evaluate:
1. GOAL: Is "{topic}" a clear, specific topic with measurable search demand?
2. SCOPE: Is it too broad (split into parts) or too narrow (merge with another)?
3. EVIDENCE: What 3 specific facts/numbers can anchor this article?
4. ACCEPTANCE: What makes this article "done"? (word count, sections, FAQ count)
5. RISK: Any accuracy risks? (rapidly changing tech, controversial claims?)

Return ONLY JSON:
{{
  "approved": true,
  "refined_topic": "...(same or slightly improved topic title)",
  "scope": "single-article or needs-split",
  "anchor_facts": ["fact with number", "fact with name", "fact with example"],
  "acceptance_criteria": {{"min_words": 800, "min_sections": 4, "min_faq": 3}},
  "risk_level": "low|medium|high",
  "risk_note": "...or null"
}}"""

    try:
        raw = _call_claude(prompt, max_tokens=400)
        raw = _extract_json(raw)
        result = json.loads(raw)
        if result.get("refined_topic") and result["refined_topic"] != topic:
            log("task-clarifier", f"Topic refined: '{topic}' → '{result['refined_topic']}'")
        if result.get("risk_level") == "high":
            log("task-clarifier", f"HIGH RISK: {result.get('risk_note')}")
        return result
    except Exception as e:
        log("task-clarifier", f"Skipped (non-blocking): {e}")
        return {"approved": True, "refined_topic": topic, "anchor_facts": [],
                "acceptance_criteria": {"min_words": 800, "min_sections": 4, "min_faq": 3}}


def task_forest_update(mem: dict, topic: str, chapter: str, status: str,
                       slug: str = "", notes: str = "") -> dict:
    """
    compass-skills/task-forest pattern:
    Maintains a DAG of tasks with goals, subtasks, dependencies, progress,
    deviations, decisions, and history. File: state/task-forest.json
    """
    forest_file = STATE_DIR / "task-forest.json"
    forest: dict = {}
    if forest_file.exists():
        try:
            forest = json.loads(forest_file.read_text())
        except Exception:
            pass

    if "tasks" not in forest:
        forest["tasks"] = {}
    if "chapter_goals" not in forest:
        forest["chapter_goals"] = {ch: f"Comprehensive {cfg['name']} coverage for beginners"
                                    for ch, cfg in CHAPTERS.items()}
    if "decisions" not in forest:
        forest["decisions"] = []

    task_id = f"{chapter}/{slug or topic[:30].replace(' ', '-').lower()}"
    forest["tasks"][task_id] = {
        "topic": topic,
        "chapter": chapter,
        "status": status,   # pending|in_progress|done|failed
        "slug": slug,
        "notes": notes,
        "updated": datetime.datetime.utcnow().isoformat(),
    }

    # record decision log (task-orchestrator workflow discipline)
    if status == "done":
        forest["decisions"].append({
            "date": datetime.date.today().isoformat(),
            "decision": f"Published '{topic}' in {chapter}",
            "outcome": "success",
        })
    elif status == "failed":
        forest["decisions"].append({
            "date": datetime.date.today().isoformat(),
            "decision": f"Attempted '{topic}' in {chapter}",
            "outcome": "failed",
            "notes": notes,
        })

    # tiered memory summary (cortex-tms pattern)
    forest["summary"] = {
        "total_tasks": len(forest["tasks"]),
        "done": sum(1 for t in forest["tasks"].values() if t["status"] == "done"),
        "failed": sum(1 for t in forest["tasks"].values() if t["status"] == "failed"),
        "in_progress": sum(1 for t in forest["tasks"].values() if t["status"] == "in_progress"),
        "last_updated": datetime.datetime.utcnow().isoformat(),
    }

    forest_file.write_text(json.dumps(forest, indent=2, ensure_ascii=False))
    return forest


def session_handoff(mem: dict, topic: str, chapter: str, result: str) -> None:
    """
    compass-skills/session-handoff-prompt pattern:
    Compresses current session state into a paste-ready prompt for next run.
    Saves to state/session-handoff.md
    """
    handoff_file = STATE_DIR / "session-handoff.md"
    recent = [a["title"] for a in mem["published_articles"][-5:]]
    next_topics = []
    for ch, topics in TOPIC_SEEDS.items():
        for t in topics:
            if not memory_has_topic(mem, t):
                next_topics.append(f"[{ch}] {t}")
            if len(next_topics) >= 5:
                break
        if len(next_topics) >= 5:
            break

    handoff = f"""# ITVedas Bot — Session Handoff
Generated: {datetime.datetime.utcnow().isoformat()}

## Last Session
- Topic attempted: {topic}
- Chapter: {chapter}
- Result: {result}

## Current State
- Total articles published: {mem['stats']['total_published']}
- Total topics done: {len(mem['done_topics'])}
- Total failures: {mem['stats']['total_failed']}

## Recent Articles (last 5)
{chr(10).join(f'- {t}' for t in recent)}

## Recommended Next Topics
{chr(10).join(f'- {t}' for t in next_topics)}

## Resume Instructions
Run: python itvedas-brain/itvedas-bot-v2.py
Memory auto-loads from: itvedas-brain/memory/bot_memory.json
Task forest at: itvedas-brain/state/task-forest.json
"""
    handoff_file.write_text(handoff)
    log("session-handoff", "Handoff saved for next session")


def write_heartbeat(mem: dict, result: str, topic: str, chapter: str) -> None:
    chapter_counts = {}
    for art in mem["published_articles"]:
        ch = art.get("chapter", "?")
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

    # find next 5 recommended topics
    next_topics = []
    for ch, topics in TOPIC_SEEDS.items():
        for t in topics:
            if not memory_has_topic(mem, t):
                next_topics.append({"topic": t, "chapter": ch})
            if len(next_topics) >= 5:
                break
        if len(next_topics) >= 5:
            break

    heartbeat = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "last_run_result": result,
        "last_topic": topic,
        "last_chapter": chapter,
        "total_published": mem["stats"]["total_published"],
        "total_failed": mem["stats"]["total_failed"],
        "articles_per_chapter": chapter_counts,
        "next_recommended_topics": next_topics,
        "memory_file": str(MEMORY_FILE),
    }
    HEARTBEAT.write_text(json.dumps(heartbeat, indent=2))
    log("heartbeat", f"Logged. Total published: {mem['stats']['total_published']}")

# ─────────────────────────────────────────────────────────────────────────────
#  CLAUDE API HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _call_claude(prompt: str, system: str | None = None, max_tokens: int = 4000) -> str:
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
            res = json.load(urllib.request.urlopen(req, timeout=120))
            return res["content"][0]["text"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            log("claude", f"Retry {attempt+1}: {e}")
            time.sleep(8)
    return ""

def _extract_json(text: str) -> str:
    """Extract JSON from text — strips markdown fences and finds first { }."""
    text = text.strip()
    # strip code fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    # find outermost { }
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

# ─────────────────────────────────────────────────────────────────────────────
#  SOUL / USER memory files (second-brain-starter pattern)
# ─────────────────────────────────────────────────────────────────────────────
def ensure_soul_files() -> None:
    """Create SOUL.md and USER.md if they don't exist."""
    if not SOUL_FILE.exists():
        SOUL_FILE.write_text(BOT_SOUL)
        log("soul", "Created SOUL.md")

    if not USER_FILE.exists():
        USER_FILE.write_text(f"""# ITVedas Bot — User/Site Profile

## Site
- URL: {SITE_URL}
- Name: {SITE_NAME}
- Type: IT education platform for beginners
- GitHub: {GITHUB_REPO}

## Content Strategy
- Write 1 article per run
- Cover all 9 chapters evenly
- Target: 200+ articles total
- Style: beginner-friendly, SEO-optimised, real examples

## Active Chapters
{chr(10).join(f"- {ch}: {cfg['name']}" for ch, cfg in CHAPTERS.items())}

## Notes
- No OpenAI required — Claude only
- Articles auto-publish to GitHub via API
- Memory persists across all runs in memory/bot_memory.json
""")
        log("soul", "Created USER.md")

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    log("bot", "=== ITVedas Super Bot v2 starting ===")

    if not ANTHROPIC_KEY:
        log("bot", "ERROR: ANTHROPIC_API_KEY not set")
        return 1

    # 1. SOUL files
    ensure_soul_files()

    # 2. MEMORY CHECK — load + sync with actual files
    log("memory", "Loading memory...")
    mem = load_memory()
    mem = scan_existing_articles(mem)
    log("memory", f"Known articles: {len(mem['published_articles'])}, Done topics: {len(mem['done_topics'])}")

    # 3. TOPIC PICK — intelligent, never repeats
    topic, chapter = pick_topic(mem)

    # 3b. TASK CLARIFIER — validate + refine topic before writing (compass-skills)
    task_forest_update(mem, topic, chapter, "in_progress")
    clarification = task_clarifier(topic, chapter, mem)
    topic = clarification.get("refined_topic", topic)  # use refined topic if improved
    anchor_facts = clarification.get("anchor_facts", [])
    log("task", f"Clarified: '{topic}' | risk={clarification.get('risk_level','low')}")

    # 4. WRITE
    try:
        data = write_article(topic, chapter, anchor_facts=anchor_facts)
    except Exception as e:
        log("writer", f"FAILED: {e}")
        mem["failed_topics"].append(topic)
        mem["stats"]["total_failed"] += 1
        task_forest_update(mem, topic, chapter, "failed", notes=str(e))
        save_memory(mem)
        write_heartbeat(mem, "FAILED", topic, chapter)
        session_handoff(mem, topic, chapter, "FAILED")
        return 1

    # 5. QA GATE
    data = qa_review(data)

    # 5b. DESIGN INTELLIGENCE — anti-AI-slop + design rules
    data = apply_design_intelligence(data)

    # 6. BUILD HTML
    html_content = build_html(data)

    # 6b. DESIGN QA — lint the final HTML
    html_content, violations = design_qa(html_content, data)
    if violations:
        mem["decisions"].append({
            "date": datetime.date.today().isoformat(),
            "topic": topic,
            "design_violations": violations,
        })

    # 7. PUBLISH
    ok = publish_to_github(data, html_content)
    if not ok:
        log("bot", "Publish failed")
        mem["failed_topics"].append(topic)
        mem["stats"]["total_failed"] += 1
        save_memory(mem)
        write_heartbeat(mem, "PUBLISH_FAILED", topic, chapter)
        return 1

    # 8. MEMORY UPDATE — critical: save before anything else
    slug_full = f"{data['date']}-{data['slug']}"
    mem["published_articles"].append({
        "slug": slug_full,
        "title": data["title"],
        "topic": topic,
        "chapter": chapter,
        "date": data["date"],
    })
    mem["done_topics"].append(topic)
    mem["stats"]["total_published"] += 1
    save_memory(mem)

    # 8b. TASK FOREST UPDATE — mark done (compass-skills/task-forest)
    task_forest_update(mem, topic, chapter, "done", slug=slug_full)

    # 9. HEARTBEAT + SESSION HANDOFF
    write_heartbeat(mem, "SUCCESS", topic, chapter)
    session_handoff(mem, topic, chapter, "SUCCESS")

    log("bot", f"=== DONE: '{data['title']}' published to {chapter}/ ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
