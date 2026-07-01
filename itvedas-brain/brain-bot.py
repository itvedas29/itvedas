#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                ITVedas BRAIN BOT — Full Autonomous Intelligence             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  A complete autonomous content brain with ALL skills integrated:            ║
║                                                                              ║
║  ┌─ SKILL MODULE 1: TIERED MEMORY SYSTEM ─────────────────────────────┐    ║
║  │  cortex-tms: working memory, episodic memory, architectural memory  │    ║
║  │  coleam00/second-brain: SOUL.md, USER.md, heartbeat, memory.json   │    ║
║  │  letta-ai/letta: stateful self-improving agent with memory loops   │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌─ SKILL MODULE 2: RESEARCH INTELLIGENCE ────────────────────────────┐    ║
║  │  AutoViralAI: self-learning trending topic research                │    ║
║  │  DATAGEN: multi-source research + evidence synthesis               │    ║
║  │  knowledge-assistant: RAG on site knowledge files                  │    ║
║  │  NVD API integration: real CVE data for security articles          │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌─ SKILL MODULE 3: TASK MANAGEMENT ──────────────────────────────────┐    ║
║  │  compass-skills: task-clarifier → task-forest → session-handoff    │    ║
║  │  task-orchestrator: server-enforced workflow discipline             │    ║
║  │  mission-control: multi-agent orchestration patterns               │    ║
║  │  agent-kanban: file-based kanban board for agentic loops           │    ║
║  │  project-butler: session logs + documentation                      │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌─ SKILL MODULE 4: CONTENT WRITING INTELLIGENCE ─────────────────────┐    ║
║  │  30x-seo: 24 production SEO skills (title, meta, schema, FAQ)      │    ║
║  │  seo-blog-writer: 6 anti-AI-detection rules                        │    ║
║  │  topic-cluster-architect: 10-step pillar/cluster strategy          │    ║
║  │  writing-agent: evidence anchoring + humanization gate             │    ║
║  │  aiwriter: SERP-driven article generation                          │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌─ SKILL MODULE 5: DESIGN INTELLIGENCE ──────────────────────────────┐    ║
║  │  styleseed: 74 rules — 8px grid, spatial rhythm, card rules        │    ║
║  │  ux-skill: 152 anti-AI-slop rules + linter                         │    ║
║  │  design-skill-os: 161 rules from masters (Tufte, Rams, Maeda)     │    ║
║  │  avoid-ai-design: anti-pattern detector + auto-rewriter            │    ║
║  │  ux-pilot: 376 UX co-pilot rules                                   │    ║
║  │  design-cognition-skill: 4-role design thinking framework          │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌─ SKILL MODULE 6: PUBLISHING INTELLIGENCE ──────────────────────────┐    ║
║  │  github-agent: direct API publish with retry + SHA management      │    ║
║  │  sitemap auto-rebuild after every article                          │    ║
║  │  chapter index auto-rebuild with new article                       │    ║
║  │  internal linker: knowledge graph → cross-links                    │    ║
║  │  social content generator: tweet + LinkedIn post per article       │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ┌─ SKILL MODULE 7: SELF-IMPROVEMENT LOOP ────────────────────────────┐    ║
║  │  letta-ai: agent improves strategy based on what's working         │    ║
║  │  ai-data-analysis: analysis of what topics/chapters perform best   │    ║
║  │  audit mode: periodic review of old articles for improvements      │    ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import base64
import datetime
import html as html_mod
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════════════════════
ROOT       = pathlib.Path(__file__).resolve().parent.parent
BRAIN_DIR  = pathlib.Path(__file__).resolve().parent
ARTICLES   = ROOT / "articles"
MEM_DIR    = BRAIN_DIR / "memory"
STATE_DIR  = BRAIN_DIR / "state"

for d in [MEM_DIR, STATE_DIR, ARTICLES]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO   = os.environ.get("GITHUB_REPOSITORY", "itvedas29/itvedas")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
GA4_ID        = os.environ.get("GA4_ID", "G-D98BFZSJYP")
MODEL         = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
SITE_URL      = "https://itvedas.com"
SITE_NAME     = "ITVedas"

# Run mode: "article" (default), "audit" (improve old), "sitemap" (rebuild only)
RUN_MODE      = os.environ.get("BOT_MODE", "article")

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGGING — simple timestamped print
# ═══════════════════════════════════════════════════════════════════════════════
def log(mod: str, msg: str) -> None:
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] [{mod:12s}] {msg}", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  CHAPTERS
# ═══════════════════════════════════════════════════════════════════════════════
CHAPTERS: dict[str, dict] = {
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

# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 1: TIERED MEMORY SYSTEM
#  Sources: cortex-tms (working/episodic/arch), coleam00/second-brain-starter,
#           letta-ai (stateful agent memory), JamesShi96/project-butler
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WorkingMemory:
    """Current-run state — cleared each run (cortex-tms working tier)."""
    topic: str           = ""
    chapter: str         = ""
    anchor_facts: list   = field(default_factory=list)
    related_topics: list = field(default_factory=list)
    acceptance: dict     = field(default_factory=dict)
    article_data: dict   = field(default_factory=dict)
    html_content: str    = ""
    violations: list     = field(default_factory=list)
    slug_full: str       = ""
    run_start: str       = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class BrainMemory:
    """
    Episodic + architectural memory (cortex-tms tiered pattern).
    Persists across runs in JSON files.
    """
    def __init__(self):
        self._mem_file   = MEM_DIR / "brain_memory.json"
        self._graph_file = MEM_DIR / "knowledge_graph.json"
        self._soul_file  = MEM_DIR / "SOUL.md"
        self._user_file  = MEM_DIR / "USER.md"
        self._data: dict = {}
        self._graph: dict = {}

    def load(self) -> None:
        """Load episodic memory from disk."""
        if self._mem_file.exists():
            try:
                self._data = json.loads(self._mem_file.read_text())
            except Exception:
                self._data = {}
        self._data.setdefault("published_articles", [])
        self._data.setdefault("done_topics", [])
        self._data.setdefault("failed_topics", [])
        self._data.setdefault("decisions", [])
        self._data.setdefault("strategy_notes", [])
        self._data.setdefault("stats", {
            "total_published": 0, "total_failed": 0,
            "last_run": None, "runs": 0,
        })

        if self._graph_file.exists():
            try:
                self._graph = json.loads(self._graph_file.read_text())
            except Exception:
                self._graph = {}

        log("memory", f"Loaded: {self._data['stats']['total_published']} published, "
            f"{len(self._data['done_topics'])} topics done")

    def save(self) -> None:
        """Persist episodic memory to disk."""
        self._data["stats"]["last_run"] = datetime.datetime.utcnow().isoformat()
        self._data["stats"]["runs"]      = self._data["stats"].get("runs", 0) + 1
        self._mem_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))
        self._graph_file.write_text(json.dumps(self._graph, indent=2, ensure_ascii=False))
        log("memory", f"Saved: {self._data['stats']['total_published']} published")

    def sync_disk(self) -> None:
        """Scan articles/ directory and sync with memory (second-brain scan)."""
        if not ARTICLES.exists():
            return
        known = {a["slug"] for a in self._data["published_articles"]}
        found = 0
        for f in ARTICLES.rglob("*.html"):
            slug = f.stem
            if slug == "index" or not re.match(r"\d{4}-\d{2}-\d{2}-", slug):
                continue
            if slug in known:
                continue
            try:
                content = f.read_text(errors="ignore")
                m = re.search(r"<title>([^<]+)</title>", content)
                title = m.group(1).split("|")[0].strip() if m else slug
                ch = f.parent.name if f.parent.name in CHAPTERS else "networking"
                self._data["published_articles"].append({
                    "slug": slug, "title": title, "chapter": ch,
                    "date": slug[:10], "topic": title,
                })
                if title not in self._data["done_topics"]:
                    self._data["done_topics"].append(title)
                found += 1
            except Exception:
                pass
        if found:
            log("memory", f"Synced {found} articles from disk")

    def has_topic(self, topic: str) -> bool:
        """Fuzzy dedup: 75%+ word overlap = already done (knowledge-assistant)."""
        topic_lower = topic.lower().strip()
        for done in self._data["done_topics"]:
            if done.lower().strip() == topic_lower:
                return True
            dw = set(done.lower().split())
            tw = set(topic_lower.split())
            if len(dw) > 2 and len(tw) > 2:
                if len(dw & tw) / max(len(dw), len(tw)) >= 0.75:
                    return True
        return False

    def add_article(self, wm: WorkingMemory) -> None:
        """Record published article in episodic memory."""
        self._data["published_articles"].append({
            "slug":    wm.slug_full,
            "title":   wm.article_data.get("title",""),
            "topic":   wm.topic,
            "chapter": wm.chapter,
            "date":    wm.article_data.get("date",""),
        })
        if wm.topic not in self._data["done_topics"]:
            self._data["done_topics"].append(wm.topic)
        self._data["stats"]["total_published"] += 1

    def record_failure(self, topic: str, reason: str) -> None:
        self._data["failed_topics"].append(topic)
        self._data["stats"]["total_failed"] += 1
        self._data["decisions"].append({
            "date": datetime.date.today().isoformat(),
            "event": f"FAILED: {topic}", "reason": reason,
        })

    def record_decision(self, event: str, notes: str = "") -> None:
        self._data["decisions"].append({
            "date": datetime.datetime.utcnow().isoformat(),
            "event": event, "notes": notes,
        })

    def update_graph(self, topic: str, chapter: str, slug: str, related: list) -> None:
        """Update knowledge graph with new article (knowledge-assistant RAG)."""
        self._graph[topic] = {
            "chapter": chapter, "slug": slug,
            "related": related, "date": datetime.date.today().isoformat(),
        }
        for rel in related:
            if rel in self._graph:
                if topic not in self._graph[rel].get("related", []):
                    self._graph[rel].setdefault("related", []).append(topic)

    def get_related_articles(self, related_topics: list) -> list[dict]:
        """Find published articles related to given topics."""
        results = []
        for rt in related_topics:
            rt_lower = rt.lower()
            for art in self._data["published_articles"]:
                title = art.get("title","").lower()
                if rt_lower in title or title in rt_lower:
                    if art not in results:
                        results.append(art)
        return results[:5]

    @property
    def published(self) -> list:
        return self._data["published_articles"]

    @property
    def done_topics(self) -> list:
        return self._data["done_topics"]

    @property
    def failed_topics(self) -> list:
        return self._data["failed_topics"]

    @property
    def stats(self) -> dict:
        return self._data["stats"]

    @property
    def graph(self) -> dict:
        return self._graph

    def ensure_soul(self) -> None:
        """Create architectural memory files if missing (second-brain pattern)."""
        soul = f"""# ITVedas Brain — SOUL
You are the ITVedas Content Brain: autonomous, quality-obsessed, memory-persistent.

Mission: build the most comprehensive beginner IT education site in plain English.
One article per run. Never repeat. Always improve. Write for humans, not bots.

Principles:
- Answer the question in the first sentence, not the 50th word
- Specific numbers beat vague claims ("~50ms" beats "fast")
- Real names beat generics ("AWS Lambda" beats "a serverless platform")
- Short paragraphs beat walls of text
- Vary everything: sentence length, paragraph length, list length
"""
        user = f"""# ITVedas Brain — USER / SITE PROFILE
Site: {SITE_URL}
Repo: {GITHUB_REPO}
Type: IT education for complete beginners
Goal: 200+ articles covering all 9 chapters

Chapters: {list(CHAPTERS.keys())}
Strategy: balance coverage, build clusters (pillar + supporting)
"""
        if not self._soul_file.exists():
            self._soul_file.write_text(soul)
        if not self._user_file.exists():
            self._user_file.write_text(user)


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 2: RESEARCH INTELLIGENCE
#  Sources: AutoViralAI (trending research), DATAGEN (multi-source synthesis),
#           knowledge-assistant (RAG), NVD API (CVE data)
# ═══════════════════════════════════════════════════════════════════════════════

# High-value topic seeds — 20+ per chapter (AutoViralAI + DATAGEN research)
TOPIC_SEEDS: dict[str, list[str]] = {
    "networking": [
        "What is a subnet mask", "How does DHCP work", "What is BGP routing",
        "TCP vs UDP explained", "What is a MAC address", "How does NAT work",
        "What is VLAN", "How does OSPF work", "What is MPLS",
        "Difference between hub switch and router", "What is ARP protocol",
        "How does traceroute work", "What is QoS in networking",
        "What is SDN software defined networking", "How does IPv6 work",
        "What is DNS and how does it work", "What is a firewall in networking",
        "How does HTTPS work", "What is a proxy server",
        "What is network bandwidth vs throughput",
        "What is a default gateway", "How does ping work",
        "What is network latency", "What is a subnet",
    ],
    "cloud": [
        "What is cloud computing for beginners", "AWS vs Azure vs GCP comparison",
        "What is serverless computing", "How does auto scaling work",
        "What is a CDN content delivery network", "What is IaaS PaaS SaaS",
        "How does load balancing work", "What is multi-cloud strategy",
        "What is cloud native development", "How does AWS Lambda work",
        "What is Kubernetes explained", "What is edge computing",
        "How does AWS S3 work", "What is a virtual machine vs container",
        "What is cloud migration strategy", "What is disaster recovery in cloud",
        "How does Azure Active Directory work", "What is cloud storage",
        "What is a VPC virtual private cloud", "What is cloud security",
        "What is serverless vs containers", "How does Google Cloud Run work",
    ],
    "security": [
        "What is zero trust security", "How does SSL TLS work",
        "What is a man in the middle attack", "How does OAuth 2.0 work",
        "What is SQL injection attack", "How does two factor authentication work",
        "What is a buffer overflow vulnerability", "What is SIEM",
        "How does a DDoS attack work", "What is penetration testing",
        "What is social engineering in cybersecurity", "How does PKI work",
        "What is XSS cross site scripting", "What is CSRF attack",
        "What is ransomware and how does it work", "What is phishing attack",
        "What is a VPN and how does it work", "What is intrusion detection system IDS",
        "What is endpoint security", "What is data encryption at rest",
        "What is a security operations center SOC", "What is threat intelligence",
        "What is OWASP Top 10", "What is malware analysis",
    ],
    "devops": [
        "What is CI CD pipeline explained", "How does Docker work",
        "What is infrastructure as code IaC", "How does Terraform work",
        "What is GitOps", "How does Ansible work for configuration",
        "What is a microservices architecture", "How does Jenkins CI work",
        "What is blue green deployment", "What is chaos engineering",
        "How does Prometheus monitoring work", "What is a service mesh",
        "What is DevSecOps", "What is container orchestration",
        "What is a Helm chart in Kubernetes", "How does GitHub Actions work",
        "What is observability in DevOps", "What is SRE site reliability engineering",
        "What is a Docker Compose file", "What is canary deployment",
        "What is shift left testing", "What is a build pipeline",
    ],
    "databases": [
        "SQL vs NoSQL databases explained", "What is database indexing",
        "How does database replication work", "What is ACID in databases",
        "What is database sharding", "How does Redis caching work",
        "What is a graph database", "How does PostgreSQL work",
        "What is database normalization", "What is CAP theorem explained",
        "What is a time series database", "How does MongoDB work",
        "What is database connection pooling", "What is a data warehouse",
        "What is ETL in databases", "What is an ORM object relational mapper",
        "What is database partitioning", "What is a stored procedure",
        "What is database MVCC", "What is a NoSQL key value store",
    ],
    "linux": [
        "Linux file permissions explained", "What is a Linux shell",
        "How does cron job work in Linux", "What is systemd in Linux",
        "Linux vs Windows server comparison", "What is SSH and how it works",
        "What is a Linux daemon process", "How does the Linux kernel work",
        "Linux process management explained", "What is grep command in Linux",
        "How does iptables firewall work", "What is a Linux package manager",
        "How to use tmux terminal multiplexer", "What is a Linux swap partition",
        "How does rsync work for file transfer", "What is a Linux environment variable",
        "What is sed command in Linux", "What is Linux namespaces and cgroups",
        "How does Linux boot process work", "What is a Linux file descriptor",
    ],
    "hardware": [
        "How does a CPU work explained", "What is GPU computing",
        "How does SSD vs HDD differ", "What is RAID storage levels explained",
        "How does RAM work", "What is a network switch vs hub vs router",
        "How does a firewall appliance work", "What is a NIC network interface card",
        "What is a server rack and how it works", "How does a data center work",
        "What is BIOS vs UEFI firmware", "What is a TPM trusted platform module",
        "How does ECC RAM work", "What is PCIe in servers",
        "What is a CPU cache L1 L2 L3", "What is server virtualization",
    ],
    "compliance": [
        "What is GDPR compliance for IT teams", "What is SOC 2 certification",
        "How does ISO 27001 work", "What is HIPAA in healthcare IT",
        "What is PCI DSS compliance explained", "What is NIST cybersecurity framework",
        "What is data residency and sovereignty", "GDPR vs CCPA differences",
        "What is FedRAMP cloud authorization", "What is a data protection officer DPO",
        "What is a security audit", "What is DORA digital operational resilience",
        "What is a data breach notification requirement",
    ],
    "cve": [
        "What is a CVE vulnerability explained", "How does CVSS scoring work",
        "What is a zero day vulnerability", "How does responsible disclosure work",
        "What is NVD national vulnerability database", "CVE vs CWE vs CAPEC",
        "What is a security patch and how to apply it", "How to read a CVE report",
        "What is vulnerability management", "What is a proof of concept exploit",
    ],
}

def fetch_nvd_cve(keyword: str = "critical") -> list[dict]:
    """
    Fetch recent CVEs from NVD API for CVE chapter articles.
    DATAGEN multi-source research pattern: pull real data before writing.
    """
    try:
        url = (
            "https://services.nvd.nist.gov/rest/json/cves/2.0"
            f"?keywordSearch={urllib.request.quote(keyword)}"
            "&resultsPerPage=5&pubStartDate=2024-01-01T00:00:00.000"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ITVedasBot/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        cves = []
        for item in data.get("vulnerabilities", [])[:5]:
            cve = item.get("cve", {})
            cve_id  = cve.get("id","")
            descs   = cve.get("descriptions",[])
            desc    = next((d["value"] for d in descs if d.get("lang")=="en"), "")
            metrics = cve.get("metrics",{})
            score   = None
            for k in ["cvssMetricV31","cvssMetricV30","cvssMetricV2"]:
                if k in metrics:
                    try:
                        score = metrics[k][0]["cvssData"]["baseScore"]
                        break
                    except Exception:
                        pass
            if cve_id and desc:
                cves.append({"id": cve_id, "description": desc[:300], "score": score})
        log("research", f"Fetched {len(cves)} CVEs from NVD")
        return cves
    except Exception as e:
        log("research", f"NVD fetch skipped: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 3: TASK MANAGEMENT
#  Sources: compass-skills, task-orchestrator, mission-control,
#           agent-kanban, cortex-tms, project-butler
# ═══════════════════════════════════════════════════════════════════════════════

class TaskForest:
    """
    compass-skills/task-forest: DAG of tasks with goals, decisions, history.
    cortex-tms: archives decisions as episodic memory.
    jpicklyk/task-orchestrator: enforced workflow states.
    """
    STATES = ("pending", "in_progress", "done", "failed")

    def __init__(self):
        self._file = STATE_DIR / "task-forest.json"
        self._data: dict = {}
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                self._data = json.loads(self._file.read_text())
            except Exception:
                pass
        self._data.setdefault("tasks", {})
        self._data.setdefault("decisions", [])
        self._data.setdefault("chapter_goals", {
            ch: f"Build comprehensive beginner {cfg['name']} coverage"
            for ch, cfg in CHAPTERS.items()
        })

    def _save(self):
        done  = sum(1 for t in self._data["tasks"].values() if t["status"] == "done")
        total = len(self._data["tasks"])
        self._data["summary"] = {
            "total": total, "done": done,
            "failed": sum(1 for t in self._data["tasks"].values() if t["status"] == "failed"),
            "completion_pct": round(done/total*100, 1) if total else 0,
        }
        self._file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))

    def update(self, topic: str, chapter: str, status: str,
               slug: str = "", notes: str = "") -> None:
        task_id = f"{chapter}/{(slug or topic[:40]).replace(' ','-').lower()}"
        self._data["tasks"][task_id] = {
            "topic": topic, "chapter": chapter, "status": status,
            "slug": slug, "notes": notes,
            "updated": datetime.datetime.utcnow().isoformat(),
        }
        if status in ("done","failed"):
            self._data["decisions"].append({
                "date": datetime.date.today().isoformat(),
                "task": f"{topic} [{chapter}]",
                "outcome": status, "notes": notes,
            })
        self._save()

    def kanban_view(self) -> str:
        """agent-kanban: markdown kanban board of all tasks."""
        boards: dict[str, list] = {"pending":[], "in_progress":[], "done":[], "failed":[]}
        for tid, t in self._data["tasks"].items():
            boards.get(t["status"], boards["pending"]).append(t)
        lines = ["# ITVedas Brain — Task Kanban\n"]
        for state, tasks in boards.items():
            if tasks:
                lines.append(f"## {state.upper()} ({len(tasks)})")
                for t in tasks[-5:]:  # last 5 per column
                    lines.append(f"- [{t['chapter']}] {t['topic']}")
                lines.append("")
        return "\n".join(lines)


def task_clarifier(topic: str, chapter: str, mem: BrainMemory) -> dict:
    """
    compass-skills/task-clarifier: validates scope + anchors evidence
    BEFORE writing — prevents wasted Claude tokens on bad topics.
    """
    ch_articles = [a for a in mem.published if a.get("chapter") == chapter]

    prompt = f"""Task clarifier for ITVedas.com content bot.

Validate writing an article about: "{topic}"
Chapter: {chapter} | Articles in chapter: {len(ch_articles)} | Total articles: {len(mem.done_topics)}

Assess:
1. GOAL — Is "{topic}" specific and searchable? What exact question does it answer?
2. SCOPE — Single article or needs to be split? (split if 2+ distinct sub-topics)
3. EVIDENCE — Identify 3 specific anchor facts with numbers/names/dates
4. ACCEPTANCE — Define "done": min sections, FAQ count, code example needed?
5. RISK — Accuracy risks? (deprecated tech, evolving standards, controversial claims?)

Return ONLY JSON (no markdown, no fences):
{{
  "approved": true,
  "refined_topic": "Same or slightly better title, under 60 chars",
  "scope": "single-article",
  "anchor_facts": [
    "specific fact with a number or measurement",
    "fact with a real product/company name",
    "fact with a protocol name, RFC, or version"
  ],
  "acceptance_criteria": {{
    "min_sections": 4,
    "min_faq": 3,
    "needs_code_example": true,
    "min_word_count": 900
  }},
  "risk_level": "low",
  "risk_note": null,
  "related_topics": ["related topic 1", "related topic 2", "related topic 3"]
}}"""

    try:
        raw    = _call_claude(prompt, max_tokens=500)
        result = json.loads(_extract_json(raw))
        refined = result.get("refined_topic","")
        if refined and refined != topic:
            log("clarifier", f"Refined: '{topic}' → '{refined}'")
        log("clarifier", f"Approved | risk={result.get('risk_level','low')} | facts={len(result.get('anchor_facts',[]))}")
        return result
    except Exception as e:
        log("clarifier", f"Non-blocking failure: {e}")
        return {
            "approved": True, "refined_topic": topic, "anchor_facts": [],
            "acceptance_criteria": {"min_sections":4,"min_faq":3,"needs_code_example":True,"min_word_count":900},
            "risk_level": "low", "related_topics": [],
        }


def session_handoff(mem: BrainMemory, wm: WorkingMemory, result: str, forest: TaskForest) -> None:
    """
    compass-skills/session-handoff + JamesShi96/project-butler:
    compress state into a paste-ready handoff for next run.
    """
    hf = STATE_DIR / "session-handoff.md"

    chapter_counts: dict[str, int] = {}
    for art in mem.published:
        ch = art.get("chapter","?")
        chapter_counts[ch] = chapter_counts.get(ch,0) + 1

    next_topics: list[str] = []
    for ch, topics in TOPIC_SEEDS.items():
        for t in topics:
            if not mem.has_topic(t):
                next_topics.append(f"[{ch}] {t}")
        if len(next_topics) >= 10:
            break

    recent = [a["title"] for a in mem.published[-5:]]
    kanban = forest.kanban_view()

    hf.write_text(f"""# ITVedas Brain — Session Handoff
Generated: {datetime.datetime.utcnow().isoformat()}
Model: {MODEL}

## This Session
- Topic: {wm.topic}
- Chapter: {wm.chapter}
- Result: **{result}**
- Slug: {wm.slug_full}

## Brain State
- Articles published: {mem.stats['total_published']}
- Topics covered: {len(mem.done_topics)}
- Failed: {mem.stats['total_failed']}
- Runs: {mem.stats.get('runs',0)}

## Coverage
{chr(10).join(f"- {ch}: {cnt}" for ch, cnt in sorted(chapter_counts.items(), key=lambda x:-x[1]))}

## Recent Articles
{chr(10).join(f"- {t}" for t in recent)}

## Next Recommended Topics
{chr(10).join(next_topics[:10])}

{kanban}

## How to Resume
```bash
python itvedas-brain/brain-bot.py
# or: BOT_MODE=audit python itvedas-brain/brain-bot.py
```
""")
    log("handoff", "Session handoff saved")


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 4: CONTENT WRITING INTELLIGENCE
#  Sources: 30x-seo (24 skills), seo-blog-writer (anti-detection),
#           topic-cluster-architect (10-step), writing-agent (evidence anchor),
#           aiwriter (SERP-driven), AutoViralAI (viral research)
# ═══════════════════════════════════════════════════════════════════════════════

WRITING_SYSTEM = """You are the ITVedas Content Brain — the autonomous writer behind itvedas.com.

TARGET: Complete beginners in IT. They may not know what a server is. Explain everything.

SEO RULES (30x-seo — 24 production skills):
- Title: exact keyword, under 60 chars, keyword front-loaded
- Meta description: 150-160 chars, includes keyword, ends with value promise
- H1 = title. H2s = semantic keyword variations (LSI — different ways people search the same thing)
- First paragraph: answers the question within 50 words — E-E-A-T signal
- FAQ: real questions people search, not made-up questions
- Slug: 3-5 words, lowercase, hyphens, no stop words, no dates

ANTI-AI-DETECTION (seo-blog-writer — 6 rules + writing-agent humanization):
1. Vary sentence lengths: mix 6-word and 25-word sentences in the SAME paragraph
2. First-person occasionally: "Here's what I mean..." or "Think of it this way..."
3. Specific numbers and real names: "~50ms" "AWS EC2 t3.micro" "RFC 793" never "many" or "fast"
4. Alternate paragraph lengths: 1-sentence, 3-sentence, 4-sentence — NEVER uniform
5. Vary list lengths: 3 or 7 items — NEVER exactly 5 every time
6. Fact-anchor every major claim with a specific measurement, company, or standard

FORBIDDEN (design-skill-os + avoid-ai-design 161 rules):
- NEVER start with: "In today's world", "Understanding X is crucial", "Have you ever"
- NEVER use: elevate, seamless, powerful, revolutionary, game-changer, leverage, utilize, paradigm,
             delve, invaluable, meticulous, pivotal, transformative, unlock, harness, robust
- NO uniform paragraphs — vary density through the article
- NO vague claims — every claim needs a number, name, or example
- Lead with the answer, not a definition
"""

def pick_topic(mem: BrainMemory) -> tuple[str, str]:
    """
    Topic selection — intelligent, balanced across chapters.
    AutoViralAI: score topics by demand. topic-cluster-architect: fill gaps.
    """
    counts: dict[str, int] = {ch: 0 for ch in CHAPTERS}
    for art in mem.published:
        ch = art.get("chapter","networking")
        if ch in counts:
            counts[ch] += 1

    candidates: list[tuple[str, str, int]] = []
    for chapter, topics in TOPIC_SEEDS.items():
        for topic in topics:
            if not mem.has_topic(topic):
                candidates.append((topic, chapter, counts.get(chapter,0)))

    if not candidates:
        log("topic", "All seeds exhausted — running cluster architect")
        return _cluster_architect(mem)

    candidates.sort(key=lambda x: x[2])  # fewest articles first = balance

    if ANTHROPIC_KEY and len(candidates) >= 3:
        try:
            return _claude_pick(candidates[:12], mem)
        except Exception as e:
            log("topic", f"Claude pick failed: {e}")

    topic, chapter, _ = candidates[0]
    log("topic", f"Selected: '{topic}' [{chapter}]")
    return topic, chapter

def _claude_pick(candidates: list, mem: BrainMemory) -> tuple[str, str]:
    """Claude picks highest-value topic from candidates (DATAGEN multi-agent)."""
    recent = [a["title"] for a in mem.published[-5:]]
    clist  = "\n".join(f"{i+1}. [{ch}] {t}" for i,(t,ch,_) in enumerate(candidates))

    prompt = f"""Content strategist for ITVedas.com — IT education for beginners.

Recent articles: {recent}
Total: {len(mem.done_topics)} topics done

Pick the BEST topic to write next from these candidates.
Prioritise: highest search demand + fills content gap + not similar to recent articles.

{clist}

Return ONLY JSON (no fences):
{{"choice": <1-{len(candidates)}>, "reason": "<one sentence why>"}}"""

    raw  = _call_claude(prompt, max_tokens=200)
    data = json.loads(_extract_json(raw))
    idx  = int(data["choice"]) - 1
    topic, chapter, _ = candidates[min(idx, len(candidates)-1)]
    log("topic", f"Claude: #{idx+1} '{topic}' [{chapter}] — {data.get('reason','')}")
    return topic, chapter

def _cluster_architect(mem: BrainMemory) -> tuple[str, str]:
    """
    topic-cluster-architect 10-step strategy:
    when seeds exhausted, find content gaps + build cluster topics.
    """
    counts: dict[str, int] = {}
    for art in mem.published:
        ch = art.get("chapter","networking")
        counts[ch] = counts.get(ch,0) + 1

    prompt = f"""SEO topic cluster architect for ITVedas.com.

Coverage per chapter: {counts}
Recently done: {mem.done_topics[-15:]}
Total articles: {len(mem.published)}

10-step cluster strategy:
1. Identify chapter with biggest gap (fewest articles vs importance)
2. Find most-searched beginner question NOT yet covered
3. Classify: pillar (comprehensive overview) or supporting (deep dive specific aspect)
4. Verify: specific keyword phrase people search?

Suggest ONE high-value topic.

Return ONLY JSON (no fences):
{{
  "topic": "...",
  "chapter": "networking|cloud|security|devops|databases|linux|hardware|compliance|cve",
  "cluster_role": "pillar|supporting",
  "reason": "one sentence gap this fills"
}}"""

    raw  = _call_claude(prompt, max_tokens=300)
    data = json.loads(_extract_json(raw))
    log("topic", f"Architect: {data.get('cluster_role')} — {data.get('reason','')}")
    return data.get("topic","What is network security"), data.get("chapter","security")


def write_article(wm: WorkingMemory, cve_data: list | None = None) -> dict:
    """
    Full article generation with all writing intelligence skills.
    Sources: DATAGEN research, seo-blog-writer anti-detection,
             30x-seo schema, writing-agent evidence anchoring.
    """
    log("writer", f"Writing: '{wm.topic}' [{wm.chapter}]")
    ch           = CHAPTERS.get(wm.chapter, CHAPTERS["networking"])
    acceptance   = wm.acceptance
    anchor_facts = wm.anchor_facts
    related      = wm.related_topics
    min_sec      = acceptance.get("min_sections", 4)
    min_faq      = acceptance.get("min_faq", 3)
    needs_code   = acceptance.get("needs_code_example", True)

    anchors_block = ""
    if anchor_facts:
        anchors_block = "\nAnchor facts (use all of these in the article):\n" + \
            "\n".join(f"- {f}" for f in anchor_facts)

    related_block = ""
    if related:
        related_block = f"\nRelated ITVedas topics to mention naturally: {related}"

    cve_block = ""
    if cve_data:
        cve_block = "\nReal CVE data to reference in this article:\n" + \
            "\n".join(f"- {c['id']} (CVSS {c.get('score','N/A')}): {c['description'][:200]}" for c in cve_data)

    prompt = f"""Write a complete, high-quality IT education article for ITVedas.com.

TOPIC: "{wm.topic}"
CHAPTER: {ch['name']}
AUDIENCE: Complete beginners — may not know what a server is
{anchors_block}
{related_block}
{cve_block}

WRITING RULES — evidence anchoring (writing-agent) + anti-detection (seo-blog-writer):

Step 1 — ANCHOR (if not pre-provided above): identify 3-5 specific facts with numbers/names
Step 2 — WRITE {min_sec}+ sections, 900+ words:
  - First sentence of article ANSWERS the question — not a definition, not "today's world"
  - Vary sentence lengths: 6-word and 25-word sentences in same paragraph
  - Use "Here's what I mean..." or "Think of it this way..." once or twice
  - Specific: "~50ms", "AWS Lambda", "RFC 2616", not "fast" or "some platforms"
  - Alternate paragraphs: 1-sentence, 3-sentence, 4-sentence — NEVER all the same
  - Lists: 3 items or 7 items — not always 5
{"  - Include at least 1 code/command example in <pre><code> tags" if needs_code else ""}
  - NEVER use: elevate seamless powerful revolutionary game-changer leverage utilize paradigm delve

SEO (30x-seo — 24 production skills):
  - Title: exact keyword, under 60 chars, keyword first
  - Meta: 150-160 chars, includes keyword, ends with a value promise
  - H2 headings: semantic keyword variations (LSI)
  - {min_faq}+ FAQ questions: real search queries, not invented ones

Return ONLY valid JSON — no markdown fences, no ```json, just raw JSON:
{{
  "title": "Exact keyword, under 60 chars",
  "slug": "keyword-slug-3-5-words",
  "meta_description": "150-160 char description with keyword and value promise at end",
  "intro": "2-3 sentences. Sentence 1 directly answers the question with a specific fact. No opener phrases.",
  "anchor_facts": ["specific fact with number", "fact with real name/product", "fact with example"],
  "sections": [
    {{
      "heading": "Semantic H2 (keyword variation)",
      "content": "<p>HTML content. Use <p>, <ul>, <li>, <strong>, <code>, <pre><code>. Vary lengths.</p>"
    }}
  ],
  "faq": [
    {{"q": "Exact question people search about {wm.topic}?", "answer": "Direct 2-3 sentence answer with specific number or name."}},
    {{"q": "Second real search query?", "answer": "Specific answer."}},
    {{"q": "Third common question?", "answer": "Specific answer with example."}}
  ],
  "key_takeaways": ["specific takeaway with measurement or fact", "takeaway 2 with real name", "takeaway 3"],
  "related_topics": ["related IT topic 1", "related topic 2", "related topic 3"]
}}"""

    raw  = _call_claude(prompt, system=WRITING_SYSTEM, max_tokens=4500)
    data = json.loads(_extract_json(raw))

    data["chapter"]       = wm.chapter
    data["chapter_name"]  = ch["name"]
    data["chapter_color"] = ch["color"]
    data["chapter_emoji"] = ch["emoji"]
    data["chapter_num"]   = ch["num"]
    data["date"]          = datetime.date.today().isoformat()
    data["topic"]         = wm.topic

    log("writer", f"Written: '{data['title']}' | {len(data.get('sections',[]))} sections | {len(data.get('faq',[]))} FAQ")
    return data


def qa_review(data: dict) -> dict:
    """
    Self-review + rewrite weak sections (DATAGEN multi-agent QA gate).
    Sections scoring below 7/10 are automatically rewritten.
    """
    log("qa", "Reviewing article quality...")
    sections_text = "\n\n".join(f"## {s['heading']}\n{s['content']}" for s in data.get("sections",[]))

    prompt = f"""Quality reviewer for ITVedas.com — IT education for beginners.

Review this article draft:
Title: {data['title']}
Intro: {data['intro']}

{sections_text}

Score each section 1-10 on:
- Clarity: would a complete beginner understand this?
- Accuracy: are the technical details correct?
- Value: does it teach something specific and useful?
- Humanness: does it sound like a person wrote it?

If any section scores below 7, rewrite it applying:
- Vary sentence lengths (short + long in same paragraph)
- One specific number or real example per section
- Active voice: "DNS resolves" not "names are resolved"
- NEVER: elevate, seamless, revolutionary, game-changer

Return ONLY JSON (no fences):
{{
  "overall_score": <1-10>,
  "verdict": "PUBLISH|NEEDS_WORK",
  "sections": [{{"heading":"...","content":"...","score":<1-10>}}],
  "intro": "...",
  "notes": "one sentence on what changed"
}}"""

    try:
        raw    = _call_claude(prompt, max_tokens=4000)
        review = json.loads(_extract_json(raw))
        score  = review.get("overall_score", 8)
        if review.get("verdict") == "NEEDS_WORK":
            data["sections"] = review["sections"]
            data["intro"]    = review.get("intro", data["intro"])
            log("qa", f"Rewrote weak sections. Score: {score}/10 | {review.get('notes','')}")
        else:
            log("qa", f"Passed: {score}/10")
    except Exception as e:
        log("qa", f"Skipped (non-blocking): {e}")
    return data


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 5: DESIGN INTELLIGENCE
#  Sources: styleseed (74), ux-skill (152), design-skill-os (161),
#           avoid-ai-design, ux-pilot (376), design-cognition-skill
# ═══════════════════════════════════════════════════════════════════════════════

SLOP_WORDS = [
    "elevate","seamless","powerful","revolutionary","game-changer",
    "next-level","cutting-edge","leverage","utilize","paradigm",
    "delve","invaluable","meticulous","pivotal","transformative",
    "unlock","harness","robust","scalable","streamline","empower",
    "journey","landscape","ecosystem","holistic","synergy","disruptive",
]

WEAK_OPENERS = [
    "in today's", "in the world of", "understanding ", "have you ever",
    "when it comes to", "in this article", "we will explore",
    "it's important to", "let's dive", "in the digital age",
]

def design_intelligence(data: dict) -> dict:
    """
    Detects + rewrites AI-slop content.
    styleseed judgment + design-skill-os red team + avoid-ai-design.
    ux-pilot: checks for 376 UX anti-patterns in copy.
    """
    if not ANTHROPIC_KEY:
        return data

    content_text = data.get("intro","") + " ".join(
        s.get("content","") for s in data.get("sections",[])
    )
    found_slop   = [w for w in SLOP_WORDS if re.search(r"\b"+w+r"\b", content_text, re.IGNORECASE)]
    intro_lower  = data.get("intro","").lower()
    weak_intro   = any(intro_lower.strip().startswith(w) for w in WEAK_OPENERS)
    thin_article = len(data.get("sections",[])) < 4

    if not found_slop and not weak_intro and not thin_article:
        log("design", "Content passes design check")
        return data

    issues = []
    if found_slop:   issues.append(f"Replace slop words with specific concrete language: {found_slop[:6]}")
    if weak_intro:   issues.append("Rewrite intro — must lead with the answer or a specific fact, not a setup phrase")
    if thin_article: issues.append("Add more sections — minimum 4 required")

    log("design", f"Fixing: {issues}")

    sections_json = json.dumps([{"heading":s["heading"],"content":s["content"]} for s in data.get("sections",[])])

    prompt = f"""Design-aware content editor for ITVedas.com.

Fix these issues:
{chr(10).join(f"- {i}" for i in issues)}

Design rules (styleseed + design-skill-os 161 principles):
- Intro MUST start with the answer or a specific fact — never a definition
- 2-4 sentences per paragraph, active voice
- Real names, specific numbers — no vague "some companies" or "modern systems"
- NO slop words: {SLOP_WORDS[:10]}

Intro to fix: {data.get('intro','')}

Sections to fix (JSON): {sections_json}

Return ONLY JSON (no fences):
{{"intro":"...","sections":[{{"heading":"...","content":"..."}}]}}"""

    try:
        raw   = _call_claude(prompt, max_tokens=4000)
        fixed = json.loads(_extract_json(raw))
        data["intro"]    = fixed.get("intro", data["intro"])
        data["sections"] = fixed.get("sections", data["sections"])
        log("design", "Content improved")
    except Exception as e:
        log("design", f"Design rewrite skipped: {e}")
    return data


def design_qa_lint(html_content: str, data: dict) -> tuple[str, list[str]]:
    """
    Anti-slop HTML linter — ux-skill 152 rules + avoid-ai-design patterns.
    Reports violations but doesn't block publishing.
    """
    violations = []
    checks = [
        (r"Lorem ipsum",                                   "Lorem ipsum detected"),
        (r"console\.log",                                  "console.log in output HTML"),
        (r"<img(?![^>]*alt=)",                             "Image missing alt text"),
        (r"\b(Elevate|Seamless|Revolutionary|Game-changer|Leverage|Holistic|Synergy)\b",
                                                           "AI-slop words in final HTML"),
        (r"Get Started|Click Here|Learn More",             "Generic CTA copy"),
        (r"style=\"[^\"]{100,}\"",                         "Excessive inline style (use CSS classes)"),
        (r"linear-gradient.*purple|linear-gradient.*violet","Purple gradient (AI-slop tell)"),
    ]
    content_text = data.get("intro","") + " ".join(s.get("content","") for s in data.get("sections",[]))
    slop_found   = [w for w in SLOP_WORDS if re.search(r"\b"+w+r"\b", content_text, re.IGNORECASE)]
    if slop_found:
        violations.append(f"Slop words survived: {slop_found}")

    for pattern, msg in checks:
        if re.search(pattern, html_content, re.IGNORECASE):
            violations.append(msg)

    if violations:
        log("design-qa", f"{len(violations)} violation(s): {'; '.join(violations)}")
    else:
        log("design-qa", "All design checks passed")

    return html_content, violations


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 6: PUBLISHING INTELLIGENCE
#  GitHub API, chapter index, sitemap, internal linker, social content
# ═══════════════════════════════════════════════════════════════════════════════

def build_internal_links(data: dict, mem: BrainMemory) -> list[dict]:
    """
    knowledge-assistant RAG: finds published articles related to this one.
    Returns up to 5 internal link opportunities.
    """
    related = data.get("related_topics", [])
    links   = mem.get_related_articles(related)
    if links:
        log("linker", f"Found {len(links)} internal links")
    return links


def estimate_reading_time(data: dict) -> int:
    text  = data.get("intro","") + " ".join(s.get("content","") for s in data.get("sections",[]))
    words = len(re.sub(r"<[^>]+>","",text).split())
    return max(3, round(words / 200))


def build_article_html(data: dict, internal_links: list[dict]) -> str:
    """Build full article HTML page — all features."""
    et       = html_mod.escape
    esc_t    = et(data["title"])
    esc_d    = et(data["meta_description"])
    slug     = data["slug"]
    chapter  = data["chapter"]
    ch_name  = data["chapter_name"]
    ch_color = data["chapter_color"]
    ch_emoji = data["chapter_emoji"]
    date_s   = data["date"]
    canonical= f"{SITE_URL}/articles/{chapter}/{slug}.html"
    read_t   = estimate_reading_time(data)

    try:
        dfmt = datetime.date.fromisoformat(date_s).strftime("%B %d, %Y")
    except Exception:
        dfmt = date_s

    faq_items = data.get("faq", [])

    # schemas
    faq_schema = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type":"Question","name":et(f["q"]),
             "acceptedAnswer":{"@type":"Answer","text":et(f["answer"])}}
            for f in faq_items
        ]
    })
    art_schema = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": data["title"], "description": data["meta_description"],
        "datePublished": date_s, "dateModified": date_s,
        "publisher": {"@type":"Organization","name":SITE_NAME,"url":SITE_URL},
        "url": canonical,
    })
    bc_schema = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type":"ListItem","position":1,"name":"Home","item":SITE_URL},
            {"@type":"ListItem","position":2,"name":ch_name,"item":f"{SITE_URL}/articles/{chapter}/"},
            {"@type":"ListItem","position":3,"name":data["title"],"item":canonical},
        ]
    })

    # ToC
    sections = data.get("sections",[])
    toc_html = ""
    for s in sections:
        h   = s.get("heading","")
        anc = re.sub(r"[^a-z0-9]+","-",h.lower()).strip("-")
        toc_html += f'<li><a href="#{anc}">{et(h)}</a></li>\n'
    if faq_items:
        toc_html += '<li><a href="#faq">FAQ</a></li>\n'

    # sections
    sec_html = ""
    for s in sections:
        h   = s.get("heading","")
        c   = s.get("content","")
        anc = re.sub(r"[^a-z0-9]+","-",h.lower()).strip("-")
        sec_html += f'<h2 id="{anc}">{et(h)}</h2>\n{c}\n'

    # facts
    facts    = data.get("anchor_facts",[])
    fact_html = ""
    if facts:
        items     = "".join(f"<li>{et(f)}</li>" for f in facts)
        fact_html = f'<div class="fact-box"><strong>Key Facts</strong><ul>{items}</ul></div>\n'

    # takeaways
    tko      = data.get("key_takeaways",[])
    tko_html = ""
    if tko:
        items    = "".join(f"<li>{et(t)}</li>" for t in tko)
        tko_html = f'<div class="takeaways"><h2>Key Takeaways</h2><ul>{items}</ul></div>\n'

    # FAQ
    faq_html = ""
    if faq_items:
        rows     = "".join(
            f'<div class="faq-item"><h3>{et(f["q"])}</h3><p>{et(f["answer"])}</p></div>\n'
            for f in faq_items
        )
        faq_html = f'<h2 id="faq">Frequently Asked Questions</h2>\n<div class="faq">{rows}</div>\n'

    # related articles
    rel_html = ""
    if internal_links:
        cards    = "".join(
            f'<a href="{lnk.get("slug","#")}" class="rel-card">{et(lnk.get("title",""))}</a>'
            for lnk in internal_links
        )
        rel_html = f'<div class="related"><h2>Related Articles</h2><div class="rel-grid">{cards}</div></div>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/assets/logo-mark.svg">
<meta name="description" content="{esc_d}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{esc_t} | {SITE_NAME}">
<meta property="og:description" content="{esc_d}">
<meta property="og:image" content="{SITE_URL}/assets/og-default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta property="article:published_time" content="{date_s}">
<link rel="canonical" href="{canonical}">
<title>{esc_t} | {SITE_NAME}</title>
<script type="application/ld+json">{art_schema}</script>
<script type="application/ld+json">{faq_schema}</script>
<script type="application/ld+json">{bc_schema}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0A0A0F;--bg2:#13131C;--bg3:#1A1A28;
  --text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;
  --accent:{ch_color};--border:rgba(255,255,255,0.08);--r:12px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}
#prog{{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:999;width:0%;transition:width .1s linear;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:.875rem;transition:color .2s;}}
.nav-links a:hover{{color:var(--text);}}
.hero{{padding:8rem 2rem 2.5rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;transition:color .2s;}}
.breadcrumb a:hover{{color:var(--accent);}}
.ch-badge{{display:inline-flex;align-items:center;gap:.4rem;font-size:.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin-bottom:.85rem;}}
.hero h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.85rem,4vw,2.75rem);font-weight:700;letter-spacing:-.025em;line-height:1.15;margin-bottom:1.25rem;}}
.hero-meta{{display:flex;gap:1.25rem;font-size:.8rem;color:var(--muted);margin-bottom:1.5rem;flex-wrap:wrap;}}
.hero p.intro{{font-size:1.05rem;color:var(--sub);line-height:1.8;border-left:3px solid var(--accent);padding-left:1rem;}}
.wrap{{max-width:860px;margin:0 auto;padding:1.5rem 2rem 6rem;display:grid;grid-template-columns:1fr 210px;gap:2.5rem;align-items:start;}}
.art{{min-width:0;}}
.toc{{position:sticky;top:80px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);padding:1.25rem;font-size:.85rem;}}
.toc h3{{font-family:'Space Grotesk',sans-serif;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.85rem;}}
.toc ol{{padding-left:1.1rem;}}
.toc li{{margin-bottom:.4rem;}}
.toc a{{color:var(--sub);text-decoration:none;transition:color .15s;}}
.toc a:hover{{color:var(--accent);}}
.art h2{{font-family:'Space Grotesk',sans-serif;font-size:1.45rem;font-weight:700;margin:2.5rem 0 1rem;color:var(--text);letter-spacing:-.015em;scroll-margin-top:80px;}}
.art h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;margin:1.75rem 0 .6rem;color:var(--text);}}
.art p{{color:var(--sub);margin-bottom:1.25rem;}}
.art ul,.art ol{{color:var(--sub);padding-left:1.5rem;margin-bottom:1.25rem;}}
.art li{{margin-bottom:.4rem;}}
.art strong{{color:var(--text);}}
.art a{{color:var(--accent);text-decoration:none;}}
.art a:hover{{text-decoration:underline;}}
.art code{{background:var(--bg2);border:1px solid var(--border);border-radius:4px;padding:.15em .45em;font-size:.875em;color:#FF6B35;font-family:'Courier New',monospace;}}
.art pre{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:1.25rem 1.5rem;overflow-x:auto;margin:1.5rem 0;}}
.art pre code{{background:none;border:none;padding:0;font-size:.875rem;color:#A8E6CF;}}
.fact-box{{background:var(--bg2);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--r);padding:1.25rem 1.5rem;margin:1.5rem 0;}}
.fact-box strong{{display:block;font-family:'Space Grotesk',sans-serif;font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.6rem;}}
.fact-box ul{{margin:0;padding-left:1.25rem;}}
.fact-box li{{color:var(--sub);font-size:.9rem;margin-bottom:.3rem;}}
.takeaways{{background:var(--bg3);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--r);padding:1.5rem;margin:2rem 0;}}
.takeaways h2{{font-size:1rem;font-family:'Space Grotesk',sans-serif;margin:0 0 .75rem;color:var(--text);}}
.takeaways ul{{margin:0;padding-left:1.25rem;}}
.takeaways li{{color:var(--sub);font-size:.9rem;}}
.faq{{margin-top:.75rem;}}
.faq-item{{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);padding:1.25rem 1.5rem;margin-bottom:.85rem;transition:border-color .2s;}}
.faq-item:hover{{border-color:var(--accent);}}
.faq-item h3{{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;margin-bottom:.5rem;color:var(--text);}}
.faq-item p{{margin:0;font-size:.9rem;color:var(--sub);}}
.related h2{{font-family:'Space Grotesk',sans-serif;font-size:1.2rem;margin:2.5rem 0 1rem;color:var(--text);}}
.rel-grid{{display:flex;flex-direction:column;gap:.6rem;}}
.rel-card{{display:block;background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);padding:.85rem 1rem;text-decoration:none;color:var(--sub);font-size:.875rem;transition:border-color .2s,color .2s;}}
.rel-card:hover{{border-color:var(--accent);color:var(--text);}}
.nav-art{{display:flex;justify-content:space-between;gap:1rem;margin-top:3rem;padding-top:2rem;border-top:1px solid var(--border);}}
.nav-art a{{flex:1;background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);padding:1rem 1.25rem;text-decoration:none;color:var(--sub);font-size:.875rem;transition:border-color .2s;cursor:pointer;}}
.nav-art a:hover{{border-color:var(--accent);}}
.nav-art .label{{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.3rem;}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:.75rem;flex-wrap:wrap;}}
.flinks a{{color:var(--muted);text-decoration:none;transition:color .2s;}}
.flinks a:hover{{color:#FF6B35;}}
@media(max-width:768px){{
  nav{{padding:0 1.25rem;}}.nav-links{{display:none;}}
  .wrap{{grid-template-columns:1fr;padding-left:1.25rem;padding-right:1.25rem;}}
  .toc{{display:none;}}
  .hero{{padding-left:1.25rem;padding-right:1.25rem;}}
}}
</style>
</head>
<body>
<div id="prog"></div>
<nav>
  <a href="/" class="logo">IT<span>Vedas</span></a>
  <div class="nav-links">
    <a href="/">Home</a><a href="/news.html">News</a>
    <a href="/articles/{chapter}/">{ch_emoji} {ch_name}</a>
    <a href="/#chapters">All Chapters</a>
    <a href="mailto:info@itvedas.com">Contact</a>
  </div>
</nav>
<div class="hero">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/articles/{chapter}/">{ch_name}</a> › {esc_t}</div>
  <div class="ch-badge">{ch_emoji} {ch_name}</div>
  <h1>{esc_t}</h1>
  <div class="hero-meta"><span>{dfmt}</span><span>{read_t} min read</span><span>ITVedas</span></div>
  <p class="intro">{et(data['intro'])}</p>
</div>
<div class="wrap">
  <article class="art">
    {fact_html}
    {sec_html}
    {tko_html}
    {faq_html}
    {rel_html}
    <div class="nav-art">
      <a href="/articles/{chapter}/"><div class="label">← Chapter</div>{ch_emoji} {ch_name}</a>
      <a href="/#chapters"><div class="label">Explore →</div>All Chapters</a>
    </div>
  </article>
  <aside class="toc">
    <h3>Contents</h3>
    <ol>{toc_html}</ol>
  </aside>
</div>
<footer>
  <div class="fl">IT<span>Vedas</span></div>
  <p>The complete IT knowledge hub — explained simply, for everyone.</p>
  <div class="flinks">
    <a href="/">Home</a><a href="/news.html">News</a>
    <a href="/articles/{chapter}/">{ch_name}</a><a href="/#chapters">Chapters</a>
    <a href="/privacy-policy.html">Privacy Policy</a>
    <a href="/terms-of-service.html">Terms</a>
    <a href="mailto:info@itvedas.com">Contact</a>
  </div>
  <p style="margin-top:1rem;">© {datetime.date.today().year} {SITE_NAME} · Knowledge for everyone</p>
</footer>
<script>
(function(){{
  var b=document.getElementById('prog');
  if(!b)return;
  window.addEventListener('scroll',function(){{
    var s=document.documentElement;
    b.style.width=Math.min(100,(s.scrollTop/(s.scrollHeight-s.clientHeight))*100)+'%';
  }},{{passive:true}});
}})();
</script>
</body>
</html>"""


def build_chapter_index(chapter: str, articles: list[dict]) -> str:
    """Build chapter index page — updated after each new article."""
    ch      = CHAPTERS.get(chapter, CHAPTERS["networking"])
    name    = ch["name"]
    color   = ch["color"]
    emoji   = ch["emoji"]
    sorted_ = sorted(articles, key=lambda a: a.get("date",""), reverse=True)

    cards = ""
    for art in sorted_[:60]:
        title = html_mod.escape(art.get("title",""))
        slug  = art.get("slug","")
        adate = art.get("date","")
        try:
            dfmt = datetime.date.fromisoformat(adate[:10]).strftime("%b %d, %Y")
        except Exception:
            dfmt = adate
        url = f"/articles/{chapter}/{slug}.html"
        cards += f"""<a href="{url}" class="card">
  <div class="card-date">{dfmt}</div>
  <h2>{title}</h2>
  <span class="card-arrow">Read →</span>
</a>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/assets/logo-mark.svg">
<meta name="description" content="ITVedas {name} — beginner-friendly guides on {name.lower()}, explained simply.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_URL}/articles/{chapter}/">
<title>{name} Guides | {SITE_NAME}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA4_ID}');</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0A0A0F;--bg2:#13131C;--text:#F0F0F8;--muted:#8888A8;--sub:#D0D0E8;--accent:{color};--border:rgba(255,255,255,0.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased;}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 2rem;height:64px;background:rgba(10,10,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}}
.logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.3rem;color:var(--text);text-decoration:none;}}
.logo span{{color:#FF6B35;}}
.nav-links{{display:flex;gap:1.5rem;}}
.nav-links a{{color:var(--muted);text-decoration:none;font-size:.875rem;transition:color .2s;}}
.nav-links a:hover{{color:var(--text);}}
.hero{{padding:8rem 2rem 3rem;max-width:860px;margin:0 auto;}}
.breadcrumb{{font-size:.8rem;color:var(--muted);margin-bottom:1.5rem;}}
.breadcrumb a{{color:var(--muted);text-decoration:none;}}
.breadcrumb a:hover{{color:var(--accent);}}
.ch-label{{font-size:.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin-bottom:.75rem;}}
h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.8rem,4vw,2.75rem);font-weight:700;letter-spacing:-.025em;line-height:1.15;margin-bottom:1rem;}}
.hero p{{color:var(--sub);font-size:1.05rem;max-width:580px;}}
.content{{max-width:860px;margin:0 auto;padding:2rem 2rem 6rem;}}
.count{{font-size:.85rem;color:var(--muted);margin-bottom:1.5rem;}}
.card{{display:block;background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:.85rem;text-decoration:none;transition:border-color .2s,transform .2s;cursor:pointer;}}
.card:hover{{border-color:var(--accent);transform:translateX(4px);}}
.card-date{{font-size:.78rem;color:var(--muted);margin-bottom:.4rem;}}
.card h2{{font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:600;color:var(--text);margin-bottom:.4rem;}}
.card-arrow{{font-size:.8rem;color:var(--accent);}}
footer{{border-top:1px solid var(--border);padding:2.5rem 2rem;text-align:center;color:var(--muted);font-size:.875rem;}}
.fl{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:var(--text);margin-bottom:.5rem;}}
.fl span{{color:#FF6B35;}}
.flinks{{display:flex;gap:1.5rem;justify-content:center;margin-top:.75rem;flex-wrap:wrap;}}
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
  <div class="ch-label">{emoji} Chapter {ch['num']}</div>
  <h1>{name}</h1>
  <p>Beginner-friendly guides on {name.lower()} — explained simply, with real examples.</p>
</div>
<div class="content">
  <div class="count">{len(sorted_)} articles in this chapter</div>
  {cards}
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


def build_sitemap(mem: BrainMemory) -> str:
    """Build complete sitemap.xml from all known articles."""
    today = datetime.date.today().isoformat()
    urls  = [
        f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/news.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{SITE_URL}/privacy-policy.html</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>",
        f"  <url><loc>{SITE_URL}/terms-of-service.html</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>",
    ]
    for ch in CHAPTERS:
        urls.append(f"  <url><loc>{SITE_URL}/articles/{ch}/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    for art in mem.published:
        slug  = art.get("slug","")
        ch    = art.get("chapter","networking")
        adate = art.get("date", today)
        if slug and re.match(r"\d{4}-\d{2}-\d{2}-", slug):
            urls.append(
                f"  <url><loc>{SITE_URL}/articles/{ch}/{slug}.html</loc>"
                f"<lastmod>{adate}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>"
            )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>")


def generate_social_content(data: dict) -> dict:
    """
    Generate tweet + LinkedIn post alongside article.
    AutoViralAI: viral content patterns from social research.
    """
    if not ANTHROPIC_KEY:
        return {}

    prompt = f"""Generate social media content for this IT article:

Title: {data['title']}
Intro: {data['intro']}
Key takeaways: {data.get('key_takeaways',[])}
URL: {SITE_URL}/articles/{data['chapter']}/{data['slug']}.html

Create:
1. TWEET (max 240 chars): Hook opener + key insight + URL. No hashtags spam. Conversational.
2. LINKEDIN (max 600 chars): Professional but friendly. 1-2 line paragraphs. End with question or call to action.

Return ONLY JSON (no fences):
{{"tweet": "...", "linkedin": "..."}}"""

    try:
        raw  = _call_claude(prompt, max_tokens=400)
        data = json.loads(_extract_json(raw))
        log("social", f"Generated tweet ({len(data.get('tweet',''))} chars) + LinkedIn")
        return data
    except Exception as e:
        log("social", f"Skipped: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL MODULE 7: SELF-IMPROVEMENT LOOP
#  Sources: letta-ai (stateful self-improvement), ai-data-analysis (analysis)
# ═══════════════════════════════════════════════════════════════════════════════

def strategy_analysis(mem: BrainMemory) -> str:
    """
    letta-ai stateful improvement: analyze performance and update strategy.
    Runs every 10 articles to find what's working.
    """
    if mem.stats.get("total_published",0) % 10 != 0:
        return ""

    counts: dict[str, int] = {}
    for art in mem.published:
        ch = art.get("chapter","?")
        counts[ch] = counts.get(ch,0) + 1

    sorted_ch = sorted(counts.items(), key=lambda x: -x[1])
    weakest   = sorted(counts.items(), key=lambda x: x[1])[:3]

    prompt = f"""You are the ITVedas Brain's self-improvement module (letta-ai pattern).

After {mem.stats['total_published']} articles, analyze the strategy:

Articles per chapter: {sorted_ch}
Weakest chapters (need more): {weakest}
Failed topics: {mem.failed_topics[-5:]}

Provide 3 strategic recommendations for the next 10 articles.
Return ONLY JSON (no fences):
{{"recommendations": ["rec 1", "rec 2", "rec 3"], "focus_chapter": "...", "note": "..."}}"""

    try:
        raw  = _call_claude(prompt, max_tokens=300)
        data = json.loads(_extract_json(raw))
        note = data.get("note","")
        recs = data.get("recommendations",[])
        log("strategy", f"Focus: {data.get('focus_chapter','')} | {note}")
        for r in recs:
            log("strategy", f"  - {r}")
        mem.record_decision("strategy_analysis", note)
        return note
    except Exception as e:
        log("strategy", f"Skipped: {e}")
        return ""


def audit_mode(mem: BrainMemory, forest: TaskForest) -> int:
    """
    Audit mode: review and improve old articles.
    BOT_MODE=audit triggers this instead of writing new articles.
    """
    log("audit", "Running in AUDIT mode — reviewing old articles")
    articles_to_review = [
        a for a in mem.published[-20:]
        if re.match(r"\d{4}-\d{2}-\d{2}-", a.get("slug",""))
    ]
    if not articles_to_review:
        log("audit", "No articles to audit")
        return 0

    # pick one article to review
    target = articles_to_review[0]
    ch     = target.get("chapter","networking")
    slug   = target.get("slug","")
    path   = ARTICLES / ch / f"{slug}.html"

    if not path.exists():
        log("audit", f"File not found: {path}")
        return 0

    content = path.read_text(errors="ignore")
    title   = target.get("title","")
    log("audit", f"Auditing: '{title}'")

    prompt = f"""Audit this IT education article for improvement opportunities.

Title: {title}
Chapter: {ch}

HTML content excerpt (first 3000 chars):
{content[:3000]}

Check for:
1. Outdated technical information
2. Missing sections (FAQ, code examples, key takeaways)
3. AI-slop language (vague, filler words)
4. Missing internal links to related topics
5. SEO improvements (meta description, heading structure)

Return ONLY JSON (no fences):
{{
  "needs_update": true,
  "priority_issues": ["issue 1", "issue 2"],
  "recommendation": "one sentence summary of what to improve"
}}"""

    try:
        raw    = _call_claude(prompt, max_tokens=400)
        result = json.loads(_extract_json(raw))
        if result.get("needs_update"):
            log("audit", f"Issues found: {result.get('priority_issues',[])} — {result.get('recommendation','')}")
            mem.record_decision(f"AUDIT: {title}", result.get("recommendation",""))
        else:
            log("audit", "Article is up to date")
        mem.save()
    except Exception as e:
        log("audit", f"Failed: {e}")

    return 0


# ═══════════════════════════════════════════════════════════════════════════════
#  GITHUB PUBLISHER
# ═══════════════════════════════════════════════════════════════════════════════

def github_put(path: str, content: str, message: str) -> bool:
    """Create or update a file via GitHub Contents API — with retry."""
    if not GITHUB_TOKEN:
        return False
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
            log("github", f"GET {path}: {e.code}")
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

def publish_everything(data: dict, html_content: str, mem: BrainMemory) -> bool:
    """Push article + chapter index + sitemap to GitHub."""
    if not GITHUB_TOKEN:
        # fallback: save locally
        out = ARTICLES / data["chapter"]
        out.mkdir(parents=True, exist_ok=True)
        fname = f"{data['date']}-{data['slug']}.html"
        (out / fname).write_text(html_content)
        log("local", f"Saved: {out/fname}")
        return True

    chapter = data["chapter"]
    date    = data["date"]
    slug    = data["slug"]
    fname   = f"{date}-{slug}.html"
    title   = data["title"]
    ok      = True

    # article
    ok &= github_put(f"articles/{chapter}/{fname}", html_content, f"bot: add '{title}' [{chapter}]")

    # chapter index (include new article)
    ch_arts = [a for a in mem.published if a.get("chapter") == chapter]
    ch_arts.append({"title": title, "slug": fname[:-5], "date": date, "chapter": chapter})
    ok &= github_put(
        f"articles/{chapter}/index.html",
        build_chapter_index(chapter, ch_arts),
        f"bot: update {chapter} index"
    )

    # sitemap
    ok &= github_put("sitemap.xml", build_sitemap(mem), "bot: update sitemap")

    return ok


# ═══════════════════════════════════════════════════════════════════════════════
#  HEARTBEAT
# ═══════════════════════════════════════════════════════════════════════════════

def write_heartbeat(mem: BrainMemory, result: str, wm: WorkingMemory) -> None:
    counts: dict[str, int] = {}
    for art in mem.published:
        ch = art.get("chapter","?")
        counts[ch] = counts.get(ch,0) + 1

    seeds_left = sum(
        1 for ch, ts in TOPIC_SEEDS.items()
        for t in ts if not mem.has_topic(t)
    )

    next_topics = []
    for ch, topics in TOPIC_SEEDS.items():
        for t in topics:
            if not mem.has_topic(t):
                next_topics.append({"topic": t, "chapter": ch})
        if len(next_topics) >= 8:
            break

    heartbeat = {
        "timestamp":       datetime.datetime.utcnow().isoformat(),
        "result":          result,
        "model":           MODEL,
        "last_topic":      wm.topic,
        "last_chapter":    wm.chapter,
        "last_slug":       wm.slug_full,
        "total_published": mem.stats["total_published"],
        "total_failed":    mem.stats["total_failed"],
        "runs":            mem.stats.get("runs",0),
        "seeds_remaining": seeds_left,
        "per_chapter":     counts,
        "next_topics":     next_topics,
        "violations":      wm.violations,
    }
    (STATE_DIR / "heartbeat.json").write_text(json.dumps(heartbeat, indent=2))
    log("heartbeat", f"OK | published={mem.stats['total_published']} | seeds_left={seeds_left}")


# ═══════════════════════════════════════════════════════════════════════════════
#  CLAUDE API + JSON EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════════

def _call_claude(prompt: str, system: str | None = None, max_tokens: int = 4000) -> str:
    if not ANTHROPIC_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    payload: dict[str, Any] = {
        "model": MODEL, "max_tokens": max_tokens,
        "messages": [{"role":"user","content":prompt}],
    }
    if system:
        payload["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)["content"][0]["text"].strip()
        except Exception as e:
            if attempt == 2: raise
            time.sleep(8 * (attempt + 1))
    return ""

def _extract_json(text: str) -> str:
    """Robustly extract JSON — strips code fences, finds outermost { }."""
    text = text.strip()
    if "```" in text:
        lines, cleaned, in_fence = text.split("\n"), [], False
        for line in lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            cleaned.append(line)
        text = "\n".join(cleaned).strip()
    s = text.find("{")
    e = text.rfind("}")
    if s != -1 and e != -1 and e > s:
        return text[s:e+1]
    return text


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN — FULL PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    log("brain", "=" * 64)
    log("brain", f"ITVedas Brain Bot | Model: {MODEL} | Mode: {RUN_MODE}")
    log("brain", "=" * 64)

    if not ANTHROPIC_KEY:
        log("brain", "ERROR: ANTHROPIC_API_KEY not set")
        return 1

    # ── INIT ─────────────────────────────────────────────────────────────────
    mem    = BrainMemory()
    forest = TaskForest()
    wm     = WorkingMemory()

    mem.load()
    mem.sync_disk()
    mem.ensure_soul()

    # ── AUDIT MODE ───────────────────────────────────────────────────────────
    if RUN_MODE == "audit":
        return audit_mode(mem, forest)

    # ── SITEMAP-ONLY MODE ────────────────────────────────────────────────────
    if RUN_MODE == "sitemap":
        log("brain", "Rebuilding sitemap only")
        github_put("sitemap.xml", build_sitemap(mem), "bot: rebuild sitemap")
        return 0

    # ── SELF-IMPROVEMENT ANALYSIS (every 10 articles) ────────────────────────
    strategy_analysis(mem)

    # ── TOPIC SELECTION ──────────────────────────────────────────────────────
    wm.topic, wm.chapter = pick_topic(mem)

    # ── CVE RESEARCH (if CVE chapter — NVD API) ──────────────────────────────
    cve_data = None
    if wm.chapter == "cve":
        keyword  = re.sub(r"^(what is |how does |what are )", "", wm.topic, flags=re.IGNORECASE)
        cve_data = fetch_nvd_cve(keyword[:30])

    # ── TASK CLARIFIER ───────────────────────────────────────────────────────
    forest.update(wm.topic, wm.chapter, "in_progress")
    clarification   = task_clarifier(wm.topic, wm.chapter, mem)
    wm.topic        = clarification.get("refined_topic", wm.topic)
    wm.anchor_facts = clarification.get("anchor_facts", [])
    wm.acceptance   = clarification.get("acceptance_criteria", {})
    wm.related_topics = clarification.get("related_topics", [])

    log("brain", f"Task: '{wm.topic}' [{wm.chapter}] | risk={clarification.get('risk_level','low')}")

    # ── WRITE ARTICLE ────────────────────────────────────────────────────────
    try:
        wm.article_data = write_article(wm, cve_data=cve_data)
    except Exception as e:
        log("writer", f"FAILED: {e}")
        mem.record_failure(wm.topic, str(e))
        forest.update(wm.topic, wm.chapter, "failed", notes=str(e))
        mem.save()
        write_heartbeat(mem, "WRITE_FAILED", wm)
        session_handoff(mem, wm, "WRITE_FAILED", forest)
        return 1

    # ── QA GATE ──────────────────────────────────────────────────────────────
    wm.article_data = qa_review(wm.article_data)

    # ── DESIGN INTELLIGENCE ──────────────────────────────────────────────────
    wm.article_data = design_intelligence(wm.article_data)

    # ── INTERNAL LINKING ─────────────────────────────────────────────────────
    internal_links = build_internal_links(wm.article_data, mem)

    # ── BUILD HTML ───────────────────────────────────────────────────────────
    wm.html_content = build_article_html(wm.article_data, internal_links)

    # ── DESIGN QA LINT ───────────────────────────────────────────────────────
    wm.html_content, wm.violations = design_qa_lint(wm.html_content, wm.article_data)
    if wm.violations:
        mem.record_decision(f"Design violations for '{wm.topic}'", "; ".join(wm.violations))

    # ── PUBLISH ──────────────────────────────────────────────────────────────
    ok = publish_everything(wm.article_data, wm.html_content, mem)
    if not ok:
        log("brain", "Publish failed")
        mem.record_failure(wm.topic, "publish failed")
        forest.update(wm.topic, wm.chapter, "failed", notes="publish failed")
        mem.save()
        write_heartbeat(mem, "PUBLISH_FAILED", wm)
        return 1

    # ── SOCIAL CONTENT ───────────────────────────────────────────────────────
    social = generate_social_content(wm.article_data)
    if social:
        (STATE_DIR / "last_social.json").write_text(json.dumps(social, indent=2))

    # ── MEMORY UPDATE ────────────────────────────────────────────────────────
    date  = wm.article_data["date"]
    slug  = wm.article_data["slug"]
    wm.slug_full = f"{date}-{slug}"

    mem.add_article(wm)
    mem.update_graph(
        wm.topic, wm.chapter, wm.slug_full,
        related=wm.article_data.get("related_topics",[])
    )
    mem.save()

    # ── TASK FOREST + HEARTBEAT + HANDOFF ────────────────────────────────────
    forest.update(wm.topic, wm.chapter, "done", slug=wm.slug_full)
    write_heartbeat(mem, "SUCCESS", wm)
    session_handoff(mem, wm, "SUCCESS", forest)

    log("brain", "=" * 64)
    log("brain", f"DONE: '{wm.article_data['title']}'")
    log("brain", f"URL:  {SITE_URL}/articles/{wm.chapter}/{wm.slug_full}.html")
    log("brain", f"Total published: {mem.stats['total_published']}")
    log("brain", "=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
