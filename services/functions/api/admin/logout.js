// POST /api/admin/logout — destroys the server-side session row.

import { json } from '../../_lib.js';
import { destroySession, clearedSessionCookie } from '../../_auth.js';

export async function onRequestPost(context) {
  const { request, env } = context;
  if (env.DB) {
    try {
      await destroySession(env, request);
    } catch (err) {
      console.error('admin/logout: could not delete session', err);
    }
  }
  return json({ ok: true }, 200, { 'Set-Cookie': clearedSessionCookie() });
}

export async function onRequestGet() {
  return json({ ok: false, error: 'Method not allowed. Use POST.' }, 405);
}
