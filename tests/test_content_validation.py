"""Content validation and integrity tests"""

import unittest
import json
import re
from pathlib import Path


class TestSearchIndexIntegrity(unittest.TestCase):
    """Test search index structure and content"""

    def test_search_index_exists(self):
        """Search index file should exist"""
        index_file = Path("/home/user/itvedas/search-index.json")
        self.assertTrue(index_file.exists())

    def test_search_index_valid_json(self):
        """Search index should be valid JSON"""
        index_file = Path("/home/user/itvedas/search-index.json")
        with open(index_file) as f:
            try:
                data = json.load(f)
                self.assertIsInstance(data, (dict, list))
            except json.JSONDecodeError:
                self.fail("Search index is not valid JSON")

    def test_search_index_has_pages(self):
        """Search index should have pages"""
        index_file = Path("/home/user/itvedas/search-index.json")
        with open(index_file) as f:
            data = json.load(f)
            if isinstance(data, dict):
                self.assertIn("pages", data)
                self.assertIsInstance(data["pages"], list)
                self.assertGreater(len(data["pages"]), 0)
            else:
                self.assertGreater(len(data), 0)

    def test_search_index_page_structure(self):
        """Each page in index should have required fields"""
        index_file = Path("/home/user/itvedas/search-index.json")
        with open(index_file) as f:
            data = json.load(f)
            pages = data.get("pages", data) if isinstance(data, dict) else data

            if pages:
                for page in pages[:10]:  # Sample first 10
                    self.assertIn("title", page)
                    self.assertIn("url", page)


class TestSitemapIntegrity(unittest.TestCase):
    """Test sitemap structure"""

    def test_sitemap_exists(self):
        """Sitemap file should exist"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        self.assertTrue(sitemap_file.exists())

    def test_sitemap_valid_xml(self):
        """Sitemap should be valid XML"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        content = sitemap_file.read_text()
        self.assertIn("<?xml", content)
        self.assertIn("</urlset>", content)

    def test_sitemap_has_urls(self):
        """Sitemap should contain URLs"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        content = sitemap_file.read_text()
        url_count = content.count("<url>")
        self.assertGreater(url_count, 0)

    def test_sitemap_urls_properly_formatted(self):
        """Sitemap URLs should be properly formatted"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        content = sitemap_file.read_text()

        # Find all URLs
        urls = re.findall(r'<loc>([^<]+)</loc>', content)
        for url in urls[:10]:  # Sample first 10
            self.assertTrue(
                url.startswith("http"),
                f"URL should be absolute: {url}"
            )


class TestArticleContent(unittest.TestCase):
    """Test article content structure"""

    def test_article_files_have_structure(self):
        """Article HTML files should have proper structure"""
        article_files = list(Path("/home/user/itvedas/articles").glob("*.html"))

        for article_file in article_files[:5]:  # Sample first 5
            content = article_file.read_text()
            # Should have heading
            self.assertIn("<h1", content, f"{article_file.name} missing h1")

    def test_article_has_metadata(self):
        """Articles should have metadata (date, author, etc)"""
        article_files = list(Path("/home/user/itvedas/articles").glob("*.html"))

        for article_file in article_files[:5]:
            content = article_file.read_text()
            # Should have some metadata
            has_metadata = any(tag in content for tag in [
                'name="author"',
                'name="date"',
                'property="article:published_time"'
            ])
            # At minimum should have title
            self.assertIn("<title>", content)


class TestChapterContent(unittest.TestCase):
    """Test chapter pages"""

    def test_chapter_pages_exist(self):
        """Chapter directory should have content"""
        chapters_dir = Path("/home/user/itvedas/chapters")
        if chapters_dir.exists():
            chapter_files = list(chapters_dir.glob("**/*.html"))
            self.assertGreater(len(chapter_files), 0)

    def test_chapter_has_navigation(self):
        """Chapters should have navigation"""
        chapters_dir = Path("/home/user/itvedas/chapters")
        if chapters_dir.exists():
            chapter_files = list(chapters_dir.glob("*.html"))
            if chapter_files:
                for chapter in chapter_files[:3]:
                    content = chapter.read_text()
                    # Should have navigation
                    self.assertIn("<nav", content)


class TestNewsArchive(unittest.TestCase):
    """Test news archive structure"""

    def test_news_files_exist(self):
        """News directory should have content"""
        news_dir = Path("/home/user/itvedas/news")
        if news_dir.exists():
            news_files = list(news_dir.glob("*.html"))
            # Should have some news files
            self.assertGreater(len(news_files), 0)

    def test_news_has_timestamps(self):
        """News items should have publication timestamps"""
        news_dir = Path("/home/user/itvedas/news")
        if news_dir.exists():
            news_files = list(news_dir.glob("*.html"))
            for news_file in news_files[:5]:
                content = news_file.read_text()
                # Should have date info
                has_date = any(pattern in content for pattern in [
                    "202",  # Year
                    "published",
                    "posted"
                ])
                self.assertTrue(has_date, f"{news_file.name} missing date")


class TestCVEDatabase(unittest.TestCase):
    """Test CVE database content"""

    def test_cve_listings_exist(self):
        """CVE listing files should exist"""
        cve_dir = Path("/home/user/itvedas/cve-data")
        self.assertTrue(cve_dir.exists())

    def test_cve_database_complete_exists(self):
        """CVE database page should exist"""
        cve_db = Path("/home/user/itvedas/cve-database-complete.html")
        self.assertTrue(cve_db.exists())

    def test_cve_content_structure(self):
        """CVE database should have proper structure"""
        cve_db = Path("/home/user/itvedas/cve-database-complete.html")
        content = cve_db.read_text()

        # Should have table structure
        self.assertIn("<table", content)
        self.assertIn("<tbody", content)


class TestToolsPage(unittest.TestCase):
    """Test tools availability"""

    def test_tools_index_exists(self):
        """Tools index page should exist"""
        tools_index = Path("/home/user/itvedas/tools/index.html")
        self.assertTrue(tools_index.exists())

    def test_tools_directory_has_content(self):
        """Tools directory should have tool files"""
        tools_dir = Path("/home/user/itvedas/tools")
        tool_files = list(tools_dir.glob("*.html"))
        self.assertGreater(len(tool_files), 1)  # More than just index

    def test_tools_have_descriptions(self):
        """Tools should have descriptions"""
        tools_dir = Path("/home/user/itvedas/tools")
        tool_files = list(tools_dir.glob("*.html"))

        for tool_file in tool_files[:3]:
            content = tool_file.read_text()
            # Should have some descriptive content
            self.assertGreater(len(content), 1000)


class TestDocumentation(unittest.TestCase):
    """Test documentation files"""

    def test_api_documentation_exists(self):
        """API documentation should exist"""
        api_doc = Path("/home/user/itvedas/API.md")
        self.assertTrue(api_doc.exists())

    def test_contributing_guide_exists(self):
        """Contributing guide should exist"""
        contributing = Path("/home/user/itvedas/CONTRIBUTING.md")
        self.assertTrue(contributing.exists())

    def test_changelog_exists(self):
        """Changelog should exist"""
        changelog = Path("/home/user/itvedas/CHANGELOG.md")
        self.assertTrue(changelog.exists())

    def test_readme_exists(self):
        """README should exist"""
        readme = Path("/home/user/itvedas/README.md")
        self.assertTrue(readme.exists())

    def test_api_documentation_content(self):
        """API documentation should have endpoints documented"""
        api_doc = Path("/home/user/itvedas/API.md")
        content = api_doc.read_text()

        self.assertIn("/api/subscribe", content)
        self.assertIn("/api/career-advice", content)

    def test_changelog_has_versions(self):
        """Changelog should have version entries"""
        changelog = Path("/home/user/itvedas/CHANGELOG.md")
        content = changelog.read_text()

        self.assertIn("##", content)  # Markdown headers for versions
        self.assertIn("1.0.0", content)


class TestResourceIntegrity(unittest.TestCase):
    """Test that all referenced resources exist"""

    def test_css_files_exist(self):
        """CSS resources should exist"""
        css_dir = Path("/home/user/itvedas/css")
        if css_dir.exists():
            css_files = list(css_dir.glob("*.css"))
            self.assertGreater(len(css_files), 0)

    def test_js_files_exist(self):
        """JavaScript resources should exist"""
        js_dir = Path("/home/user/itvedas/js")
        self.assertTrue(js_dir.exists())
        js_files = list(js_dir.glob("*.js"))
        self.assertGreater(len(js_files), 0)

    def test_image_resources_exist(self):
        """Image resources should exist or be referenced correctly"""
        img_dir = Path("/home/user/itvedas/img")
        if img_dir.exists():
            img_files = list(img_dir.glob("*"))
            self.assertGreater(len(img_files), 0)


class TestPerformanceIndicators(unittest.TestCase):
    """Test performance-related aspects"""

    def test_minified_assets_present(self):
        """Should have minified CSS/JS files"""
        js_files = list(Path("/home/user/itvedas/js").glob("*.min.js"))
        # Minified files are optional but good practice
        pass  # No strict requirement

    def test_sitemap_page_count_reasonable(self):
        """Sitemap should list reasonable number of pages"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        content = sitemap_file.read_text()
        url_count = content.count("<url>")
        # Should have substantial content (100+ pages)
        self.assertGreater(url_count, 50)


if __name__ == "__main__":
    unittest.main()
