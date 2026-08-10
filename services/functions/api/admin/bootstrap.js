// POST /api/admin/bootstrap — creates the first admin account.
//
// Gated on a one-time secret (ADMIN_BOOTSTRAP_TOKEN) AND on there being zero
// existing admins, so it can't be replayed to add a rogue account later.
// Unset the secret once the first account exists.

import { json, clean, isValidEmail, hashPassword, checkRateLimit, clientIp } from '../../_lib.js';

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.DB) return json({ ok: false, error: 'Service unavailable.' }, 503);
  if (!env.ADMIN_BOOTSTRAP_TOKEN) {
    return json({ ok: false, error: 'Bootstrap is disabled.' }, 403);
  }

  const rl = await checkRateLimit(env, `bootstrap:${clientIp(request)}`, 5, 3600);
  if (!rl.allowed) return json({ ok: false, error: 'Too many attempts.' }, 429);

  let payload;
  try {
    payload = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid request.' }, 400);
  }

  const token = typeof payload.token === 'string' ? payload.token : '';
  // Length-independent comparison isn't critical here (single-use, rate
  // limited), but the check is cheap.
  if (token.length !== env.ADMIN_BOOTSTRAP_TOKEN.length) {
    return json({ ok: false, error: 'Invalid bootstrap token.' }, 403);
  }
  let diff = 0;
  for (let i = 0; i < token.length; i++) {
    diff |= token.charCodeAt(i) ^ env.ADMIN_BOOTSTRAP_TOKEN.charCodeAt(i);
  }
  if (diff !== 0) return json({ ok: false, error: 'Invalid bootstrap token.' }, 403);

  const existing = await env.DB.prepare('SELECT COUNT(*) AS n FROM admin_users').first();
  if ((existing?.n ?? 0) > 0) {
    return json({ ok: false, error: 'An admin account already exists. Bootstrap is closed.' }, 409);
  }

  const email = clean(payload.email, 254).toLowerCase();
  const name = clean(payload.name, 120);
  const password = typeof payload.password === 'string' ? payload.password : '';

  if (!isValidEmail(email)) return json({ ok: false, error: 'A valid email is required.' }, 400);
  if (password.length < 12) {
    return json({ ok: false, error: 'Password must be at least 12 characters.' }, 400);
  }

  const passwordHash = await hashPassword(password);
  await env.DB.prepare(
    'INSERT INTO admin_users (email, name, password_hash) VALUES (?, ?, ?)'
  ).bind(email, name || null, passwordHash).run();

  return json({ ok: true, message: 'Admin account created. Remove ADMIN_BOOTSTRAP_TOKEN now.' });
}

export async function onRequestGet() {
  return json({ ok: false, error: 'Method not allowed. Use POST.' }, 405);
}
