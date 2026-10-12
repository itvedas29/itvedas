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
let forwarded;
globalThis.fetch = async (url, options) => {
    assert.equal(url, 'https://script.google.com/macros/s/test/exec');
    forwarded = JSON.parse(options.body);
    return Response.json({ success: true });
};
const env = {
    GOOGLE_SHEETS_WEB_APP_URL: 'https://script.google.com/macros/s/test/exec',
    GOOGLE_SHEETS_WEBHOOK_SECRET: 'test-secret',
    SUBSCRIBE_RATE_LIMIT: {
        get: async key => values.get(key) ?? null,
        put: async (key, value) => values.set(key, value)
    }
};

async function post(email, ip, origin = 'https://itvedas.com', consent = true) {
    const request = new Request('https://itvedas.com/api/subscribe', {
        method: 'POST',
        headers: { Origin: origin, 'CF-Connecting-IP': ip, 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, consent })
    });
    return onRequestPost({ request, env });
}

const accepted = await post('User@example.com', '192.0.2.1');
assert.equal(accepted.status, 200);
assert.equal((await accepted.json()).success, true);
assert.equal(forwarded.email, 'User@example.com');
assert.equal(forwarded.secret, 'test-secret');
assert.equal(forwarded.source, 'homepage-newsletter');
globalThis.fetch = async () => Response.json({ success: false, code: 'already_subscribed' });
const mappedDuplicateResponse = await post('user@example.com', '192.0.2.3');
assert.equal(mappedDuplicateResponse.status, 409);
const invalid = await post('not-an-email', '192.0.2.3');
assert.equal(invalid.status, 400);
const noConsent = await post('other@example.com', '192.0.2.4', 'https://itvedas.com', false);
assert.equal(noConsent.status, 400);
const blocked = await post('other@example.com', '192.0.2.5', 'https://evil.example');
assert.equal(blocked.status, 403);
const noConfig = await onRequestPost({
    request: new Request('https://itvedas.com/api/subscribe', {
        method: 'POST',
        headers: { Origin: 'https://itvedas.com', 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'missing@example.com', consent: true })
    }),
    env: {}
});
assert.equal(noConfig.status, 503);
console.log('subscribe handler checks passed');
"""


class SubscribeAPITests(unittest.TestCase):
    """Black-box tests for the newsletter Cloudflare function."""

    def test_handler_validation_forwarding_and_configuration(self):
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
