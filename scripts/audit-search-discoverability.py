#!/usr/bin/env python3
"""Read-only SEO, answer-engine, and technical discoverability audit."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SITE_URL = "https://www.itvedas.com"
AI_CRAWLERS = ("GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "PerplexityBot", "Google-Extended")
CONTENT_ROOTS = ("articles", "chapters", "news", "toolkit")
SKIP_DIRS = {".git", ".wrangler", ".venv", "coverage", "node_modules", "venv", "__pycache__"}
NON_PUBLIC_PATH_PARTS = {
    "assets", "cve-data", "deployment", "drafts", "functions", "knowledge-imports",
    "partials", "scripts", "tests",
}
NON_PUBLIC_FILES = {
    "404.html", "cve-database-complete.html", "cve-database.html",
    "cve-detail.html", "cve-listing.html", "preview.html",
}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


class PageParser(HTMLParser):
    """Collect page-level HTML signals without external dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.headings: list[tuple[int, str]] = []
        self.in_heading: int | None = None
        self.heading_parts: list[str] = []
        self.text_parts: list[str] = []
        self.scripts: list[dict[str, str]] = []
        self.in_jsonld = False
        self.script_parts: list[str] = []
        self.html_attrs: dict[str, str] = {}
        self.external_assets = 0
        self.missing_image_dimensions = 0
        self.missing_lazy_loading = 0
        self.suppressed_text_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.html_attrs = values
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = values.get("name", "").lower() or values.get("property", "").lower()
            if key:
                self.meta[key].append(values)
        elif tag == "link":
            if values.get("href"):
                self.links.append(values)
            href = values.get("href", "")
            if href.startswith(("https://", "http://")) and values.get("rel", "").lower() in {
                "stylesheet", "preload", "modulepreload"
            }:
                self.external_assets += 1
        elif tag == "a" and values.get("href"):
            self.links.append(values)
        elif tag == "img":
            self.images.append(values)
            if not values.get("width") or not values.get("height"):
                self.missing_image_dimensions += 1
            if values.get("loading", "").lower() != "lazy":
                self.missing_lazy_loading += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.in_heading = int(tag[1])
            self.heading_parts = []
        elif tag in {"head", "script", "style", "noscript", "svg"}:
            self.suppressed_text_tags.append(tag)
            if tag == "script":
                source = values.get("src", "")
                if source.startswith(("https://", "http://")):
                    self.external_assets += 1
                self.in_jsonld = values.get("type", "").lower() == "application/ld+json"
                self.script_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in self.suppressed_text_tags:
            self.suppressed_text_tags.reverse()
            self.suppressed_text_tags.remove(tag)
            self.suppressed_text_tags.reverse()
        if tag == "title":
            self.in_title = False
        elif re.fullmatch(r"h[1-6]", tag) and self.in_heading is not None:
            self.headings.append((self.in_heading, clean_text(" ".join(self.heading_parts))))
            self.in_heading = None
        elif tag == "script" and self.in_jsonld:
            self.scripts.append({"type": "application/ld+json", "content": "".join(self.script_parts)})
            self.in_jsonld = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_heading is not None:
            self.heading_parts.append(data)
        if self.in_jsonld:
            self.script_parts.append(data)
        if self.suppressed_text_tags:
            return
        self.text_parts.append(data)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def schema_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_objects(child)


def page_url(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if relative == "index.html":
        relative = ""
    elif relative.endswith("/index.html"):
        relative = relative[: -len("index.html")]
    elif relative.endswith(".html"):
        relative = relative[:-5]
    return f"{SITE_URL}/{relative}"


def parse_page(path: Path) -> tuple[PageParser, str]:
    source = path.read_text(encoding="utf-8", errors="replace")
    parser = PageParser()
    parser.feed(source)
    parser.close()
    return parser, source


def add_finding(
    findings: list[dict[str, str]], severity: str, category: str, path: str, issue: str, recommendation: str
) -> None:
    findings.append({
        "severity": severity,
        "category": category,
        "path": path,
        "issue": issue,
        "recommendation": recommendation,
    })


def html_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*.html")
        if not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    )


def is_public_page(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    lowered_parts = {part.lower() for part in relative.parts}
    if lowered_parts.intersection(NON_PUBLIC_PATH_PARTS) or path.name.lower() in NON_PUBLIC_FILES:
        return False
    if "template" in path.stem.lower():
        return False
    return True


def resolve_local_url(source: Path, url: str, root: Path) -> Path | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme or parsed.netloc or url.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None
    raw_path = urllib.parse.unquote(parsed.path)
    if not raw_path:
        return source
    target = (root / raw_path.lstrip("/")) if raw_path.startswith("/") else (source.parent / raw_path)
    try:
        target = target.resolve()
        target.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    candidates = [target]
    if not raw_path.lower().endswith(".html"):
        candidates.extend((target.with_name(target.name + ".html"), target / "index.html"))
    elif target.suffix.lower() == ".html" and target.name.lower() != "index.html":
        candidates.append(target.with_name("index.html"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return target


def normalized_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))


def audit(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    all_pages = html_files(root)
    pages = [path for path in all_pages if is_public_page(path, root)]
    if not all_pages:
        raise ValueError(f"No HTML pages found under {root}")

    indexed_pages: list[dict[str, Any]] = []
    title_paths: dict[str, list[str]] = defaultdict(list)
    canonical_paths: dict[str, list[str]] = defaultdict(list)
    incoming_pages: dict[str, set[str]] = defaultdict(set)
    total_words = 0
    article_count = 0
    now = dt.date.today()

    for path in pages:
        relative = path.relative_to(root).as_posix()
        try:
            parser, source = parse_page(path)
        except OSError as exc:
            add_finding(findings, "high", "crawlability", relative, f"Unable to read HTML: {exc}", "Restore readable UTF-8 HTML.")
            continue
        title = clean_text(" ".join(parser.title_parts))
        relative_parts = path.relative_to(root).parts
        is_content = relative_parts[0] in CONTENT_ROOTS
        meta = parser.meta
        description = clean_text(meta.get("description", [{}])[0].get("content", "")) if meta.get("description") else ""
        canonicals = [link.get("href", "").strip() for link in parser.links if link.get("rel", "").lower() == "canonical"]
        canonical = canonicals[0] if canonicals else ""
        robots_values = " ".join(item.get("content", "") for item in meta.get("robots", []))
        noindex = bool(re.search(r"\bnoindex\b", robots_values, re.I))
        text_content = clean_text(" ".join(parser.text_parts))
        words = len(text_content.split())
        total_words += words
        article_count += int(is_content and path.name != "index.html")

        if not parser.html_attrs.get("lang"):
            add_finding(findings, "medium", "accessibility", relative, "The root <html> element has no language declaration.", "Set an accurate lang attribute, such as lang=\"en\".")
        if not title:
            add_finding(findings, "high", "on-page SEO", relative, "Missing or empty <title>.", "Add a unique, descriptive page title.")
        elif len(title) < 20 or len(title) > 70:
            add_finding(findings, "low", "on-page SEO", relative, f"Title is {len(title)} characters; outside the 20–70 character review range.", "Review title clarity and search-result truncation; this range is advisory.")
        if title:
            title_paths[title.casefold()].append(relative)
        if not description:
            add_finding(findings, "medium", "on-page SEO", relative, "Missing meta description.", "Write a unique summary that accurately describes the page.")
        elif len(description) < 70 or len(description) > 170:
            add_finding(findings, "low", "on-page SEO", relative, f"Meta description is {len(description)} characters; outside the 70–170 character review range.", "Review whether the snippet is complete and compelling; search engines may rewrite it.")
        if len(meta.get("description", [])) > 1:
            add_finding(findings, "medium", "on-page SEO", relative, "Multiple meta descriptions are declared.", "Keep one accurate meta description.")
        if len(canonicals) != 1:
            add_finding(findings, "high" if not canonicals else "medium", "indexing", relative,
                        "Missing canonical URL." if not canonicals else f"Found {len(canonicals)} canonical URLs.",
                        "Declare exactly one absolute, preferred canonical URL for indexable pages.")
        elif not canonical.startswith("https://"):
            add_finding(findings, "high", "indexing", relative, f"Canonical is not an absolute HTTPS URL: {canonical}", "Use the preferred HTTPS URL on the canonical site host.")
        else:
            canonical_paths[normalized_url(canonical)].append(relative)
            if urllib.parse.urlsplit(canonical).netloc.lower() not in {"www.itvedas.com", "itvedas.com"}:
                add_finding(findings, "high", "indexing", relative, f"Canonical points to an unexpected host: {canonical}", "Point the canonical to the preferred ITVedas host or explicitly confirm the cross-domain canonical.")
        if not meta.get("viewport"):
            add_finding(findings, "medium", "mobile", relative, "Missing viewport meta tag.", "Add a responsive viewport declaration.")
        h1s = [text for level, text in parser.headings if level == 1]
        if len(h1s) != 1:
            add_finding(findings, "medium", "on-page SEO", relative, f"Found {len(h1s)} H1 headings; expected one descriptive page heading.", "Use one clear H1 aligned with the page's primary subject.")
        if is_content and path.name != "index.html" and words < 300:
            add_finding(findings, "medium", "content depth", relative, f"Only {words} visible words detected on this content page.", "Review whether the page fully answers the search intent; word count alone is not a quality score.")
        if is_content and path.name != "index.html":
            if words >= 300 and len(re.findall(r"<h[2-6]\b", source, re.I)) == 0:
                add_finding(findings, "low", "content structure", relative, "Long-form content has no H2–H6 section headings.", "Break the article into descriptive sections for readers and passage-level discovery.")
            if not re.search(r"<link\b[^>]*rel=[\"'](?:prev|next)[\"']", source, re.I):
                pass
            has_article_schema = False
            for item in parser.scripts:
                try:
                    schema = json.loads(item["content"])
                    for obj in schema_objects(schema):
                        schema_type = obj.get("@type", [])
                        types = schema_type if isinstance(schema_type, list) else [schema_type]
                        if any(str(value).lower() in {"article", "newsarticle", "blogposting", "techarticle"} for value in types):
                            has_article_schema = True
                        published = obj.get("datePublished")
                        if isinstance(published, str):
                            try:
                                if dt.date.fromisoformat(published[:10]) > now:
                                    add_finding(findings, "medium", "structured data", relative, f"Article datePublished is in the future: {published[:10]}.", "Correct the publication date; future dates can undermine trust and date interpretation.")
                            except ValueError:
                                add_finding(findings, "low", "structured data", relative, f"Invalid datePublished value: {published!r}.", "Use a valid ISO 8601 date.")
                except (json.JSONDecodeError, TypeError):
                    add_finding(findings, "high", "structured data", relative, "Malformed JSON-LD structured data.", "Correct or remove the invalid application/ld+json block.")
            if not has_article_schema:
                add_finding(findings, "low", "structured data", relative, "No Article/NewsArticle/BlogPosting/TechArticle JSON-LD found.", "Consider accurate Article markup with headline, author, datePublished, dateModified, and image; markup does not guarantee a rich result.")
            if not re.search(r"<(?:blockquote|cite)\b|\bhttps?://", source, re.I):
                add_finding(findings, "low", "trust and citations", relative, "No obvious citation, quotation, or external source link was detected.", "For factual or time-sensitive claims, cite primary sources and distinguish original analysis from reporting.")
            if not re.search(r"<(?:time\b|meta\b[^>]*(?:datePublished|dateModified))", source, re.I) and not re.search(r'"date(?:Published|Modified)"\s*:', source, re.I):
                add_finding(findings, "low", "trust and freshness", relative, "No publication or modification date was detected.", "Display and maintain accurate publication/update dates where editorially appropriate.")

        for image in parser.images:
            if "alt" not in image:
                add_finding(findings, "medium", "accessibility", relative, "An image is missing its alt attribute.", "Add meaningful alternative text, or alt=\"\" for a decorative image.")
        if parser.missing_image_dimensions:
            add_finding(findings, "low", "page experience", relative, f"{parser.missing_image_dimensions} image(s) have no explicit width or height.", "Add intrinsic dimensions to reduce layout shift.")
        if parser.missing_lazy_loading > 2 and len(parser.images) > 3:
            add_finding(findings, "info", "page experience", relative, f"{parser.missing_lazy_loading} of {len(parser.images)} images do not declare lazy loading.", "Lazy-load below-the-fold images while keeping the primary/hero image eager.")
        if parser.external_assets > 8:
            add_finding(findings, "info", "page experience", relative, f"{parser.external_assets} external scripts/styles were detected.", "Review third-party dependencies for performance, privacy, and availability.")

        if not noindex:
            indexed_pages.append({"path": path, "url": page_url(path, root), "canonical": canonical, "relative": relative})

        for link in parser.links:
            href = link.get("href", "").strip()
            if not href or "{" in href or "}" in href:
                continue
            target = resolve_local_url(path, href, root)
            if target is None:
                parsed = urllib.parse.urlsplit(href)
                if parsed.scheme in {"http", "https"} and parsed.netloc.lower() in {"www.itvedas.com", "itvedas.com"}:
                    target = resolve_local_url(path, parsed.path, root)
                else:
                    continue
            if target is not None:
                if not target.exists():
                    add_finding(findings, "medium", "internal links", relative, f"Broken local link: {href}", "Update the target URL or restore the intended destination.")
                else:
                    resolved = target.resolve()
                    incoming_pages[str(resolved)].add(relative)

    for title, paths in title_paths.items():
        if len(paths) > 1:
            for path in paths:
                add_finding(findings, "medium", "duplicate metadata", path, f"Duplicate title shared by {len(paths)} pages: {title}", "Write a distinct title that identifies this page's unique purpose.")
    for canonical, paths in canonical_paths.items():
        if len(paths) > 1:
            for path in paths:
                add_finding(findings, "high", "duplicate metadata", path, f"Canonical URL is shared by {len(paths)} pages: {canonical}", "Ensure each indexable page has its own canonical, or intentionally consolidate duplicate content.")

    for path in pages:
        relative = path.relative_to(root).as_posix()
        if relative.split("/", 1)[0] in CONTENT_ROOTS and path.name != "index.html":
            if not incoming_pages.get(str(path.resolve())):
                add_finding(findings, "low", "internal links", relative, "No incoming internal links were detected.", "Link this page from a relevant hub or related article if it should be discoverable.")

    robots_path = root / "robots.txt"
    if not robots_path.is_file():
        add_finding(findings, "high", "discovery files", "robots.txt", "robots.txt is missing.", "Publish a valid robots.txt with the sitemap URL and intended crawler access.")
    else:
        robots = robots_path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"(?im)^\s*Sitemap:\s*https://www\.itvedas\.com/sitemap\.xml\s*$", robots):
            add_finding(findings, "medium", "discovery files", "robots.txt", "Expected sitemap declaration is missing.", "Add Sitemap: https://www.itvedas.com/sitemap.xml.")
        for crawler in AI_CRAWLERS:
            if not re.search(rf"(?im)^\s*User-agent:\s*{re.escape(crawler)}\s*$", robots):
                add_finding(findings, "info", "AI crawler policy", "robots.txt", f"No explicit robots.txt policy for {crawler}.", "Review this crawler's current published policy and state your intended access; robots.txt is a request, not access control.")

    llms_path = root / "llms.txt"
    if not llms_path.is_file():
        add_finding(findings, "low", "AI discovery", "llms.txt", "No llms.txt file is present.", "Consider a concise, maintained guide to the site's authoritative content; llms.txt is an emerging convention, not a ranking/indexing guarantee.")
    elif len(llms_path.read_text(encoding="utf-8", errors="replace").split()) < 30:
        add_finding(findings, "low", "AI discovery", "llms.txt", "llms.txt has fewer than 30 words.", "Review whether it sufficiently describes the site and links to authoritative, current resources.")

    sitemap_path = root / "sitemap.xml"
    sitemap_urls: set[str] = set()
    if not sitemap_path.is_file():
        add_finding(findings, "high", "discovery files", "sitemap.xml", "Sitemap is missing.", "Generate and publish sitemap.xml containing canonical, indexable URLs.")
    else:
        try:
            xml_root = ET.parse(sitemap_path).getroot()
            for location in xml_root.iter():
                if location.tag.rsplit("}", 1)[-1] == "loc" and location.text:
                    sitemap_urls.add(normalized_url(location.text))
        except ET.ParseError as exc:
            add_finding(findings, "critical", "discovery files", "sitemap.xml", f"Sitemap XML is invalid: {exc}", "Regenerate a valid XML sitemap.")
        for record in indexed_pages:
            canonical = record["canonical"] or record["url"]
            normalized = normalized_url(canonical)
            if normalized not in sitemap_urls:
                add_finding(findings, "medium", "sitemap coverage", record["relative"], f"Indexable page is absent from sitemap: {canonical}", "Add its preferred canonical URL to the generated sitemap or apply noindex if it should not be indexed.")
        for url in sorted(sitemap_urls):
            matching = next((record for record in indexed_pages if normalized_url(record["canonical"] or record["url"]) == url), None)
            if matching is None and url.startswith(SITE_URL):
                add_finding(findings, "low", "sitemap coverage", "sitemap.xml", f"Sitemap URL did not match an indexable local HTML page: {url}", "Verify the URL is intentionally generated, live, canonical, and indexable.")

    report_counts = Counter(item["severity"] for item in findings)
    findings.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["category"], item["path"], item["issue"]))
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "site": SITE_URL,
        "scope": "All repository HTML pages, internal links, robots.txt, sitemap.xml, and llms.txt",
        "summary": {
            "html_pages": len(pages),
            "excluded_non_public_html_pages": len(all_pages) - len(pages),
            "content_pages": article_count,
            "indexable_pages": len(indexed_pages),
            "sitemap_urls": len(sitemap_urls),
            "visible_words_total": total_words,
            "findings_total": len(findings),
            "by_severity": {severity: report_counts.get(severity, 0) for severity in SEVERITY_ORDER},
        },
        "findings": findings,
        "notes": [
            "This is a static, heuristic audit. It does not query Google Search Console, Google Analytics, Bing Webmaster Tools, live HTTP status, Core Web Vitals field data, or live search rankings.",
            "GEO/AIO recommendations focus on crawl access, clear source attribution, structured context, answer-ready organization, freshness, and discoverable authoritative resources. No markup or file guarantees placement in search or generative answers.",
            "Robots.txt and llms.txt are public guidance files, not security controls. Never expose secrets or private content to make it machine-readable.",
            "Word-count and snippet-length thresholds are review prompts, not direct ranking requirements.",
        ],
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# ITVedas search discoverability audit",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Scope: {report['scope']}",
        f"- HTML pages: {summary['html_pages']} ({summary['content_pages']} content pages)",
        f"- Indexable pages: {summary['indexable_pages']} · Sitemap URLs: {summary['sitemap_urls']}",
        f"- Findings: {summary['findings_total']}",
        "",
        "## Findings by severity",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for severity in SEVERITY_ORDER:
        lines.append(f"| {severity.title()} | {summary['by_severity'][severity]} |")
    lines.extend(["", "## Actionable findings", ""])
    if not report["findings"]:
        lines.append("No findings were detected by these checks.")
    else:
        for finding in report["findings"]:
            lines.extend([
                f"### [{finding['severity'].upper()}] {finding['category']} — `{finding['path']}`",
                "",
                f"**Finding:** {finding['issue']}",
                "",
                f"**Suggested action:** {finding['recommendation']}",
                "",
            ])
    lines.extend(["## Scope and limitations", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to audit (default: current directory).")
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/itvedas-discoverability-audit"), help="Directory for JSON and Markdown reports.")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"Repository root is not a directory: {root}")
    try:
        report = audit(root)
    except (OSError, ValueError) as exc:
        print(f"Discoverability audit failed: {exc}", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "discoverability-audit.json"
    markdown_path = args.out_dir / "discoverability-audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "json_report": str(json_path), "markdown_report": str(markdown_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
