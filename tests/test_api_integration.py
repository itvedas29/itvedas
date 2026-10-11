"""Integration tests for API endpoints."""

import json
import os
import socket
import subprocess
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestCVEApiServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]

        env = os.environ.copy()
        env.update({"HOST": "127.0.0.1", "PORT": str(cls.port), "RATE_LIMIT_PER_MIN": "20"})
        cls.server = subprocess.Popen(
            ["node", str(REPO_ROOT / "api-cve-server.js")],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if cls.server.poll() is not None:
                raise RuntimeError("CVE API server exited during startup")
            try:
                with urlopen(f"{cls.base_url}/api/health", timeout=1):
                    return
            except URLError:
                time.sleep(0.05)
        cls.server.terminate()
        cls.server.wait(timeout=5)
        raise RuntimeError("CVE API server did not become ready")

    @classmethod
    def tearDownClass(cls):
        if cls.server.poll() is None:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait(timeout=5)

    def get_json(self, path):
        with urlopen(f"{self.base_url}{path}", timeout=10) as response:
            return response.status, json.load(response)

    def test_repeated_query_parameters_are_normalized_without_crashing(self):
        search_status, search = self.get_json("/api/cve/search?q=a&q=b")
        filter_status, filtered = self.get_json("/api/cve/filter?affected=a&affected=b")
        health_status, health = self.get_json("/api/health")

        self.assertEqual(search_status, 200)
        self.assertEqual(search["query"], "a")
        self.assertEqual(filter_status, 200)
        self.assertEqual(filtered["filters"]["affected"], "a")
        self.assertEqual(health_status, 200)
        self.assertTrue(health["success"])
        self.assertIsNone(self.server.poll(), "server exited after repeated query requests")


if __name__ == "__main__":
    unittest.main()
