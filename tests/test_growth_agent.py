import datetime
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "itvedas-brain"))

from core import google_data  # noqa: E402
from core import growth as G  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "itvedas-brain" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agent = _load("growth_agent", "growth-agent.py")

TODAY = datetime.date(2026, 11, 10)
PAGE = """<!DOCTYPE html><html><head>
<meta name="description" content="Old description about DNS &amp; lookups.">
<meta property="og:title" content="Old DNS Title | ITVedas">
<meta property="og:description" content="Old description about DNS &amp; lookups.">
<title>Old DNS Title | ITVedas</title>
<script type="application/ld+json">{"headline": "Old DNS Title", "dateModified": "2026-07-05"}</script>
</head><body><h1>What is DNS?</h1><p>DNS turns names into numbers.</p></body></html>"""
GOOD_TITLE = "What Is DNS and How Does It Work? Simple Guide"
GOOD_DESC = ("Learn what DNS is and how it works, step by step: how a domain name becomes "
             "an IP address, with plain-English examples for beginners.")


def row(page, clicks, impressions, position, query=None):
    r = {"page": page, "clicks": clicks, "impressions": impressions,
         "ctr": clicks / impressions if impressions else 0.0, "position": position}
    if query:
        r["query"] = query
    return r


class TestWindows(unittest.TestCase):
    def test_windows_are_adjacent_28_day_ranges_before_the_lag(self):
        w = G.windows(TODAY)
        self.assertEqual(w["current"], ("2026-10-11", "2026-11-07"))
        self.assertEqual(w["previous"], ("2026-09-13", "2026-10-10"))

    def test_after_window_waits_for_full_data(self):
        self.assertIsNone(G.after_window("2026-10-20", TODAY))
        self.assertEqual(G.after_window("2026-10-01", TODAY), ("2026-10-04", "2026-10-31"))


class TestUrlMapping(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "articles").mkdir()
        (self.root / "articles" / "dns.html").write_text(PAGE)
        (self.root / "index.html").write_text(PAGE)
        (self.root / "privacy-policy.html").write_text(PAGE)

    def tearDown(self):
        self.tmp.cleanup()

    def test_maps_extensionless_and_html_urls(self):
        for url in ("https://www.itvedas.com/articles/dns", "https://itvedas.com/articles/dns.html",
                    "https://www.itvedas.com/articles/dns?utm=1#top"):
            self.assertEqual(G.url_to_file(url, self.root).name, "dns.html")

    def test_refuses_non_editable_foreign_and_traversal_urls(self):
        for url in ("https://www.itvedas.com/", "https://www.itvedas.com/privacy-policy",
                    "https://evil.example/articles/dns", "https://www.itvedas.com/articles/../index",
                    "https://www.itvedas.com/articles/%2e%2e/index", "https://www.itvedas.com/articles/missing"):
            self.assertIsNone(G.url_to_file(url, self.root), url)


class TestOpportunities(unittest.TestCase):
    def test_low_ctr_needs_volume_position_and_a_real_shortfall(self):
        pages = [row("a", 2, 1000, 4.0),     # 0.2% at position 4: flagged
                 row("b", 60, 1000, 4.0),    # 6%: fine
                 row("c", 0, 50, 3.0),       # too few impressions
                 row("d", 1, 1000, 30.0)]    # ranks too low for a snippet fix
        self.assertEqual([p["page"] for p in G.find_low_ctr(pages)], ["a"])

    def test_gaps_skip_brand_short_and_well_ranked_queries(self):
        rows = [row("p", 0, 100, 25.0, "how does bgp peering work"),
                row("p", 0, 100, 25.0, "itvedas dns"),
                row("p", 0, 100, 25.0, "dns"),
                row("p", 5, 100, 3.0, "what is dns"),
                row("p", 0, 10, 40.0, "rare long query here")]
        self.assertEqual([g["query"] for g in G.find_gaps(rows)], ["how does bgp peering work"])

    def test_striking_groups_queries_by_page(self):
        rows = [row("p1", 1, 80, 9.0, "q one"), row("p1", 0, 40, 14.0, "q two"),
                row("p2", 9, 500, 2.0, "top already")]
        out = G.find_striking(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["queries"], ["q one", "q two"])

    def test_decliners(self):
        out = G.find_decliners([row("a", 10, 100, 5)], [row("a", 40, 100, 5), row("b", 5, 100, 5)])
        self.assertEqual([d["page"] for d in out], ["a"])

    def test_ai_sources(self):
        self.assertTrue(G.is_ai_source("chatgpt.com"))
        self.assertTrue(G.is_ai_source("perplexity.ai"))
        self.assertFalse(G.is_ai_source("google"))


class TestHeadEditing(unittest.TestCase):
    def test_read_head_strips_suffix_and_unescapes(self):
        head = G.read_head(PAGE)
        self.assertEqual(head, {"title": "Old DNS Title", "suffix": " | ITVedas",
                                "description": "Old description about DNS & lookups."})

    def test_apply_head_changes_only_head_tags_and_escapes(self):
        out = G.apply_head(PAGE, 'DNS & "You" <b>', "New desc with \"quotes\" & more", " | ITVedas")
        self.assertIn("<title>DNS &amp; \"You\" &lt;b&gt; | ITVedas</title>", out)
        self.assertIn('<meta name="description" content="New desc with &quot;quotes&quot; &amp; more">', out)
        self.assertIn('property="og:title" content="DNS &amp; &quot;You&quot; &lt;b&gt; | ITVedas"', out)
        self.assertIn("<h1>What is DNS?</h1>", out)
        self.assertIn('"headline": "Old DNS Title", "dateModified": "2026-07-05"', out)
        self.assertEqual(G.read_head(out)["title"], 'DNS & "You" <b>')

    def test_apply_then_revert_is_lossless(self):
        head = G.read_head(PAGE)
        changed = G.apply_head(PAGE, GOOD_TITLE, GOOD_DESC, head["suffix"])
        before, after = G.head_tags(PAGE), G.head_tags(changed)
        self.assertEqual(G.revert_head(changed, before, after), PAGE)
        self.assertIsNone(G.revert_head(PAGE, before, after))

    def test_other_suffix_styles_and_mismatched_og_tags_revert_exactly(self):
        page = ('<title>Phind - AI Tool Review & Guide \u2014 ITVedas</title>\n'
                '<meta name="description" content="Old.">\n'
                '<meta property="og:title" content="Phind - a different og title">')
        head = G.read_head(page)
        self.assertEqual((head["title"], head["suffix"]), ("Phind - AI Tool Review & Guide", " \u2014 ITVedas"))
        changed = G.apply_head(page, GOOD_TITLE, GOOD_DESC, head["suffix"])
        self.assertIn("<title>" + GOOD_TITLE + " \u2014 ITVedas</title>", changed)
        self.assertEqual(G.revert_head(changed, G.head_tags(page), G.head_tags(changed)), page)

    def test_validate_rewrite(self):
        old = G.read_head(PAGE)
        self.assertIsNone(G.validate_rewrite(old, GOOD_TITLE, GOOD_DESC, "what is dns how it works"))
        self.assertIn("length", G.validate_rewrite(old, "DNS", GOOD_DESC, "dns"))
        self.assertIn("length", G.validate_rewrite(old, GOOD_TITLE, "Too short.", "dns"))
        self.assertIn("markup", G.validate_rewrite(old, GOOD_TITLE + "<", GOOD_DESC, "dns"))
        self.assertIn("site name", G.validate_rewrite(old, "What Is DNS Explained | ITVedas", GOOD_DESC, "dns"))
        self.assertIn("search for", G.validate_rewrite(old, GOOD_TITLE, GOOD_DESC, "kubernetes pod networking"))
        self.assertEqual(G.validate_rewrite(old, old["title"], old["description"], "dns"), "no change")

    def test_judge_change(self):
        base = {"ctr": 0.02, "position": 5.0}
        self.assertEqual(G.judge_change(base, {"impressions": 500, "ctr": 0.01, "position": 5.5}), "reverted")
        self.assertEqual(G.judge_change(base, {"impressions": 500, "ctr": 0.03, "position": 5.5}), "kept")
        self.assertEqual(G.judge_change(base, {"impressions": 500, "ctr": 0.01, "position": 12.0}), "inconclusive")
        self.assertEqual(G.judge_change(base, {"impressions": 10, "ctr": 0.0, "position": 5.0}), "inconclusive")


class TestKeywordsAndLlms(unittest.TestCase):
    def test_duplicate_keywords(self):
        existing = ["what is DNS and how does it work step by step"]
        self.assertTrue(G.is_duplicate_keyword("What is DNS and how does it work, step by step?", existing))
        self.assertTrue(G.is_duplicate_keyword("how does dns work step by step", existing))
        self.assertFalse(G.is_duplicate_keyword("how to flush dns cache on windows", existing))

    def test_llms_section_is_inserted_then_replaced(self):
        text = "# ITVedas\n\n## Core topics\n\n- a\n\n## Reference\n\n- b\n"
        once = G.update_llms_txt(text, [("T1", "https://x/1")])
        self.assertLess(once.index(G.LLMS_HEADING), once.index("## Reference"))
        twice = G.update_llms_txt(once, [("T2", "https://x/2")])
        self.assertEqual(twice.count(G.LLMS_HEADING), 1)
        self.assertIn("T2", twice)
        self.assertNotIn("T1", twice)
        self.assertIn("## Reference\n\n- b", twice)


class TestServiceAccountParsing(unittest.TestCase):
    def test_unset_is_none_and_garbage_raises(self):
        self.assertIsNone(google_data.load_service_account_info(""))
        with self.assertRaises(google_data.GoogleDataError):
            google_data.load_service_account_info("not-a-key")
        with self.assertRaises(google_data.GoogleDataError):
            google_data.load_service_account_info('{"type": "authorized_user"}')

    def test_accepts_raw_and_base64_json(self):
        import base64
        raw = json.dumps({"type": "service_account", "client_email": "bot@example.iam.gserviceaccount.com"})
        self.assertEqual(google_data.load_service_account_info(raw)["type"], "service_account")
        encoded = base64.b64encode(raw.encode()).decode()
        self.assertEqual(google_data.load_service_account_info(encoded)["type"], "service_account")


class TestFindSite(unittest.TestCase):
    class Session:
        def __init__(self, sites):
            self.sites = sites

        def get(self, url, timeout):
            outer = self

            class Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"siteEntry": [{"siteUrl": u, "permissionLevel": "siteFullUser"} for u in outer.sites]}
            return Response()

    def test_prefers_domain_property_then_https_www(self):
        find = google_data.gsc_find_site
        self.assertEqual(find(self.Session(["https://www.itvedas.com/", "sc-domain:itvedas.com"])), "sc-domain:itvedas.com")
        self.assertEqual(find(self.Session(["http://itvedas.com/", "https://www.itvedas.com/", "https://other.com/"])),
                         "https://www.itvedas.com/")
        self.assertIsNone(find(self.Session(["https://other.com/"])))


class TestFullRun(unittest.TestCase):
    """The whole agent against a throwaway site with fake Google + Claude."""

    URL = "https://www.itvedas.com/articles/2026-07-05-networking"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "articles").mkdir()
        (self.root / "chapters").mkdir()
        (self.root / "itvedas-brain" / "state").mkdir(parents=True)
        self.page = self.root / "articles" / "2026-07-05-networking.html"
        self.page.write_text(PAGE, encoding="utf-8")
        (self.root / "llms.txt").write_text("# ITVedas\n\n## Reference\n\n- x\n", encoding="utf-8")
        (self.root / "itvedas-brain" / "state" / "state.json").write_text(json.dumps({
            "published": [{"file": "2026-07-05-networking.html", "keyword": "what is DNS", "topic": "Networking"}],
            "used_keywords": ["what is DNS"]}), encoding="utf-8")
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def gsc(self, start, end, dimensions, page_filter=None):
        self.calls.append((start, end, tuple(dimensions), page_filter))
        if page_filter:
            return [row(self.URL, self.after[0], self.after[1], 4.0)]
        if dimensions == ["page"]:
            return [row(self.URL, 4, 2000, 4.0)]
        return [row(self.URL, 3, 1500, 4.0, "what is dns and how does it work"),
                row(self.URL, 0, 300, 11.0, "dns lookup steps explained"),
                row(self.URL, 0, 200, 30.0, "how to flush dns cache on windows")]

    @staticmethod
    def ga4(start, end, dimensions, metrics):
        if dimensions == ["sessionSource"]:
            return [{"sessionSource": "chatgpt.com", "sessions": 12.0}, {"sessionSource": "google", "sessions": 300.0}]
        return [{"sessionDefaultChannelGroup": "Organic Search", "sessions": 300.0},
                {"sessionDefaultChannelGroup": "Direct", "sessions": 100.0}]

    @staticmethod
    def llm(prompt, schema):
        if "keywords" in schema["properties"]:
            return {"keywords": [
                {"keyword": "how to flush dns cache on windows", "topic": "Networking", "reason": "gap"},
                {"keyword": "what is dns", "topic": "Networking", "reason": "duplicate, must be dropped"}]}
        return {"title": GOOD_TITLE, "description": GOOD_DESC, "reason": "leads with the query"}

    def state(self, name):
        return json.loads((self.root / "itvedas-brain" / "state" / name).read_text(encoding="utf-8"))

    def test_dry_run_changes_nothing(self):
        summary = agent.run(self.root, TODAY, self.gsc, self.ga4, self.llm, dry_run=True)
        self.assertEqual(len(summary["applied"]), 1)
        self.assertEqual(self.page.read_text(encoding="utf-8"), PAGE)
        self.assertFalse((self.root / "itvedas-brain" / "state" / "growth_state.json").exists())
        self.assertNotIn(G.LLMS_HEADING, (self.root / "llms.txt").read_text(encoding="utf-8"))
        self.assertIn("DRY RUN", G.render_report(summary))

    def test_live_run_rewrites_queues_and_reports(self):
        summary = agent.run(self.root, TODAY, self.gsc, self.ga4, self.llm)
        head = G.read_head(self.page.read_text(encoding="utf-8"))
        self.assertEqual((head["title"], head["suffix"]), (GOOD_TITLE, " | ITVedas"))
        change = self.state("growth_state.json")["changes"][0]
        self.assertEqual((change["status"], change["old_title"]), ("pending", "Old DNS Title"))
        queue = self.state("growth_queue.json")
        self.assertEqual([k["keyword"] for k in queue["keywords"]], ["how to flush dns cache on windows"])
        # The page just had its title changed, so it is not also queued for a refresh.
        self.assertEqual(queue["refresh"], [])
        self.assertEqual(summary["ga4"]["ai"], 12.0)
        self.assertIn("/articles/2026-07-05-networking.html", summary["touched"])
        self.assertIn(GOOD_TITLE, (self.root / "llms.txt").read_text(encoding="utf-8"))
        report = G.render_report(summary)
        self.assertIn("Sessions from AI assistants | 12", report)
        self.assertIn("how to flush dns cache on windows", report)

        # A second run a week later leaves the page alone (change still being measured).
        again = agent.run(self.root, TODAY + datetime.timedelta(days=7), self.gsc, self.ga4, self.llm)
        self.assertEqual(again["applied"], [])
        self.assertEqual(len(self.state("growth_state.json")["changes"]), 1)

    def _run_then_judge(self, after):
        agent.run(self.root, TODAY, self.gsc, self.ga4, self.llm)
        self.after = after
        return agent.run(self.root, TODAY + datetime.timedelta(days=35), self.gsc, None, None)

    def test_worse_ctr_is_reverted(self):
        summary = self._run_then_judge((1, 2000))   # 0.05% vs 0.2% baseline
        self.assertEqual(summary["judged"][0]["status"], "reverted")
        self.assertEqual(self.page.read_text(encoding="utf-8"), PAGE)
        self.assertEqual(self.state("growth_state.json")["changes"][0]["status"], "reverted")

    def test_better_ctr_is_kept(self):
        summary = self._run_then_judge((60, 2000))
        self.assertEqual(summary["judged"][0]["status"], "kept")
        self.assertEqual(G.read_head(self.page.read_text(encoding="utf-8"))["title"], GOOD_TITLE)

    def test_revert_is_skipped_if_page_was_rewritten_since(self):
        agent.run(self.root, TODAY, self.gsc, self.ga4, self.llm)
        text = self.page.read_text(encoding="utf-8")
        rewritten = G.apply_head(text, "A Completely New Title From The Writer", GOOD_DESC, " | ITVedas")
        self.page.write_text(rewritten, encoding="utf-8")
        self.after = (1, 2000)
        summary = agent.run(self.root, TODAY + datetime.timedelta(days=35), self.gsc, None, None)
        self.assertEqual(summary["judged"][0]["status"], "superseded")
        self.assertEqual(self.page.read_text(encoding="utf-8"), rewritten)

    def test_url_variants_of_one_page_are_rewritten_once(self):
        def gsc(start, end, dimensions, page_filter=None):
            if dimensions == ["page"]:
                return [row(self.URL, 4, 2000, 4.0), row(self.URL + ".html", 2, 1500, 4.0)]
            return []
        summary = agent.run(self.root, TODAY, gsc, None, self.llm, dry_run=True)
        self.assertEqual(len(summary["applied"]), 1)

    def test_bad_rewrite_is_rejected(self):
        summary = agent.run(self.root, TODAY, self.gsc, self.ga4,
                            lambda p, s: {"title": "Buy now!!!", "description": "x", "reason": "r", "keywords": []})
        self.assertEqual(summary["applied"], [])
        self.assertEqual(self.page.read_text(encoding="utf-8"), PAGE)
        self.assertTrue(any("rejected" in s for s in summary["skipped"]))


class TestWriterQueue(unittest.TestCase):
    """content-writer.py takes growth-queue work once its calendar is done."""

    def setUp(self):
        self.writer = _load("content_writer", "content-writer.py")
        self.tmp = tempfile.TemporaryDirectory()
        self.writer.GROWTH_QUEUE_FILE = Path(self.tmp.name) / "growth_queue.json"
        self.writer.score_by_search_interest = lambda keywords: {}
        self.entry = {"file": "2026-07-05-networking.html", "keyword": self.writer.CALENDAR[0][0],
                      "topic": "Networking", "date": "2026-07-05"}
        self.state = {"used_keywords": [k for k, _ in self.writer.CALENDAR], "published": [self.entry]}

    def tearDown(self):
        self.tmp.cleanup()

    def queue(self, data=None):
        if data is not None:
            self.writer.GROWTH_QUEUE_FILE.write_text(json.dumps(data), encoding="utf-8")
        return json.loads(self.writer.GROWTH_QUEUE_FILE.read_text(encoding="utf-8"))

    def test_no_queue_keeps_original_refresh_behaviour(self):
        keyword, _topic, is_refresh, existing = self.writer.pick_keyword(self.state)
        self.assertTrue(is_refresh)
        self.assertIs(existing, self.entry)
        self.assertEqual(keyword, self.entry["keyword"])

    def test_new_topic_first_then_refresh_with_focus_queries(self):
        self.queue({"keywords": [{"keyword": "how to flush dns cache on windows", "topic": "Networking"}],
                    "refresh": [{"file": self.entry["file"], "queries": ["dns lookup steps"]}]})
        self.assertEqual(self.writer.pick_keyword(self.state),
                         ("how to flush dns cache on windows", "Networking", False, None))
        self.assertEqual(self.writer._FOCUS_QUERIES, [])
        self.writer.finish_growth_item("how to flush dns cache on windows", "x.html", False)
        self.assertEqual(self.queue()["keywords"], [])

        keyword, _topic, is_refresh, existing = self.writer.pick_keyword(self.state)
        self.assertEqual((keyword, is_refresh, existing), (self.entry["keyword"], True, self.entry))
        self.assertEqual(self.writer._FOCUS_QUERIES, ["dns lookup steps"])
        self.writer.finish_growth_item(keyword, self.entry["file"], True)
        self.assertEqual(self.queue()["refresh"], [])

    def test_failed_item_is_retried_once_then_dropped(self):
        self.queue({"keywords": [{"keyword": "a brand new topic here", "topic": "Cloud"}], "refresh": []})
        for _ in range(2):
            self.assertEqual(self.writer.pick_keyword(self.state)[0], "a brand new topic here")
        self.assertTrue(self.writer.pick_keyword(self.state)[2])   # falls back to a refresh
        self.assertEqual(self.queue()["keywords"], [])

    def test_already_written_keyword_and_unknown_file_are_ignored(self):
        self.queue({"keywords": [{"keyword": self.writer.CALENDAR[0][0], "topic": "Networking"}],
                    "refresh": [{"file": "not-in-state.html", "queries": ["q"]}]})
        self.assertTrue(self.writer.pick_keyword(self.state)[2])
        self.assertEqual(self.queue(), {"keywords": [], "refresh": []})


if __name__ == "__main__":
    unittest.main()
