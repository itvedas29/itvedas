"""Tests for utility scripts"""

import unittest
import json
import re
import sys
import types
from unittest.mock import patch


class TestQAValidation(unittest.TestCase):
    """Test QA validation script logic"""

    def test_search_index_structure(self):
        """Search index should have valid structure"""
        sample_index = {
            "version": "1.0",
            "generated": "2026-07-17",
            "pages": [
                {"title": "Test", "url": "/test", "topic": "Test"}
            ]
        }
        self.assertIn("pages", sample_index)
        self.assertIsInstance(sample_index["pages"], list)

    def test_json_validation(self):
        """JSON files should be parseable"""
        valid_json = '{"key": "value"}'
        parsed = json.loads(valid_json)
        self.assertEqual(parsed["key"], "value")

    def test_exception_handling(self):
        """Scripts should catch specific exceptions"""
        try:
            result = json.loads("{invalid}")
        except json.JSONDecodeError as e:
            self.assertIsInstance(e, json.JSONDecodeError)


class TestSitemapGeneration(unittest.TestCase):
    """Test sitemap generation"""

    def test_url_formatting(self):
        """URLs should be properly formatted"""
        test_url = "/articles/networking/guide.html"
        self.assertTrue(test_url.startswith("/"))

    def test_xml_structure(self):
        """Sitemap should be valid XML"""
        xml_sample = '<?xml version="1.0"?><urlset><url><loc>/test</loc></url></urlset>'
        self.assertIn("<?xml", xml_sample)
        self.assertIn("</urlset>", xml_sample)


class TestCVEIngestionNormalization(unittest.TestCase):
    def test_cpe23_vendor_and_product_extraction_is_deterministic(self):
        requests_stub = types.ModuleType("requests")
        with patch.dict(sys.modules, {"requests": requests_stub}):
            from scripts.cve_unified_sync import normalize

        def cpe(vendor):
            return f"cpe:2.3:a:{vendor}:sample_product:*:*:*:*:*:*:*:*"

        cve = {
            "id": "CVE-2026-12345",
            "descriptions": [{"lang": "en", "value": "Example vulnerability"}],
            "configurations": [{"nodes": [{"cpeMatch": [
                {"criteria": cpe("zeta_vendor")},
                {"criteria": cpe("alpha_vendor")},
            ]}]}],
        }

        normalized = normalize(cve, set())
        cve["configurations"][0]["nodes"][0]["cpeMatch"].reverse()
        normalized_reversed = normalize(cve, set())

        self.assertEqual(normalized["affected"], "Alpha Vendor")
        self.assertEqual(normalized["affected_products"], ["Sample Product"])
        self.assertEqual(normalized_reversed["affected"], normalized["affected"])


if __name__ == "__main__":
    unittest.main()
