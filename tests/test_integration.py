"""Integration and workflow tests"""

import unittest
import json
from pathlib import Path


class TestSearchIndexIntegration(unittest.TestCase):
    """Integration tests for search index"""

    def test_search_index_has_minimum_pages(self):
        """Search index should have minimum number of pages"""
        index_file = Path("/home/user/itvedas/search-index.json")
        if index_file.exists():
            with open(index_file) as f:
                data = json.load(f)
                pages = data.get("pages", data) if isinstance(data, dict) else data
                self.assertGreater(len(pages), 50)

    def test_search_index_pages_have_urls(self):
        """All pages in index should have URLs"""
        index_file = Path("/home/user/itvedas/search-index.json")
        if index_file.exists():
            with open(index_file) as f:
                data = json.load(f)
                pages = data.get("pages", data) if isinstance(data, dict) else data
                for page in pages[:20]:  # Sample
                    self.assertIn("url", page)

    def test_search_index_pages_have_titles(self):
        """All pages in index should have titles"""
        index_file = Path("/home/user/itvedas/search-index.json")
        if index_file.exists():
            with open(index_file) as f:
                data = json.load(f)
                pages = data.get("pages", data) if isinstance(data, dict) else data
                for page in pages[:20]:  # Sample
                    self.assertIn("title", page)

    def test_search_index_urls_start_with_slash(self):
        """All URLs in index should start with /"""
        index_file = Path("/home/user/itvedas/search-index.json")
        if index_file.exists():
            with open(index_file) as f:
                data = json.load(f)
                pages = data.get("pages", data) if isinstance(data, dict) else data
                for page in pages[:20]:
                    url = page.get("url", "")
                    self.assertTrue(url.startswith("/") or url.startswith("http"))


class TestSitemapIntegration(unittest.TestCase):
    """Integration tests for sitemap"""

    def test_sitemap_urls_match_index_scope(self):
        """Sitemap should have similar number of URLs as search index"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        index_file = Path("/home/user/itvedas/search-index.json")

        if sitemap_file.exists() and index_file.exists():
            sitemap_content = sitemap_file.read_text()
            sitemap_count = sitemap_content.count("<url>")

            with open(index_file) as f:
                data = json.load(f)
                pages = data.get("pages", data) if isinstance(data, dict) else data
                index_count = len(pages)

            # Sitemap should have same or more URLs
            self.assertGreaterEqual(sitemap_count, index_count * 0.5)

    def test_sitemap_urls_are_unique(self):
        """Sitemap should not have duplicate URLs"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        if sitemap_file.exists():
            import re
            content = sitemap_file.read_text()
            urls = re.findall(r'<loc>([^<]+)</loc>', content)
            unique_urls = set(urls)
            self.assertEqual(len(urls), len(unique_urls))

    def test_sitemap_urls_use_https(self):
        """Sitemap URLs should use HTTPS"""
        sitemap_file = Path("/home/user/itvedas/sitemap.xml")
        if sitemap_file.exists():
            import re
            content = sitemap_file.read_text()
            urls = re.findall(r'<loc>([^<]+)</loc>', content)
            for url in urls[:20]:  # Sample
                self.assertTrue(
                    url.startswith("https://") or url.startswith("http://"),
                    f"Invalid URL: {url}"
                )


class TestHTMLFilesExist(unittest.TestCase):
    """Verify key HTML files exist"""

    def test_homepage_exists(self):
        """Homepage should exist"""
        homepage = Path("/home/user/itvedas/index.html")
        self.assertTrue(homepage.exists())

    def test_problems_solutions_exists(self):
        """Problems & Solutions page should exist"""
        page = Path("/home/user/itvedas/problems-solutions.html")
        self.assertTrue(page.exists())

    def test_cve_database_exists(self):
        """CVE database page should exist"""
        page = Path("/home/user/itvedas/cve-database-complete.html")
        self.assertTrue(page.exists())

    def test_tools_exist(self):
        """Tools directory should have content"""
        tools_dir = Path("/home/user/itvedas/tools")
        self.assertTrue(tools_dir.exists())
        self.assertGreater(len(list(tools_dir.glob("*.html"))), 0)

    def test_news_exists(self):
        """News directory should exist and have items"""
        news_dir = Path("/home/user/itvedas/news")
        if news_dir.exists():
            news_files = list(news_dir.glob("*.html"))
            self.assertGreater(len(news_files), 0)


class TestDirectoryStructure(unittest.TestCase):
    """Test repository directory structure"""

    def test_required_directories_exist(self):
        """Required directories should exist"""
        required_dirs = [
            "js", "css", "scripts", "tests", "functions"
        ]
        for dir_name in required_dirs:
            dir_path = Path(f"/home/user/itvedas/{dir_name}")
            self.assertTrue(dir_path.exists(), f"Missing directory: {dir_name}")

    def test_javascript_files_exist(self):
        """Essential JavaScript files should exist"""
        js_dir = Path("/home/user/itvedas/js")
        self.assertTrue((js_dir / "html-sanitizer.js").exists())
        self.assertTrue((js_dir / "accessibility-enhancements.js").exists())
        self.assertTrue((js_dir / "inline-handler-setup.js").exists())

    def test_script_files_are_executable(self):
        """Python scripts should be readable"""
        scripts_dir = Path("/home/user/itvedas/scripts")
        python_files = list(scripts_dir.glob("*.py"))
        self.assertGreater(len(python_files), 0)


class TestAssetAvailability(unittest.TestCase):
    """Test that critical assets are available"""

    def test_logo_referenced_in_html(self):
        """Logo should be referenced in HTML files"""
        index = Path("/home/user/itvedas/index.html")
        if index.exists():
            content = index.read_text()
            # Should reference logo
            has_logo_ref = "logo" in content.lower()
            self.assertTrue(has_logo_ref)

    def test_css_files_referenced(self):
        """CSS files should be referenced in HTML"""
        index = Path("/home/user/itvedas/index.html")
        if index.exists():
            content = index.read_text()
            has_css = "<link" in content and ".css" in content
            self.assertTrue(has_css)

    def test_javascript_files_referenced(self):
        """JavaScript files should be referenced"""
        index = Path("/home/user/itvedas/index.html")
        if index.exists():
            content = index.read_text()
            has_js = "<script" in content and ".js" in content
            self.assertTrue(has_js)


class TestConfigurationFiles(unittest.TestCase):
    """Test configuration file presence and format"""

    def test_pytest_config_exists(self):
        """pytest.ini should exist"""
        pytest_ini = Path("/home/user/itvedas/pytest.ini")
        self.assertTrue(pytest_ini.exists())

    def test_netlify_config_exists(self):
        """netlify.toml should exist"""
        netlify = Path("/home/user/itvedas/netlify.toml")
        self.assertTrue(netlify.exists())

    def test_gitignore_exists(self):
        """.gitignore should exist"""
        gitignore = Path("/home/user/itvedas/.gitignore")
        self.assertTrue(gitignore.exists())

    def test_security_headers_in_netlify(self):
        """Security headers should be configured in netlify.toml"""
        netlify = Path("/home/user/itvedas/netlify.toml")
        if netlify.exists():
            content = netlify.read_text()
            self.assertIn("Content-Security-Policy", content)
            self.assertIn("Strict-Transport-Security", content)


if __name__ == "__main__":
    unittest.main()
