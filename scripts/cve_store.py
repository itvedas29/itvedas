#!/usr/bin/env python3
"""Single source of truth for reading/writing the canonical CVE database.

Why this exists
---------------
* Storage: the master DB used to be a 40+ MB pretty-printed JSON file that
  bots rewrote and committed every day, so git history grew by tens of MB per
  sync. It is now stored gzipped (~5-6 MB) at cve-database-full.json.gz.
  load_db() still reads the legacy cve-database-full.json if it is the only
  copy, and save_db() removes it, so the first sync migrates automatically.
* Severity: a CVE with no CVSS score yet (NVD "awaiting analysis") used to be
  labelled "Low" because 0.0 < 4.0. It is now "Unscored".
* Type: older ingestion defaulted every record to "Remote Code Execution".
  classify_type() derives the type from CWE ids and the description, and
  repair_record() fixes legacy records on load.
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_GZ = ROOT / "cve-database-full.json.gz"
DB_LEGACY = ROOT / "cve-database-full.json"

SEVERITIES = ("Critical", "High", "Medium", "Low", "Unscored")

# Types the old pipeline assigned by default rather than from evidence.
_DEFAULT_TYPES = {"Remote Code Execution", "Security Vulnerability", "", None}


# ── storage ──────────────────────────────────────────────────────────
def load_db() -> list[dict]:
    """Return the CVE list, repairing legacy records in memory."""
    if DB_GZ.exists():
        with gzip.open(DB_GZ, "rt", encoding="utf-8") as fh:
            raw = json.load(fh)
    elif DB_LEGACY.exists():
        raw = json.loads(DB_LEGACY.read_text(encoding="utf-8"))
    else:
        return []
    if isinstance(raw, dict):
        raw = raw.get("cves", [])
    return [repair_record(r) for r in raw if isinstance(r, dict) and r.get("id")]


def save_db(records: list[dict]) -> None:
    """Write the DB gzipped and deterministically (mtime=0) so unchanged data
    produces a byte-identical file and git sees no diff."""
    records = sorted(records, key=lambda x: (-int(x.get("year") or 0), x.get("id", "")))
    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    tmp = DB_GZ.with_suffix(".gz.tmp")
    with open(tmp, "wb") as raw_fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_fh, compresslevel=9, mtime=0) as gz:
            gz.write(payload)
    tmp.replace(DB_GZ)
    if DB_LEGACY.exists():
        DB_LEGACY.unlink()


# ── classification ───────────────────────────────────────────────────
def severity(score: float | None, cvss_version: str | None = None) -> str:
    try:
        s = float(score or 0)
    except (TypeError, ValueError):
        s = 0.0
    if s <= 0 and not cvss_version:
        return "Unscored"
    if s >= 9:
        return "Critical"
    if s >= 7:
        return "High"
    if s >= 4:
        return "Medium"
    return "Low"


# Checked in order; first match wins. CWE ids are the strongest signal.
_CWE_TYPES = [
    ({"CWE-78", "CWE-77", "CWE-88"}, "Command Injection"),
    ({"CWE-89"}, "SQL Injection"),
    ({"CWE-79", "CWE-80"}, "Cross-Site Scripting"),
    ({"CWE-352"}, "Cross-Site Request Forgery"),
    ({"CWE-918"}, "Server-Side Request Forgery"),
    ({"CWE-22", "CWE-23", "CWE-35", "CWE-59"}, "Path Traversal"),
    ({"CWE-502"}, "Deserialization"),
    ({"CWE-94", "CWE-95", "CWE-1336"}, "Code Injection"),
    ({"CWE-434"}, "Unrestricted File Upload"),
    ({"CWE-287", "CWE-288", "CWE-290", "CWE-306", "CWE-798", "CWE-1390"}, "Authentication Bypass"),
    ({"CWE-862", "CWE-863", "CWE-639", "CWE-284", "CWE-285"}, "Authorization Bypass"),
    ({"CWE-269", "CWE-250", "CWE-266", "CWE-732", "CWE-276"}, "Privilege Escalation"),
    ({"CWE-119", "CWE-120", "CWE-121", "CWE-122", "CWE-125", "CWE-787",
      "CWE-190", "CWE-191", "CWE-416", "CWE-415", "CWE-843"}, "Memory Corruption"),
    ({"CWE-400", "CWE-770", "CWE-674", "CWE-835", "CWE-1333", "CWE-476", "CWE-404"}, "Denial of Service"),
    ({"CWE-200", "CWE-209", "CWE-532", "CWE-312", "CWE-319", "CWE-359", "CWE-497"}, "Information Disclosure"),
    ({"CWE-295", "CWE-297", "CWE-326", "CWE-327", "CWE-328", "CWE-347"}, "Cryptographic Weakness"),
    ({"CWE-601"}, "Open Redirect"),
    ({"CWE-362", "CWE-367"}, "Race Condition"),
]

_TEXT_TYPES = [
    (r"sql injection", "SQL Injection"),
    (r"cross[- ]site scri|\bxss\b", "Cross-Site Scripting"),  # tolerate truncated text
    (r"cross[- ]site request forgery|\bcsrf\b", "Cross-Site Request Forgery"),
    (r"server[- ]side request forgery|\bssrf\b", "Server-Side Request Forgery"),
    (r"command injection|os command|execute arbitrary (?:system |os |shell )?commands", "Command Injection"),
    (r"path traversal|directory traversal|\.\./", "Path Traversal"),
    (r"deserializ", "Deserialization"),
    (r"template injection|\bssti\b|code injection|eval injection", "Code Injection"),
    (r"(?:unrestricted|arbitrary) file upload", "Unrestricted File Upload"),
    (r"remote code execution|\brce\b|execute arbitrary code|arbitrary code execution", "Remote Code Execution"),
    (r"authentication bypass|bypass authentication|hard-?coded (?:credentials|password)", "Authentication Bypass"),
    (r"missing authorization|incorrect access control|broken access control|idor|insecure direct object", "Authorization Bypass"),
    (r"privilege escalation|escalat\w+ (?:of )?privileges|elevate privileges", "Privilege Escalation"),
    (r"buffer overflow|out-of-bounds|use[- ]after[- ]free|heap overflow|integer overflow|memory corruption|type confusion", "Memory Corruption"),
    (r"denial of service|\bdos\b|crash|resource exhaustion|infinite loop|null pointer", "Denial of Service"),
    (r"information disclosure|sensitive information|information exposure|data exposure|leak", "Information Disclosure"),
    (r"open redirect", "Open Redirect"),
    (r"certificate validation|improper certificate|weak (?:crypto|encryption)", "Cryptographic Weakness"),
    (r"race condition", "Race Condition"),
]


def classify_type(description: str = "", cwes=None) -> str:
    cwe_set = {str(c).upper() for c in (cwes or [])}
    for ids, label in _CWE_TYPES:
        if cwe_set & ids:
            return label
    text = (description or "").lower()
    for pattern, label in _TEXT_TYPES:
        if re.search(pattern, text):
            return label
    return "Security Vulnerability"


def repair_record(rec: dict) -> dict:
    """Fix fields produced by older ingestion code. Idempotent."""
    rec["severity"] = severity(rec.get("cvss"), rec.get("cvss_version"))
    # Legacy imports predate these fields. Mark provenance honestly rather
    # than inventing dates.
    rec.setdefault("source", "legacy-import")
    rec.setdefault("published_date", None)
    if not isinstance(rec.get("known_exploited"), bool):
        rec["known_exploited"] = bool(rec.get("known_exploited"))
    if rec.get("type") in _DEFAULT_TYPES:
        rec["type"] = classify_type(rec.get("description", ""), rec.get("cwe"))
    return rec
