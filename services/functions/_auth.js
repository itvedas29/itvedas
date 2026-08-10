// Admin session handling. Sessions are server-side rows in admin_sessions;
// the cookie carries only an opaque random token, so revoking a session is a
// DELETE rather than a secret rotation.

import { randomToken, json } from './_lib.js';

const COOKIE_NAME = 'itv_admin_session';
const SESSION_TTL_SECONDS = 60 * 60 * 8; // 8 hours

export function sessionCookie(token, maxAge) {
  // HttpOnly so JS can't read it; SameSite=Strict because the admin UI is
  // same-origin only and this removes CSRF exposure on state-changing routes.
  const parts = [
    `${COOKIE_NAME}=${token}`,
    'Path=/',
    'HttpOnly',
    'Secure',
    'SameSite=Strict',
    `Max-Age=${maxAge}`
  ];
  return parts.join('; ');
}

export function clearedSessionCookie() {
  return sessionCookie('', 0);
}

function readCookie(request, name) {
  const header = request.headers.get('Cookie') || '';
  for (const part of header.split(';')) {
    const [k, ...rest] = part.trim().split('=');
    if (k === name) return rest.join('=');
  }
  return null;
}

export async function createSession(env, adminUserId) {
  const token = randomToken();
  const expiresAt = new Date(Date.now() + SESSION_TTL_SECONDS * 1000).toISOString();
  await env.DB.prepare(
    'INSERT INTO admin_sessions (token, admin_user_id, expires_at) VALUES (?, ?, ?)'
  ).bind(token, adminUserId, expiresAt).run();

  // Opportunistic cleanup so expired rows don't accumulate unboundedly.
  await env.DB.prepare("DELETE FROM admin_sessions WHERE expires_at < datetime('now')").run();

  return { token, maxAge: SESSION_TTL_SECONDS };
}

export async function destroySession(env, request) {
  const token = readCookie(request, COOKIE_NAME);
  if (token) {
    await env.DB.prepare('DELETE FROM admin_sessions WHERE token = ?').bind(token).run();
  }
}

// Returns the admin user row, or null. Expiry is enforced in SQL so a stale
// cookie can never authenticate even if the cleanup pass hasn't run.
export async function getSessionUser(env, request) {
  if (!env.DB) return null;
  const token = readCookie(request, COOKIE_NAME);
  if (!token) return null;

  return await env.DB.prepare(
    `SELECT u.id, u.email, u.name
       FROM admin_sessions s
       JOIN admin_users u ON u.id = s.admin_user_id
      WHERE s.token = ?
        AND s.expires_at > datetime('now')
        AND u.is_active = 1`
  ).bind(token).first();
}

// Wraps an admin API handler, rejecting unauthenticated requests with 401.
export function requireAdmin(handler) {
  return async function (context) {
    const user = await getSessionUser(context.env, context.request);
    if (!user) {
      return json({ ok: false, error: 'Not authenticated.' }, 401);
    }
    context.data = context.data || {};
    context.data.adminUser = user;
    return handler(context);
  };
}
