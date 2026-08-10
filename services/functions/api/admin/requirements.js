// GET /api/admin/requirements — dashboard counts + filtered enquiry list.

import { json, STATUSES, clean } from '../../_lib.js';
import { requireAdmin } from '../../_auth.js';

export const onRequestGet = requireAdmin(async function (context) {
  const { request, env } = context;
  const url = new URL(request.url);

  const status = clean(url.searchParams.get('status'), 30);
  const search = clean(url.searchParams.get('q'), 100);
  const page = Math.max(1, parseInt(url.searchParams.get('page'), 10) || 1);
  const perPage = 25;
  const offset = (page - 1) * perPage;

  if (status && !STATUSES.includes(status)) {
    return json({ ok: false, error: 'Unknown status filter.' }, 400);
  }

  const where = [];
  const params = [];
  if (status) {
    where.push('r.status = ?');
    params.push(status);
  }
  if (search) {
    where.push('(r.reference LIKE ? OR c.name LIKE ? OR c.email LIKE ? OR co.name LIKE ?)');
    const like = `%${search}%`;
    params.push(like, like, like, like);
  }
  const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : '';

  try {
    const counts = await env.DB.prepare(
      'SELECT status, COUNT(*) AS n FROM requirements GROUP BY status'
    ).all();

    const countsByStatus = {};
    for (const s of STATUSES) countsByStatus[s] = 0;
    let total = 0;
    for (const row of counts.results || []) {
      countsByStatus[row.status] = row.n;
      total += row.n;
    }

    const listSql = `
      SELECT r.id, r.reference, r.status, r.budget_range, r.urgency, r.created_at,
             c.name AS customer_name, c.email AS customer_email,
             co.name AS company_name,
             (SELECT GROUP_CONCAT(category, ', ')
                FROM requirement_categories rc WHERE rc.requirement_id = r.id) AS categories
        FROM requirements r
        LEFT JOIN customers c ON c.id = r.customer_id
        LEFT JOIN companies co ON co.id = r.company_id
        ${whereSql}
       ORDER BY r.created_at DESC
       LIMIT ? OFFSET ?`;

    const list = await env.DB.prepare(listSql).bind(...params, perPage, offset).all();

    const filteredCount = await env.DB.prepare(`
      SELECT COUNT(*) AS n
        FROM requirements r
        LEFT JOIN customers c ON c.id = r.customer_id
        LEFT JOIN companies co ON co.id = r.company_id
        ${whereSql}`).bind(...params).first();

    return json({
      ok: true,
      total,
      counts: countsByStatus,
      page,
      perPage,
      matching: filteredCount?.n ?? 0,
      requirements: list.results || []
    });
  } catch (err) {
    console.error('admin/requirements: list failed', err);
    return json({ ok: false, error: 'Could not load enquiries.' }, 500);
  }
});
