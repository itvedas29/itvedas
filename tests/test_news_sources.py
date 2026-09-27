import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "itvedas-brain"))
from core import news_sources as ns  # noqa: E402

NOW = dt.datetime(2026, 9, 27, 12, tzinfo=dt.timezone.utc)

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>Chan</title><link>https://ex.com</link>
<item><title>Critical Fortinet flaw CVE-2026-1111 exploited in attacks</title><link>https://ex.com/a</link>
<description><![CDATA[<p>Attackers exploit <b>FortiOS</b> bug.</p>]]></description><pubDate>Sat, 26 Sep 2026 10:00:00 GMT</pubDate></item>
<item><title>Old story that should be filtered out by age</title><link>https://ex.com/old</link>
<pubDate>Mon, 01 Jun 2026 10:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>F</title>
<entry><title>Hackers exploit Fortinet FortiOS vulnerability CVE-2026-1111</title>
<link rel="alternate" href="https://other.org/b"/><updated>2026-09-27T08:00:00Z</updated>
<summary>FortiOS SSL-VPN flaw under active exploitation.</summary></entry>
<entry><title>Kubernetes 1.40 released with new scheduler features</title>
<link href="https://other.org/k8s"/><published>2026-09-27T01:00:00Z</published></entry></feed>"""


class TestFeeds(unittest.TestCase):
    def test_rss_and_atom_parse_with_links_and_dates(self):
        rss = ns.parse_feed(RSS, "https://www.ex.com/feed")
        atom = ns.parse_feed(ATOM, "https://other.org/atom")
        self.assertEqual(rss[0]["link"], "https://ex.com/a")
        self.assertEqual(rss[0]["source"], "ex.com")
        self.assertIn("FortiOS", rss[0]["desc"])
        self.assertNotIn("<b>", rss[0]["desc"])
        self.assertEqual(atom[0]["link"], "https://other.org/b")
        self.assertEqual(atom[1]["published"].year, 2026)

    def test_fetch_all_filters_old_items_and_survives_dead_feeds(self):
        pages = {"https://ex.com/rss": RSS, "https://other.org/atom": ATOM}
        def fetch(url, **kw):
            if url not in pages:
                raise OSError("404")
            return pages[url]
        logs = []
        items = ns.fetch_all_feeds(list(pages) + ["https://dead.example/feed"], now=NOW, log=logs.append, fetch=fetch)
        titles = [i["title"] for i in items]
        self.assertNotIn("Old story that should be filtered out by age", titles)
        self.assertEqual(len(items), 3)
        self.assertIn("FAIL", logs[0])


class TestClusteringAndRanking(unittest.TestCase):
    def setUp(self):
        items = ns.parse_feed(RSS, "https://ex.com/rss")[:1] + ns.parse_feed(ATOM, "https://other.org/atom")
        self.clusters = ns.cluster_items(items)

    def test_same_story_from_two_outlets_merges(self):
        self.assertEqual(len(self.clusters), 2)
        forti = next(c for c in self.clusters if c["cves"])
        self.assertEqual(forti["sources"], ["ex.com", "other.org"])

    def test_ranking_prefers_exploited_multi_source_story(self):
        lookup = lambda cid: {"id": cid, "cvss": 9.8, "severity": "Critical", "known_exploited": True}
        ranked = ns.rank_clusters(self.clusters, lookup)
        self.assertTrue(ranked[0]["cves"])
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_min_score_skips_trivia_but_keeps_official_announcements(self):
        trivia = ns.cluster_items([{"title": "Browser extension update fixes small UI glitch", "link": "https://bc.test/x",
                                    "desc": "", "source": "bleepingcomputer.com", "published": None}])
        official = ns.cluster_items([{"title": "Kubernetes 1.40 released with new scheduler", "link": "https://k8s.test/x",
                                      "desc": "", "source": "kubernetes.io", "published": None}])
        self.assertLess(ns.rank_clusters(trivia)[0]["score"], ns.MIN_SCORE)
        self.assertGreaterEqual(ns.rank_clusters(official)[0]["score"], ns.MIN_SCORE)

    def test_already_published_by_cve_and_by_title(self):
        forti, k8s = sorted(self.clusters, key=lambda c: not c["cves"])
        seen = {ns.story_key(forti): "2026-09-20"}
        self.assertTrue(ns.already_published(forti, seen))
        self.assertFalse(ns.already_published(k8s, seen))
        seen[ns.story_key(k8s)] = "2026-09-20"
        self.assertTrue(ns.already_published(k8s, seen))


class TestGroundingAndSafety(unittest.TestCase):
    def test_extract_article_text_skips_chrome(self):
        page = ("<html><nav><p>Home About Contact navigation links here</p></nav><article>"
                "<p>Fortinet disclosed a critical heap overflow in FortiOS SSL-VPN on Friday.</p>"
                "<p>Subscribe to our newsletter for more stories like this one every day.</p>"
                "<script>var x='<p>not text at all, this is javascript code</p>'</script>"
                "<p>Administrators should upgrade to FortiOS 7.6.5 or disable SSL-VPN.</p></article></html>")
        text = ns.extract_article_text(page)
        self.assertIn("heap overflow", text)
        self.assertIn("7.6.5", text)
        self.assertNotIn("navigation", text)
        self.assertNotIn("newsletter", text)
        self.assertNotIn("javascript", text)

    def test_extract_keeps_security_content_about_cookies(self):
        page = ("<p>Attackers forged session cookies to bypass FortiWeb authentication checks.</p>"
                "<p>We use cookies to improve your experience on this website, accept them.</p>")
        text = ns.extract_article_text(page)
        self.assertIn("session cookies", text)
        self.assertNotIn("improve your experience", text)

    def test_sanitizer_removes_injected_markup(self):
        dirty = ('<h2>Fix</h2><p onclick="steal()">Patch <strong>now</strong></p>'
                 '<script>alert(1)</script><img src=x onerror=alert(2)>'
                 '<a href="javascript:alert(3)">bad</a><a href="https://vendor.com/advisory">good</a>'
                 '<iframe src="https://evil"></iframe><p style="display:none">hidden</p>')
        clean = ns.sanitize_html(dirty)
        for bad in ("script", "onclick", "onerror", "<img", "javascript:", "iframe", "style="):
            self.assertNotIn(bad, clean)
        self.assertIn("<h2>Fix</h2>", clean)
        self.assertIn('href="https://vendor.com/advisory" rel="noopener nofollow"', clean)
        self.assertIn("<strong>now</strong>", clean)


if __name__ == "__main__":
    unittest.main()
