"""Tests for the read-only search discoverability audit."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit-search-discoverability.py"
SPEC = importlib.util.spec_from_file_location("discoverability_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


class TestDiscoverabilityAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        article_text = " ".join(
            ["A documented control helps administrators secure identity, hardware, access, and evidence consistently."]
            * 35
        )
        (self.root / "articles").mkdir()
        (self.root / "robots.txt").write_text(
            "User-agent: *\nAllow: /\nSitemap: https://www.itvedas.com/sitemap.xml\n",
            encoding="utf-8",
        )
        (self.root / "llms.txt").write_text(
            "# Test site\nAn authoritative guide to reliable IT operations and security practice.\n",
            encoding="utf-8",
        )
        self.article = self.root / "articles" / "example.html"
        self.article.write_text(
            f"""<!doctype html>
<html lang="en"><head>
<title>Example IT security runbook for administrators</title>
<meta name="description" content="A practical IT security runbook with detailed controls and clear steps for administrators to apply.">
<meta name="robots" content="index,follow">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://www.itvedas.com/articles/example">
<script type="application/ld+json">{{"@type":"TechArticle","headline":"Example","datePublished":"2026-01-01"}}</script>
</head><body><h1>Example IT security runbook</h1>
<h2>Deployment controls</h2><p>Read the <a href="/about">about page</a>. {article_text}</p>
<img src="/assets/example.png" alt="Example illustration" width="600" height="400">
</body></html>""",
            encoding="utf-8",
        )
        (self.root / "about.html").write_text(
            '<!doctype html><html lang="en"><head><title>About ITVedas</title>'
            '<meta name="description" content="Learn more about this independent IT education resource and its practical learning guides.">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<link rel="canonical" href="https://www.itvedas.com/about"></head>'
            '<body><h1>About ITVedas</h1></body></html>',
            encoding="utf-8",
        )
        self.sitemap = self.root / "sitemap.xml"
        self.sitemap.write_text(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "<url><loc>https://www.itvedas.com/articles/example</loc></url>"
            "<url><loc>https://www.itvedas.com/about</loc></url></urlset>",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_local_site_has_no_findings(self):
        report = AUDIT.audit(self.root)
        self.assertEqual(report["summary"]["html_pages"], 2)
        self.assertEqual(report["summary"]["indexable_pages"], 2)
        self.assertFalse(any(
            finding["severity"] in {"critical", "high", "medium"}
            for finding in report["findings"]
        ))

    def test_reports_missing_metadata_broken_link_and_sitemap_gap(self):
        self.sitemap.write_text(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "<url><loc>https://www.itvedas.com/about</loc></url></urlset>",
            encoding="utf-8",
        )
        self.article.write_text(
            '<!doctype html><html><head><title>Short</title></head><body>'
            '<h1>One</h1><a href="/missing-route">broken</a></body></html>',
            encoding="utf-8",
        )
        report = AUDIT.audit(self.root)
        issues = [finding["issue"] for finding in report["findings"]]
        self.assertTrue(any("Missing meta description" in issue for issue in issues))
        self.assertTrue(any("Missing canonical URL" in issue for issue in issues))
        self.assertTrue(any("Broken local link" in issue for issue in issues))
        self.assertTrue(any("absent from sitemap" in issue for issue in issues))

    def test_noindex_page_is_not_expected_in_sitemap(self):
        self.article.write_text(
            self.article.read_text(encoding="utf-8").replace(
                'content="index,follow"', 'content="noindex,follow"'
            ),
            encoding="utf-8",
        )
        report = AUDIT.audit(self.root)
        self.assertFalse(any(
            finding["path"] == "articles/example.html" and "absent from sitemap" in finding["issue"]
            for finding in report["findings"]
        ))

    def test_report_json_is_serializable(self):
        report = AUDIT.audit(self.root)
        self.assertEqual(json.loads(json.dumps(report))["site"], "https://www.itvedas.com")

    def test_extensionless_dotted_route_resolves_to_html_page(self):
        dotted_article = self.root / "articles" / "release-1.33-notes.html"
        dotted_article.write_text("<html></html>", encoding="utf-8")
        resolved = AUDIT.resolve_local_url(
            self.root / "about.html", "/articles/release-1.33-notes", self.root
        )
        self.assertEqual(resolved, dotted_article)


if __name__ == "__main__":
    unittest.main()
