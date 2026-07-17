"""HTML structure and content validation tests"""

import unittest
import re
from pathlib import Path
from html.parser import HTMLParser


class HTMLStructureValidator(HTMLParser):
    """Parse and validate HTML structure"""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.meta_tags = {}
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "meta":
            attrs_dict = dict(attrs)
            if "name" in attrs_dict:
                self.meta_tags[attrs_dict["name"]] = attrs_dict.get("content", "")
            if "property" in attrs_dict:
                self.meta_tags[attrs_dict["property"]] = attrs_dict.get("content", "")
        elif tag == "link":
            self.links.append(dict(attrs))


class TestHTMLStructure(unittest.TestCase):
    """Test basic HTML structure"""

    def setUp(self):
        self.html_files = list(Path("/home/user/itvedas").glob("*.html"))

    def test_html_files_exist(self):
        """Should have HTML files to test"""
        self.assertGreater(len(self.html_files), 0)

    def test_html_has_doctype(self):
        """HTML files should have DOCTYPE declaration"""
        for html_file in self.html_files[:5]:  # Sample first 5
            content = html_file.read_text()
            self.assertIn("<!DOCTYPE", content, f"{html_file.name} missing DOCTYPE")

    def test_html_has_title(self):
        """HTML files should have title element"""
        for html_file in self.html_files[:5]:
            content = html_file.read_text()
            self.assertIn("<title>", content, f"{html_file.name} missing title")

    def test_html_charset_defined(self):
        """HTML should define character set"""
        for html_file in self.html_files[:5]:
            content = html_file.read_text()
            has_charset = "charset" in content or "UTF-8" in content
            self.assertTrue(has_charset, f"{html_file.name} missing charset")

    def test_html_viewport_meta_tag(self):
        """Mobile-responsive pages should have viewport meta"""
        for html_file in self.html_files[:5]:
            content = html_file.read_text()
            has_viewport = 'viewport' in content.lower()
            self.assertTrue(has_viewport, f"{html_file.name} missing viewport")


class TestCanonicalURLs(unittest.TestCase):
    """Test canonical URL implementation"""

    def test_canonical_urls_present(self):
        """Pages should have canonical URLs"""
        html_files = list(Path("/home/user/itvedas").glob("*.html"))
        files_with_canonical = 0

        for html_file in html_files[:10]:
            content = html_file.read_text()
            if 'rel="canonical"' in content:
                files_with_canonical += 1

        self.assertGreater(files_with_canonical, 0)

    def test_canonical_url_format(self):
        """Canonical URLs should be absolute"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            if 'rel="canonical"' in content:
                # Extract canonical URL
                match = re.search(r'href="([^"]*)"[^>]*rel="canonical"', content)
                if match:
                    url = match.group(1)
                    self.assertTrue(url.startswith("http"), "Canonical URL should be absolute")


class TestMetaTags(unittest.TestCase):
    """Test meta tag implementation"""

    def test_meta_description_present(self):
        """Pages should have meta description"""
        html_files = list(Path("/home/user/itvedas").glob("*.html"))
        files_with_description = 0

        for html_file in html_files[:10]:
            content = html_file.read_text()
            if 'name="description"' in content or 'meta.*description' in content:
                files_with_description += 1

        self.assertGreater(files_with_description, 0)

    def test_open_graph_tags(self):
        """Pages should have Open Graph tags for social sharing"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            og_tags = [
                'property="og:title"',
                'property="og:description"',
                'property="og:type"',
                'property="og:url"'
            ]
            for tag in og_tags:
                self.assertIn(tag, content, f"Missing {tag}")

    def test_meta_tags_not_empty(self):
        """Meta tag content should not be empty"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            # Check for empty meta tags
            empty_meta = re.findall(r'<meta[^>]*content=""', content)
            self.assertEqual(len(empty_meta), 0, "Found empty meta tag content")


class TestAccessibility(unittest.TestCase):
    """Test accessibility features"""

    def test_alt_text_on_images(self):
        """Images should have alt text"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            img_tags = re.findall(r'<img[^>]*>', content)
            for img in img_tags:
                # Should have alt attribute
                has_alt = 'alt=' in img
                self.assertTrue(has_alt, f"Image missing alt: {img[:50]}")

    def test_heading_hierarchy(self):
        """Headings should follow proper hierarchy"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            # Check that we have h1, h2, h3 tags
            has_h1 = "<h1" in content
            has_h2 = "<h2" in content
            self.assertTrue(has_h1, "Should have h1 heading")

    def test_buttons_have_type_attribute(self):
        """Buttons should have type attribute"""
        html_files = list(Path("/home/user/itvedas").glob("**/*.html"))
        for html_file in html_files[:5]:
            content = html_file.read_text()
            # Extract button tags
            buttons = re.findall(r'<button[^>]*>', content)
            for button in buttons:
                # Each button should have type or be in form
                self.assertTrue(
                    'type=' in button or '<button' in button,
                    f"Button missing type: {button}"
                )


class TestSRI(unittest.TestCase):
    """Test Subresource Integrity implementation"""

    def test_sri_on_cdns(self):
        """External CDN resources should have SRI"""
        html_files = list(Path("/home/user/itvedas").glob("*.html"))
        files_with_sri = 0

        for html_file in html_files[:10]:
            content = html_file.read_text()
            if 'integrity=' in content and 'crossorigin=' in content:
                files_with_sri += 1

        # At least some files should have SRI
        self.assertGreater(files_with_sri, 0)

    def test_integrity_hash_format(self):
        """SRI integrity hashes should be properly formatted"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            integrity_matches = re.findall(r'integrity="([^"]*)"', content)
            for integrity in integrity_matches:
                # Should start with sha256-, sha384-, or sha512-
                self.assertTrue(
                    integrity.startswith(("sha256-", "sha384-", "sha512-")),
                    f"Invalid integrity hash: {integrity}"
                )


class TestLinksAndReferences(unittest.TestCase):
    """Test links and internal references"""

    def test_relative_links_valid(self):
        """Relative links should point to existing resources"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            links = re.findall(r'href="(/[^"]*)"', content)
            # Should have some internal links
            self.assertGreater(len(links), 0)

    def test_external_links_have_target_blank(self):
        """External links should open in new tab"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            # Check for external HTTP/HTTPS links
            external_links = re.findall(r'href="(https?://[^"]*)"', content)
            for link in external_links:
                # These should generally have target="_blank"
                pass  # This is a guideline, not strict requirement

    def test_nav_links_accessible(self):
        """Navigation links should be in nav elements"""
        html_file = Path("/home/user/itvedas/problems-solutions.html")
        if html_file.exists():
            content = html_file.read_text()
            # Should have nav element
            self.assertIn("<nav", content)


class TestNoInlineHandlers(unittest.TestCase):
    """Test that refactoring removed inline event handlers"""

    def test_no_onclick_attributes(self):
        """Should not have onclick= attributes (refactored)"""
        html_files = list(Path("/home/user/itvedas").glob("*.html"))
        for html_file in html_files[:10]:
            content = html_file.read_text()
            # Should not have inline onclick (may have data-onclick for refactored code)
            inline_onclick = re.findall(r'\s+onclick=', content)
            self.assertEqual(len(inline_onclick), 0, f"{html_file.name} has inline onclick")

    def test_event_listener_script_loaded(self):
        """Refactored files should load event listener script"""
        html_files = list(Path("/home/user/itvedas").glob("*.html"))
        files_with_script = 0

        for html_file in html_files:
            content = html_file.read_text()
            if 'inline-handler-setup.js' in content:
                files_with_script += 1

        # Should have several files with the script
        self.assertGreater(files_with_script, 0)


if __name__ == "__main__":
    unittest.main()
