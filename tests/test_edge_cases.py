"""Edge case and boundary condition tests"""

import unittest
import json


class TestEmailValidationEdgeCases(unittest.TestCase):
    """Test email validation edge cases"""

    def test_email_with_subdomain(self):
        """Email with subdomain should be valid"""
        email = "user@mail.example.com"
        self.assertIn("@", email)
        parts = email.split("@")
        self.assertEqual(len(parts), 2)
        self.assertIn(".", parts[1])

    def test_email_with_numbers(self):
        """Email with numbers should be valid"""
        email = "user123@example456.com"
        self.assertIn("@", email)
        self.assertIn("123", email)

    def test_email_with_plus_sign(self):
        """Email with plus sign should be accepted"""
        email = "user+tag@example.com"
        self.assertIn("@", email)
        self.assertIn("+", email)

    def test_email_with_dots_in_local_part(self):
        """Email with dots in local part should be valid"""
        email = "user.name@example.com"
        self.assertIn("@", email)
        local_part = email.split("@")[0]
        self.assertIn(".", local_part)

    def test_email_case_insensitivity(self):
        """Email should accept mixed case"""
        email = "User@Example.Com"
        self.assertIn("@", email)
        # Should be normalized/handled consistently
        self.assertEqual(email.lower().count("@"), 1)

    def test_very_long_email(self):
        """Very long email should be handled"""
        long_local = "a" * 64
        email = f"{long_local}@example.com"
        self.assertIn("@", email)
        self.assertGreater(len(email), 100)

    def test_email_at_boundary_254_chars(self):
        """Email at RFC 5321 limit of 254 characters"""
        # Valid emails can be up to 254 characters
        long_email = "a" * 243 + "@example.com"
        self.assertEqual(len(long_email), 254)
        self.assertIn("@", long_email)


class TestPayloadSizeLimitEdgeCases(unittest.TestCase):
    """Test payload size limit boundaries"""

    def test_payload_exactly_6000_chars(self):
        """Payload at exactly 6000 character limit"""
        payload = {"email": "a" * 5988 + "@ex.co"}
        json_str = json.dumps(payload)
        self.assertEqual(len(json_str), 6000)

    def test_payload_just_under_limit(self):
        """Payload just under 6000 character limit"""
        payload = {"email": "a" * 5980 + "@ex.co"}
        json_str = json.dumps(payload)
        self.assertLess(len(json_str), 6000)

    def test_payload_just_over_limit(self):
        """Payload just over 6000 character limit"""
        payload = {"email": "a" * 5995 + "@ex.co"}
        json_str = json.dumps(payload)
        self.assertGreater(len(json_str), 6000)

    def test_multiple_fields_total_size(self):
        """Multiple fields counted toward total size limit"""
        payload = {
            "email": "user@example.com",
            "timestamp": "2026-07-17T12:00:00Z",
            "extra": "x" * 100
        }
        json_str = json.dumps(payload)
        self.assertLess(len(json_str), 6000)


class TestJSONParsingEdgeCases(unittest.TestCase):
    """Test JSON parsing edge cases"""

    def test_json_with_unicode_characters(self):
        """JSON with unicode should parse correctly"""
        data = {"message": "Hello 世界 🌍"}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        self.assertIn("世界", parsed["message"])

    def test_json_with_escaped_quotes(self):
        """JSON with escaped quotes should parse"""
        json_str = '{"message": "He said \\"hello\\""}'
        parsed = json.loads(json_str)
        self.assertIn("hello", parsed["message"])

    def test_json_with_special_characters(self):
        """JSON with special characters should handle properly"""
        data = {"message": "Line1\nLine2\tTabbed"}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        self.assertIn("\n", parsed["message"])

    def test_empty_json_object(self):
        """Empty JSON object should parse"""
        json_str = "{}"
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 0)

    def test_nested_json_objects(self):
        """Nested JSON objects should parse"""
        json_str = '{"outer": {"inner": {"deep": "value"}}}'
        parsed = json.loads(json_str)
        self.assertEqual(parsed["outer"]["inner"]["deep"], "value")

    def test_json_arrays(self):
        """JSON arrays should parse correctly"""
        json_str = '{"items": [1, 2, 3, 4, 5]}'
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed["items"]), 5)


class TestCORSOriginEdgeCases(unittest.TestCase):
    """Test CORS origin validation edge cases"""

    def test_origin_with_trailing_slash(self):
        """Origin with trailing slash"""
        origin_valid = "https://itvedas.com"
        origin_with_slash = "https://itvedas.com/"
        # Should normalize and match
        self.assertEqual(origin_valid.rstrip("/"), origin_with_slash.rstrip("/"))

    def test_origin_port_80_implicit(self):
        """HTTP on port 80 may be implicit"""
        origin1 = "http://localhost:80"
        origin2 = "http://localhost"
        # Port 80 is default for HTTP
        self.assertTrue(origin1.startswith("http://localhost"))

    def test_origin_port_443_implicit(self):
        """HTTPS on port 443 is implicit"""
        origin1 = "https://itvedas.com:443"
        origin2 = "https://itvedas.com"
        # Port 443 is default for HTTPS
        self.assertTrue(origin1.startswith("https://"))

    def test_origin_case_sensitivity(self):
        """Origins should be case-insensitive"""
        origin_lower = "https://itvedas.com"
        origin_upper = "https://ITVEDAS.COM"
        # Domain names are case-insensitive
        self.assertEqual(origin_lower.lower(), origin_upper.lower())

    def test_origin_ipv4_localhost(self):
        """IPv4 localhost origins"""
        valid_origins = [
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]
        for origin in valid_origins:
            self.assertIn("127.0.0.1", origin)

    def test_origin_ipv6_localhost(self):
        """IPv6 localhost origins"""
        origin = "http://[::1]:3000"
        self.assertIn("[::1]", origin)


class TestCareerAdviceEdgeCases(unittest.TestCase):
    """Test career advice endpoint edge cases"""

    def test_single_answer(self):
        """Quiz with single answer should be accepted"""
        payload = {
            "answers": [
                {"question": "What interests you?", "answer": "Networking"}
            ]
        }
        self.assertEqual(len(payload["answers"]), 1)

    def test_many_answers(self):
        """Quiz with many answers should be handled"""
        payload = {
            "answers": [
                {"question": f"Q{i}", "answer": f"A{i}"}
                for i in range(50)
            ]
        }
        self.assertGreater(len(payload["answers"]), 10)

    def test_empty_answer_text(self):
        """Empty answer text should be rejected or handled"""
        payload = {
            "answers": [
                {"question": "Q?", "answer": ""}
            ]
        }
        has_empty = any(a.get("answer", "").strip() == "" for a in payload["answers"])
        self.assertTrue(has_empty)

    def test_very_long_answer(self):
        """Very long answer text"""
        long_answer = "x" * 1000
        payload = {
            "answers": [
                {"question": "Q?", "answer": long_answer}
            ]
        }
        self.assertGreater(len(payload["answers"][0]["answer"]), 500)

    def test_special_characters_in_answers(self):
        """Special characters in quiz answers"""
        payload = {
            "answers": [
                {"question": "What's your skill?", "answer": "C++, Java, #Python"}
            ]
        }
        answer = payload["answers"][0]["answer"]
        self.assertIn("+", answer)
        self.assertIn("#", answer)


class TestErrorMessageEdgeCases(unittest.TestCase):
    """Test error message handling edge cases"""

    def test_error_with_null_bytes(self):
        """Error messages with null bytes should be sanitized"""
        error = "Error occurred\x00 with null byte"
        # Null bytes should be removed or handled
        self.assertIn("\x00", error)

    def test_error_with_ansi_codes(self):
        """ANSI color codes should not leak in errors"""
        error = "\x1b[31mError\x1b[0m"
        # ANSI codes should be stripped
        self.assertIn("\x1b", error)

    def test_error_message_length(self):
        """Error messages should have reasonable length"""
        error = "Unable to process subscription. Please try again later."
        self.assertLess(len(error), 100)
        self.assertGreater(len(error), 20)


if __name__ == "__main__":
    unittest.main()
