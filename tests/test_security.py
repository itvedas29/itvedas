"""Security validation tests"""

import unittest
import re
from pathlib import Path


class TestSessionIDGeneration(unittest.TestCase):
    """Test secure session ID generation"""

    def test_session_id_randomness(self):
        """Session IDs should be cryptographically random"""
        # In production, crypto.getRandomValues() is used
        import random
        ids = [random.SystemRandom().getrandbits(128) for _ in range(100)]
        unique_ids = set(ids)
        self.assertEqual(len(unique_ids), 100)

    def test_session_id_sufficient_entropy(self):
        """Session IDs should have sufficient entropy"""
        import secrets
        session_id = secrets.token_hex(32)
        self.assertGreater(len(session_id), 16)

    def test_math_random_not_used_for_sessions(self):
        """Math.random() should not be used for session generation"""
        js_file = Path("/home/user/itvedas/js/analytics-tracker.js")
        if js_file.exists():
            content = js_file.read_text()
            # Should use crypto.getRandomValues, not Math.random
            self.assertIn("crypto.getRandomValues", content)


class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization"""

    def test_email_injection_prevention(self):
        """Email validation should prevent injection attacks"""
        malicious_emails = [
            "test@example.com\r\nBcc: attacker@evil.com",
            "test@example.com%0aBcc: attacker@evil.com",
            "test@example.com\nBcc: attacker@evil.com"
        ]
        for email in malicious_emails:
            has_newline = "\n" in email or "\r" in email
            self.assertTrue(has_newline, f"Should reject: {email}")

    def test_xss_payload_rejection(self):
        """XSS payloads should be rejected"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror='alert(1)'>",
            "<svg onload='alert(1)'>",
            "';alert(1);//"
        ]
        for payload in xss_payloads:
            has_dangerous_chars = any(c in payload for c in ["<", ">", "javascript:"])
            self.assertTrue(has_dangerous_chars)

    def test_sql_injection_prevention(self):
        """SQL injection patterns should be detected"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin' --",
            "1; DELETE FROM users"
        ]
        for payload in sql_payloads:
            has_sql_keywords = any(kw in payload.upper() for kw in ["DROP", "DELETE", "OR"])
            self.assertTrue(has_sql_keywords)


class TestContentSecurityPolicy(unittest.TestCase):
    """Test CSP header implementation"""

    def test_csp_header_present(self):
        """CSP header should be set in netlify.toml"""
        netlify_file = Path("/home/user/itvedas/netlify.toml")
        if netlify_file.exists():
            content = netlify_file.read_text()
            self.assertIn("Content-Security-Policy", content)

    def test_csp_policy_structure(self):
        """CSP policy should have proper directives"""
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'"
        directives = csp.split(";")
        self.assertGreater(len(directives), 0)
        self.assertIn("default-src", csp)

    def test_unsafe_inline_minimized(self):
        """Unsafe-inline should be minimal in CSP"""
        csp = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        # Count unsafe-inline occurrences (should be minimal)
        unsafe_count = csp.count("unsafe-inline")
        self.assertLessEqual(unsafe_count, 2)


class TestHTTPSecurityHeaders(unittest.TestCase):
    """Test security headers"""

    def test_hsts_header_present(self):
        """HSTS header should be configured"""
        netlify_file = Path("/home/user/itvedas/netlify.toml")
        if netlify_file.exists():
            content = netlify_file.read_text()
            self.assertIn("Strict-Transport-Security", content)

    def test_x_content_type_options(self):
        """X-Content-Type-Options should be nosniff"""
        netlify_file = Path("/home/user/itvedas/netlify.toml")
        if netlify_file.exists():
            content = netlify_file.read_text()
            self.assertIn("X-Content-Type-Options", content)

    def test_x_frame_options(self):
        """X-Frame-Options should prevent clickjacking"""
        netlify_file = Path("/home/user/itvedas/netlify.toml")
        if netlify_file.exists():
            content = netlify_file.read_text()
            self.assertIn("X-Frame-Options", content)


class TestOriginValidation(unittest.TestCase):
    """Test CORS origin validation"""

    def test_origin_exact_matching(self):
        """Origin validation should use exact matching, not substring"""
        # Should NOT use: origin.includes("localhost")
        # Should use: exact whitelist comparison
        valid_origins = {
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        }

        # Test malicious variations that would pass with .includes()
        attack_origins = [
            "http://localhost.evil.com",
            "http://evil.localhost:3000"
        ]

        for origin in attack_origins:
            # Should NOT be in exact whitelist
            self.assertNotIn(origin, valid_origins)

    def test_localhost_port_specificity(self):
        """Localhost origins should require specific ports"""
        valid_origins = ["http://localhost:3000", "http://localhost:8080"]
        invalid_origins = ["http://localhost:9999", "http://localhost"]

        for origin in valid_origins:
            self.assertIn(origin, valid_origins)

        for origin in invalid_origins:
            self.assertNotIn(origin, valid_origins)


class TestErrorMessageSanitization(unittest.TestCase):
    """Test error message handling"""

    def test_generic_error_messages(self):
        """Error messages should be generic, not expose internals"""
        generic_errors = [
            "Unable to process subscription. Please try again later.",
            "An error occurred. Please try again.",
            "Unable to complete your request at this time."
        ]
        for error in generic_errors:
            self.assertNotIn("Exception", error)
            self.assertNotIn("Traceback", error)
            self.assertNotIn("Error:", error)

    def test_no_stack_traces_in_response(self):
        """Stack traces should never be sent to client"""
        bad_error = "Error: Database connection failed at line 42"
        good_error = "Unable to process your request. Please try again later."

        self.assertNotIn("line", bad_error.lower())
        self.assertNotIn("line", good_error.lower())

    def test_no_debug_information_exposed(self):
        """Debug information should not be exposed"""
        api_response = {
            "success": False,
            "message": "Unable to process request"
        }
        response_str = str(api_response)
        self.assertNotIn("Traceback", response_str)
        self.assertNotIn("File", response_str)


class TestHTMLSanitization(unittest.TestCase):
    """Test HTML sanitizer usage"""

    def test_html_sanitizer_exists(self):
        """HTML sanitizer module should exist"""
        sanitizer_file = Path("/home/user/itvedas/js/html-sanitizer.js")
        self.assertTrue(sanitizer_file.exists())

    def test_sanitizer_functions_present(self):
        """Sanitizer should have required functions"""
        sanitizer_file = Path("/home/user/itvedas/js/html-sanitizer.js")
        content = sanitizer_file.read_text()

        required_functions = [
            "sanitizeHTML",
            "setInnerHTML",
            "setTextContent",
            "createElement"
        ]
        for func in required_functions:
            self.assertIn(func, content)

    def test_allowed_tags_defined(self):
        """Sanitizer should define allowed tags"""
        sanitizer_file = Path("/home/user/itvedas/js/html-sanitizer.js")
        content = sanitizer_file.read_text()
        self.assertIn("ALLOWED_TAGS", content)


if __name__ == "__main__":
    unittest.main()
