// GET /api/admin/attachment/:id — streams an attachment from R2.
// Admin-only: customer uploads are never publicly reachable.

import { json } from '../../../_lib.js';
import { requireAdmin } from '../../../_auth.js';

export const onRequestGet = requireAdmin(async function (context) {
  const { env, params } = context;
  const id = parseInt(params.id, 10);
  if (!Number.isFinite(id)) return json({ ok: false, error: 'Invalid id.' }, 400);

  if (!env.ATTACHMENTS) {
    return json({ ok: false, error: 'Attachment storage is not configured.' }, 503);
  }

  const row = await env.DB.prepare(
    'SELECT r2_key, filename, content_type FROM requirement_attachments WHERE id = ?'
  ).bind(id).first();
  if (!row) return json({ ok: false, error: 'Not found.' }, 404);

  const object = await env.ATTACHMENTS.get(row.r2_key);
  if (!object) return json({ ok: false, error: 'File is no longer available.' }, 404);

  // Always download, never render inline — an uploaded SVG or HTML file
  // rendered inline would execute script in the admin's origin.
  const safeName = row.filename.replace(/["\\]/g, '');
  return new Response(object.body, {
    headers: {
      'Content-Type': row.content_type || 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${safeName}"`,
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': 'private, no-store'
    }
  });
});
