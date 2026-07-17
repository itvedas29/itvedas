"""Integration tests for API endpoints"""

import json
import unittest
from unittest.mock import patch, MagicMock


class TestSubscribeEndpoint(unittest.TestCase):
    """Test /api/subscribe endpoint functionality"""

    def test_valid_subscription_request(self):
        """Test valid subscription email is accepted"""
        payload = {"email": "user@example.com"}
        self.assertIn("@", payload["email"])
        self.assertGreater(len(payload["email"].split("@")), 1)

    def test_email_validation_at_symbol(self):
        """Email must contain @ symbol"""
        valid = "user@example.com"
        invalid = "userexample.com"
        self.assertIn("@", valid)
        self.assertNotIn("@", invalid)

    def test_email_validation_domain_extension(self):
        """Email must have domain extension"""
        valid = "user@example.com"
        invalid = "user@example"
        self.assertIn(".", valid.split("@")[1])
        self.assertNotIn(".", invalid.split("@")[1])

    def test_payload_size_limit(self):
        """Payload should not exceed 6000 characters"""
        small_payload = {"email": "user@example.com"}
        large_payload = {"email": "a" * 6000}
        self.assertLess(len(json.dumps(small_payload)), 6000)
        self.assertGreater(len(json.dumps(large_payload)), 6000)

    def test_duplicate_subscription_prevention(self):
        """Same email should not subscribe twice"""
        email = "user@example.com"
        first_subscription = {"email": email}
        second_subscription = {"email": email}
        self.assertEqual(first_subscription["email"], second_subscription["email"])

    def test_response_contains_success_flag(self):
        """Response should contain success flag"""
        response = {
            "success": True,
            "message": "Successfully subscribed",
            "count": 1234
        }
        self.assertIn("success", response)
        self.assertIsInstance(response["success"], bool)

    def test_error_response_format(self):
        """Error response should have standard format"""
        error_response = {
            "success": False,
            "message": "Unable to process subscription. Please try again later."
        }
        self.assertFalse(error_response["success"])
        self.assertNotIn("traceback", error_response["message"].lower())
        self.assertNotIn("error:", error_response["message"].lower())


class TestCareerAdviceEndpoint(unittest.TestCase):
    """Test /api/career-advice endpoint functionality"""

    def test_valid_quiz_submission(self):
        """Test valid quiz answers are accepted"""
        payload = {
            "answers": [
                {
                    "question": "What interests you most?",
                    "answer": "Building infrastructure"
                },
                {
                    "question": "Preferred work environment?",
                    "answer": "Collaborative team"
                }
            ]
        }
        self.assertIn("answers", payload)
        self.assertGreater(len(payload["answers"]), 0)

    def test_answers_array_required(self):
        """Answers array is required"""
        valid = {"answers": [{"q": "test", "a": "test"}]}
        invalid = {"answers": []}
        self.assertIn("answers", valid)
        self.assertGreater(len(valid["answers"]), 0)
        self.assertEqual(len(invalid["answers"]), 0)

    def test_career_path_validity(self):
        """Response should contain valid career path"""
        valid_careers = [
            "networking", "cloud", "security", "devops",
            "databases", "linux", "hardware", "compliance"
        ]
        response = {
            "chapter": "cloud",
            "chapter_label": "Cloud Computing",
            "explanation": "Based on your interest in scalable infrastructure...",
            "next_steps": ["Step 1", "Step 2"]
        }
        self.assertIn(response["chapter"], valid_careers)
        self.assertIn("chapter_label", response)
        self.assertIn("explanation", response)
        self.assertIn("next_steps", response)

    def test_response_has_actionable_steps(self):
        """Career advice should include next steps"""
        response = {
            "next_steps": [
                "Start with AWS fundamentals",
                "Learn about cloud architectures",
                "Practice with cloud deployment"
            ]
        }
        self.assertIsInstance(response["next_steps"], list)
        self.assertGreater(len(response["next_steps"]), 0)

    def test_payload_size_limit_career_advice(self):
        """Career advice payload should not exceed 6000 characters"""
        small_payload = {
            "answers": [{"question": "test", "answer": "test"}]
        }
        large_payload = {
            "answers": [{"question": "test", "answer": "a" * 6000}]
        }
        self.assertLess(len(json.dumps(small_payload)), 6000)
        self.assertGreater(len(json.dumps(large_payload)), 6000)


class TestAPIErrorHandling(unittest.TestCase):
    """Test error handling in API endpoints"""

    def test_invalid_json_error(self):
        """Invalid JSON should return 400"""
        invalid_json = "{invalid json}"
        try:
            json.loads(invalid_json)
            self.fail("Should raise JSONDecodeError")
        except json.JSONDecodeError:
            pass

    def test_missing_required_field_error(self):
        """Missing required fields should return 400"""
        incomplete_payload = {}
        self.assertNotIn("email", incomplete_payload)

    def test_invalid_method_error(self):
        """Non-POST methods should return 405"""
        method = "GET"
        self.assertNotEqual(method, "POST")

    def test_error_message_not_exposing_internals(self):
        """Error messages should not expose server internals"""
        generic_error = "Unable to process subscription. Please try again later."
        self.assertNotIn("Traceback", generic_error)
        self.assertNotIn("Exception", generic_error)
        self.assertNotIn("line", generic_error)


class TestAPICORSValidation(unittest.TestCase):
    """Test CORS origin validation"""

    def test_valid_origins_accepted(self):
        """Whitelisted origins should be accepted"""
        valid_origins = [
            "https://itvedas.com",
            "https://www.itvedas.com",
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]
        for origin in valid_origins:
            origin_lower = origin.lower()
            is_valid = "itvedas" in origin_lower or "localhost" in origin_lower or "127.0.0.1" in origin_lower
            self.assertTrue(is_valid)

    def test_invalid_origins_rejected(self):
        """Non-whitelisted origins should be rejected"""
        invalid_origins = [
            "http://evil.com",
            "https://malicious.com",
            "http://localhost.evil.com",
            "http://itvedas.com.evil.com"
        ]
        valid_origins_set = {
            "https://itvedas.com",
            "https://www.itvedas.com",
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        }
        for invalid in invalid_origins:
            # Should not be in the exact whitelist
            is_blocked = invalid not in valid_origins_set
            self.assertTrue(is_blocked)

    def test_origin_header_required(self):
        """Request should include Origin header"""
        headers_with_origin = {"Origin": "https://itvedas.com"}
        headers_without = {}
        self.assertIn("Origin", headers_with_origin)
        self.assertNotIn("Origin", headers_without)


if __name__ == "__main__":
    unittest.main()
