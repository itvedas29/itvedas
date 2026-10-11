"""Tests for subscribe API endpoint"""

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

NODE_HANDLER_TEST = r"""
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { readFile } from 'node:fs/promises';

if (!globalThis.crypto) Object.defineProperty(globalThis, 'crypto', { value: webcrypto });
const source = await readFile('functions/api/subscribe.js', 'utf8');
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const { onRequestPost } = await import(moduleUrl);
const values = new Map();
const env = { SUBSCRIBERS: {
    get: async key => values.get(key) ?? null,
    put: async (key, value) => values.set(key, value)
} };

async function post(email, ip, origin = 'https://itvedas.com') {
    const request = new Request('https://itvedas.com/api/subscribe', {
        method: 'POST',
        headers: { Origin: origin, 'CF-Connecting-IP': ip, 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    return onRequestPost({ request, env });
}

const accepted = await post('User@example.com', '192.0.2.1');
assert.equal(accepted.status, 200);
assert.equal((await accepted.json()).success, true);
const duplicate = await post('user@example.com', '192.0.2.2');
assert.equal(duplicate.status, 400);
assert.equal((await duplicate.json()).message, 'Already subscribed');
const invalid = await post('not-an-email', '192.0.2.3');
assert.equal(invalid.status, 400);
const blocked = await post('other@example.com', '192.0.2.4', 'https://evil.example');
assert.equal(blocked.status, 403);
console.log('subscribe handler checks passed');
"""


class SubscribeAPITests(unittest.TestCase):
    """Black-box tests for the newsletter Cloudflare function."""

    def test_handler_validation_duplicate_and_origin(self):
        result = subprocess.run(
            ["node", "--input-type=module", "-e", NODE_HANDLER_TEST],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("subscribe handler checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
