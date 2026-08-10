// GET  /api/admin/requirement/:id — full enquiry detail
// POST /api/admin/requirement/:id — status change, note, project link, quote

import { json, STATUSES, clean } from '../../../_lib.js';
import { requireAdmin } from '../../../_auth.js';

const PLATFORMS = ['fiverr', 'upwork', 'other'];

export const onRequestGet = requireAdmin(async function (context) {
  const { env, params } = context;
  const id = parseInt(params.id, 10);
  if (!Number.isFinite(id)) return json({ ok: false, error: 'Invalid id.' }, 400);

  try {
    const requirement = await env.DB.prepare(`
      SELECT r.*,
             c.name AS customer_name, c.email AS customer_email, c.phone AS customer_phone,
             c.country AS customer_country, c.preferred_contact,
             co.name AS company_name, co.country AS company_country
        FROM requirements r
        LEFT JOIN customers c ON c.id = r.customer_id
        LEFT JOIN companies co ON co.id = r.company_id
       WHERE r.id = ?`).bind(id).first();

    if (!requirement) return json({ ok: false, error: 'Not found.' }, 404);

    const [categories, attachments, notes, history, project, quotes, emails] = await Promise.all([
      env.DB.prepare('SELECT category FROM requirement_categories WHERE requirement_id = ?').bind(id).all(),
      env.DB.prepare('SELECT id, filename, content_type, size_bytes, created_at FROM requirement_attachments WHERE requirement_id = ? ORDER BY id').bind(id).all(),
      env.DB.prepare(`SELECT n.id, n.body, n.created_at, u.name AS author
                        FROM requirement_notes n LEFT JOIN admin_users u ON u.id = n.admin_user_id
                       WHERE n.requirement_id = ? ORDER BY n.created_at DESC`).bind(id).all(),
      env.DB.prepare('SELECT from_status, to_status, created_at FROM status_history WHERE requirement_id = ? ORDER BY created_at DESC').bind(id).all(),
      env.DB.prepare('SELECT * FROM projects WHERE requirement_id = ? ORDER BY id DESC LIMIT 1').bind(id).first(),
      env.DB.prepare('SELECT id, amount_usd, scope, notes, sent_at, created_at FROM quotes WHERE requirement_id = ? ORDER BY id DESC').bind(id).all(),
      env.DB.prepare('SELECT template, recipient, status, error, created_at FROM email_events WHERE requirement_id = ? ORDER BY created_at DESC').bind(id).all()
    ]);

    return json({
      ok: true,
      requirement,
      categories: (categories.results || []).map(r => r.category),
      attachments: attachments.results || [],
      notes: notes.results || [],
      history: history.results || [],
      project: project || null,
      quotes: quotes.results || [],
      emails: emails.results || []
    });
  } catch (err) {
    console.error('admin/requirement: detail failed', err);
    return json({ ok: false, error: 'Could not load the enquiry.' }, 500);
  }
});

export const onRequestPost = requireAdmin(async function (context) {
  const { env, params, request, data } = context;
  const id = parseInt(params.id, 10);
  if (!Number.isFinite(id)) return json({ ok: false, error: 'Invalid id.' }, 400);

  let payload;
  try {
    payload = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid request body.' }, 400);
  }

  const action = clean(payload.action, 40);
  const adminId = data.adminUser.id;

  try {
    const existing = await env.DB.prepare('SELECT id, status FROM requirements WHERE id = ?').bind(id).first();
    if (!existing) return json({ ok: false, error: 'Not found.' }, 404);

    if (action === 'set_status') {
      const next = clean(payload.status, 30);
      if (!STATUSES.includes(next)) return json({ ok: false, error: 'Unknown status.' }, 400);
      if (next === existing.status) return json({ ok: true, unchanged: true });

      await env.DB.prepare("UPDATE requirements SET status = ?, updated_at = datetime('now') WHERE id = ?")
        .bind(next, id).run();
      await env.DB.prepare('INSERT INTO status_history (requirement_id, from_status, to_status, admin_user_id) VALUES (?,?,?,?)')
        .bind(id, existing.status, next, adminId).run();
      return json({ ok: true, status: next });
    }

    if (action === 'add_note') {
      const body = clean(payload.body, 4000);
      if (!body) return json({ ok: false, error: 'Note cannot be empty.' }, 400);
      await env.DB.prepare('INSERT INTO requirement_notes (requirement_id, admin_user_id, body) VALUES (?,?,?)')
        .bind(id, adminId, body).run();
      return json({ ok: true });
    }

    if (action === 'set_project') {
      const platform = clean(payload.platform, 20);
      if (platform && !PLATFORMS.includes(platform)) {
        return json({ ok: false, error: 'Unknown platform.' }, 400);
      }
      const projectUrl = clean(payload.project_url, 500);
      // Reject anything that isn't an http(s) URL — a stored javascript: URL
      // would become a stored XSS the moment the admin UI renders it as a link.
      if (projectUrl && !/^https?:\/\//i.test(projectUrl)) {
        return json({ ok: false, error: 'Project URL must start with http:// or https://' }, 400);
      }
      const projectRef = clean(payload.project_ref, 120);
      const notes = clean(payload.notes, 2000);
      const priceRaw = payload.agreed_price_usd;
      const price = priceRaw === '' || priceRaw === null || priceRaw === undefined
        ? null : Number(priceRaw);
      if (price !== null && (!Number.isFinite(price) || price < 0)) {
        return json({ ok: false, error: 'Invalid agreed price.' }, 400);
      }
      const startedAt = clean(payload.started_at, 40);

      const current = await env.DB.prepare('SELECT id FROM projects WHERE requirement_id = ? ORDER BY id DESC LIMIT 1').bind(id).first();
      if (current) {
        await env.DB.prepare(
          `UPDATE projects SET platform = ?, project_url = ?, project_ref = ?,
                  agreed_price_usd = ?, notes = ?, started_at = ? WHERE id = ?`
        ).bind(platform || null, projectUrl || null, projectRef || null, price, notes || null, startedAt || null, current.id).run();
      } else {
        await env.DB.prepare(
          `INSERT INTO projects (requirement_id, platform, project_url, project_ref, agreed_price_usd, notes, started_at)
           VALUES (?,?,?,?,?,?,?)`
        ).bind(id, platform || null, projectUrl || null, projectRef || null, price, notes || null, startedAt || null).run();
      }
      return json({ ok: true });
    }

    if (action === 'add_quote') {
      const amountRaw = payload.amount_usd;
      const amount = amountRaw === '' || amountRaw === null || amountRaw === undefined
        ? null : Number(amountRaw);
      if (amount !== null && (!Number.isFinite(amount) || amount < 0)) {
        return json({ ok: false, error: 'Invalid quote amount.' }, 400);
      }
      const scope = clean(payload.scope, 4000);
      const notes = clean(payload.notes, 2000);
      await env.DB.prepare('INSERT INTO quotes (requirement_id, amount_usd, scope, notes) VALUES (?,?,?,?)')
        .bind(id, amount, scope || null, notes || null).run();
      return json({ ok: true });
    }

    return json({ ok: false, error: 'Unknown action.' }, 400);

  } catch (err) {
    console.error('admin/requirement: update failed', err);
    return json({ ok: false, error: 'Could not apply the change.' }, 500);
  }
});
