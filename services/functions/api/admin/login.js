// POST /api/admin/login — admin authentication.

import { json, clean, isValidEmail, verifyPassword, checkRateLimit, clientIp } from '../../_lib.js';
import { createSession, sessionCookie } from '../../_auth.js';

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.DB) {
    console.error('admin/login: DB binding missing');
    return json({ ok: false, error: 'Service unavailable.' }, 503);
  }

  // 10 attempts per IP per 15 minutes — enough for a fat-fingered password,
  // far too slow for credential stuffing.
  const rl = await checkRateLimit(env, `login:${clientIp(request)}`, 10, 900);
  if (!rl.allowed) {
    return json({ ok: false, error: 'Too many login attempts. Try again later.' }, 429,
      { 'Retry-After': String(rl.retryAfter) });
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid request.' }, 400);
  }

  const email = clean(payload.email, 254).toLowerCase();
  const password = typeof payload.password === 'string' ? payload.password : '';

  if (!isValidEmail(email) || !password) {
    return json({ ok: false, error: 'Invalid email or password.' }, 401);
  }

  const user = await env.DB.prepare(
    'SELECT id, email, password_hash, is_active FROM admin_users WHERE email = ?'
  ).bind(email).first();

  // Same generic message and a real hash comparison either way — a fast
  // "no such user" path would let an attacker enumerate valid admin emails
  // by response timing.
  const storedHash = user?.password_hash
    || 'pbkdf2$210000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=';
  const passwordOk = await verifyPassword(password, storedHash);

  if (!user || !user.is_active || !passwordOk) {
    return json({ ok: false, error: 'Invalid email or password.' }, 401);
  }

  const { token, maxAge } = await createSession(env, user.id);
  await env.DB.prepare("UPDATE admin_users SET last_login_at = datetime('now') WHERE id = ?")
    .bind(user.id).run();

  return json({ ok: true }, 200, { 'Set-Cookie': sessionCookie(token, maxAge) });
}

export async function onRequestGet() {
  return json({ ok: false, error: 'Method not allowed. Use POST.' }, 405);
}
