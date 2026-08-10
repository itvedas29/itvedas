// GET /api/admin/session — who am I? Used by the admin UI to decide whether
// to render the dashboard or bounce to the login screen.

import { json } from '../../_lib.js';
import { getSessionUser } from '../../_auth.js';

export async function onRequestGet(context) {
  const user = await getSessionUser(context.env, context.request);
  if (!user) return json({ ok: false, authenticated: false }, 401);
  return json({ ok: true, authenticated: true, user: { email: user.email, name: user.name } });
}
