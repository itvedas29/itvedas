// Shared helpers for ITVedas Services Pages Functions.
// Files prefixed with _ are not routed by Cloudflare Pages, so this is
// importable server-side code, not a public endpoint.

export const CATEGORIES = [
  'microsoft-365', 'google-workspace', 'windows-support', 'macos-jamf',
  'endpoint-management', 'cybersecurity', 'active-directory',
  'patch-management', 'it-migration', 'remote-it-support',
  'it-asset-management', 'other'
];

export const BUDGETS = [
  'under-50', '50-100', '100-250', '250-500', '500-1000', '1000-plus', 'not-sure'
];

export const URGENCIES = ['normal', 'soon', 'urgent', 'critical'];

export const STATUSES = [
  'new', 'reviewing', 'contacted', 'qualified', 'quoted',
  'fiverr_upwork', 'in_progress', 'completed', 'follow_up', 'cancelled'
];

export const MAX_ATTACHMENTS = 3;
export const MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024; // 5 MB each
export const ALLOWED_ATTACHMENT_TYPES = [
  'image/png', 'image/jpeg', 'image/gif', 'image/webp',
  'application/pdf', 'text/plain', 'text/csv'
];

export function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      ...extraHeaders
    }
  });
}

export function badRequest(message, field) {
  return json({ ok: false, error: message, field }, 400);
}

// Trims, coerces to string, enforces a max length. Returns '' for nullish.
// Every value written to D1 goes through this — parameterized queries handle
// SQL injection, this bounds the size and keeps types predictable.
export function clean(value, maxLen = 500) {
  if (value === null || value === undefined) return '';
  const s = String(value).trim();
  return s.length > maxLen ? s.slice(0, maxLen) : s;
}

export function isValidEmail(email) {
  if (typeof email !== 'string') return false;
  if (email.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
}

// ITV-XXXXXX using an unambiguous alphabet (no O/0/I/1) so references are
// easy to read out over a call without transcription errors.
const REF_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
export function generateReference() {
  const bytes = crypto.getRandomValues(new Uint8Array(6));
  let out = '';
  for (const b of bytes) out += REF_ALPHABET[b % REF_ALPHABET.length];
  return `ITV-${out}`;
}

export function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

// --- password hashing (PBKDF2-SHA256, WebCrypto only — no deps) ------------

// 100,000 is the HARD CEILING imposed by the Cloudflare Workers runtime, not a
// tuning choice. This was 210,000; every login and the admin bootstrap threw
//
//   NotSupportedError: Pbkdf2 failed: iteration counts above 100000 are not
//   supported (requested 210000)
//
// and returned HTTP 500. Local `wrangler dev` does NOT enforce the cap, so it
// only surfaced against real infrastructure. Do not raise this value — it will
// break authentication in production while continuing to pass locally.
//
// 100k is below OWASP's current PBKDF2-SHA256 guidance (600k). Since the
// platform forbids reaching that, the compensating controls are: login is rate
// limited to 10 attempts per 15 minutes per IP, accounts are few and operator-
// created, and passwords are long random strings rather than user-chosen. If
// stronger stretching is ever needed, chain several deriveBits passes (each
// under the cap) rather than raising this constant.
//
// verifyPassword reads the iteration count out of the stored hash, so existing
// hashes at any count keep verifying and a future change stays backward
// compatible.
const PBKDF2_ITERATIONS = 100000;

function b64encode(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)));
}
function b64decode(str) {
  return Uint8Array.from(atob(str), c => c.charCodeAt(0));
}

// A syntactically-valid hash that verifyPassword will run a real PBKDF2
// comparison against and correctly reject, used as the comparison target for
// logins against an email that doesn't exist — so "wrong password" and
// "no such user" cost the same CPU time and return the same response,
// closing the timing side-channel that would otherwise let an attacker
// enumerate valid admin emails.
//
// Built from PBKDF2_ITERATIONS rather than a hand-written literal: a hand-
// written copy is exactly what went stale here before. This constant was
// hardcoded at 210000 in login.js while PBKDF2_ITERATIONS was corrected to
// 100000 elsewhere, so it kept exceeding the Workers PBKDF2 cap — meaning
// every login attempt against an unregistered email threw NotSupportedError
// and returned 500 instead of 401. Confirmed in production: 6 consecutive
// failed logins against a nonexistent address returned 500 before the rate
// limiter's 429 ever engaged. Deriving it from the constant makes that class
// of drift impossible.
export const DUMMY_PASSWORD_HASH =
  `pbkdf2$${PBKDF2_ITERATIONS}$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=`;

export async function hashPassword(password, saltBytes) {
  const salt = saltBytes || crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    key, 256
  );
  return `pbkdf2$${PBKDF2_ITERATIONS}$${b64encode(salt)}$${b64encode(bits)}`;
}

export async function verifyPassword(password, stored) {
  if (typeof stored !== 'string') return false;
  const parts = stored.split('$');
  if (parts.length !== 4 || parts[0] !== 'pbkdf2') return false;
  const iterations = parseInt(parts[1], 10);
  if (!Number.isFinite(iterations) || iterations < 1000) return false;

  let salt, expected;
  try {
    salt = b64decode(parts[2]);
    expected = b64decode(parts[3]);
  } catch {
    return false;
  }

  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']
  );
  const bits = new Uint8Array(await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    key, expected.length * 8
  ));

  // Constant-time compare — a length-varying or early-exit compare leaks
  // information about the stored hash across many login attempts.
  if (bits.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < bits.length; i++) diff |= bits[i] ^ expected[i];
  return diff === 0;
}

// --- rate limiting ---------------------------------------------------------

// KV-backed fixed-window counter. Not perfectly precise under concurrency,
// but enough to stop scripted abuse of the public form and login endpoint.
export async function checkRateLimit(env, key, limit, windowSeconds) {
  if (!env.RATE_LIMIT) return { allowed: true }; // KV not bound — fail open, logged by caller
  const now = Math.floor(Date.now() / 1000);
  const bucket = Math.floor(now / windowSeconds);
  const k = `rl:${key}:${bucket}`;
  const current = parseInt(await env.RATE_LIMIT.get(k), 10) || 0;
  if (current >= limit) {
    return { allowed: false, retryAfter: (bucket + 1) * windowSeconds - now };
  }
  await env.RATE_LIMIT.put(k, String(current + 1), { expirationTtl: windowSeconds * 2 });
  return { allowed: true };
}

export function clientIp(request) {
  return request.headers.get('CF-Connecting-IP') || 'unknown';
}

// --- email -----------------------------------------------------------------

// Sends via Resend if configured. Returns a {status, error} record which the
// caller logs to email_events — a failed notification must never fail the
// customer's submission, so this always resolves rather than throwing.
export async function sendEmail(env, { to, subject, html, replyTo }) {
  if (!env.RESEND_API_KEY || !env.EMAIL_FROM) {
    return { status: 'skipped', error: 'email not configured' };
  }
  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: env.EMAIL_FROM,
        to: [to],
        subject,
        html,
        ...(replyTo ? { reply_to: replyTo } : {})
      })
    });
    if (!res.ok) {
      const text = await res.text();
      return { status: 'failed', error: `${res.status}: ${text.slice(0, 200)}` };
    }
    return { status: 'sent', error: null };
  } catch (err) {
    return { status: 'failed', error: String(err).slice(0, 200) };
  }
}

// Escapes untrusted values before they're interpolated into email HTML.
export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
