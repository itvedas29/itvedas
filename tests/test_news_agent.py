import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "itvedas-brain"))
SPEC = importlib.util.spec_from_file_location(
    "news_agent", ROOT / "itvedas-brain" / "news-agent.py"
)
news_agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(news_agent)


class TestNewsTopics(unittest.TestCase):
    def test_classifies_security_and_technical_topics(self):
        cases = {
            "CVE-2026-12345 affects a cloud server": "CVE",
            "Researchers disclose a ransomware attack": "Security",
            "New artificial intelligence model released": "AI",
            "AWS announces serverless cloud update": "Cloud",
            "GitLab adds a new CI/CD deployment feature": "DevOps",
            "PostgreSQL database update improves SQL performance": "Databases",
            "Linux kernel release adds hardware support": "Linux",
            "DNS networking changes reach enterprise routers": "Networking",
            "New processor and GPU hardware announced": "Hardware",
            "NIST compliance guidance updated": "Compliance",
            "Open-source software framework gets a new release": "Software",
            "Technology company announces a new product": "General",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(news_agent.classify(title), expected)

    def test_news_index_surfaces_broad_guide_coverage(self):
        titles = (
            "CVE-2026-12345 affects a cloud server",
            "Researchers disclose a ransomware attack",
            "New artificial intelligence model released",
            "AWS announces serverless cloud update",
            "GitLab adds a new CI/CD deployment feature",
            "PostgreSQL database update improves SQL performance",
            "Linux kernel release adds hardware support",
            "DNS networking changes reach enterprise routers",
            "New processor and GPU hardware announced",
            "NIST compliance guidance updated",
            "Open-source software framework gets a new release",
            "Technology company announces a new product",
        )
        articles = [
            {
                "slug": f"story-{index}",
                "headline": title,
                "summary": "Short summary",
                "topic": news_agent.classify(title),
                "date": "2026-10-11",
            }
            for index, title in enumerate(titles)
        ]
        page = news_agent.build_news_index(articles, "today")
        for href in (
            "/articles/security/",
            "/articles/cve/",
            "/articles/ai-models/",
            "/articles/cloud/",
            "/articles/devops/",
            "/articles/networking/",
            "/articles/databases/",
            "/articles/linux/",
            "/articles/hardware/",
            "/articles/api/",
            "/chapters",
        ):
            with self.subTest(href=href):
                self.assertIn(href, page)
        for topic in {article["topic"] for article in articles}:
            with self.subTest(topic=topic):
                self.assertIn(f'data-t="{topic}"', page)
        self.assertIn("software, networking, databases, Linux and hardware", page)


if __name__ == "__main__":
    unittest.main()
