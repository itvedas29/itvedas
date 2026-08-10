// POST /api/requirements — public IT requirement submission.
//
// Accepts multipart/form-data (so attachments can ride along in one request).
// Every field is re-validated here; the client-side wizard's validation is
// purely a UX affordance and is assumed to be bypassable.

import {
  CATEGORIES, BUDGETS, URGENCIES,
  MAX_ATTACHMENTS, MAX_ATTACHMENT_BYTES, ALLOWED_ATTACHMENT_TYPES,
  json, badRequest, clean, isValidEmail, generateReference,
  checkRateLimit, clientIp, sendEmail, escapeHtml
} from '../_lib.js';

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.DB) {
    console.error('requirements: DB binding missing');
    return json({ ok: false, error: 'Service temporarily unavailable. Please try again later.' }, 503);
  }

  // 5 submissions per IP per hour. A real prospect submits once; anything
  // above this is scripted.
  const ip = clientIp(request);
  const rl = await checkRateLimit(env, `req:${ip}`, 5, 3600);
  if (!rl.allowed) {
    return json(
      { ok: false, error: 'Too many submissions. Please try again later.' },
      429,
      { 'Retry-After': String(rl.retryAfter) }
    );
  }

  let form;
  try {
    form = await request.formData();
  } catch {
    return badRequest('Could not read the submitted form.');
  }

  // Honeypot — a field hidden from humans via CSS. Bots fill it in.
  // Returning a normal-looking success avoids telling the bot it was caught.
  if (clean(form.get('website'), 100)) {
    return json({ ok: true, reference: generateReference() });
  }

  // --- validate ------------------------------------------------------------

  const categories = form.getAll('categories')
    .map(c => clean(c, 50))
    .filter(c => CATEGORIES.includes(c));
  if (categories.length === 0) {
    return badRequest('Select at least one category.', 'categories');
  }

  const description = clean(form.get('description'), 5000);
  if (description.length < 20) {
    return badRequest('Please describe your requirement in a little more detail (at least 20 characters).', 'description');
  }

  const budget = clean(form.get('budget'), 30);
  if (budget && !BUDGETS.includes(budget)) {
    return badRequest('Invalid budget selection.', 'budget');
  }

  const urgency = clean(form.get('urgency'), 20) || 'normal';
  if (!URGENCIES.includes(urgency)) {
    return badRequest('Invalid urgency selection.', 'urgency');
  }

  const name = clean(form.get('name'), 120);
  if (!name) return badRequest('Your name is required.', 'name');

  const email = clean(form.get('email'), 254);
  if (!isValidEmail(email)) return badRequest('A valid email address is required.', 'email');

  const companyName = clean(form.get('company'), 160);
  const country = clean(form.get('country'), 80);
  const phone = clean(form.get('phone'), 40);
  const preferredContact = clean(form.get('preferred_contact'), 30);
  const extraMessage = clean(form.get('extra_message'), 2000);

  const env_users = clean(form.get('users_count'), 30);
  const env_devices = clean(form.get('devices_count'), 30);
  const env_windows = clean(form.get('windows_devices'), 30);
  const env_mac = clean(form.get('mac_devices'), 30);
  const env_suite = clean(form.get('productivity_suite'), 40);
  const env_endpoint = clean(form.get('endpoint_solution'), 120);
  const env_other = clean(form.get('other_technology'), 300);

  const source = clean(form.get('source'), 200);
  const ipCountry = request.headers.get('CF-IPCountry') || '';

  // --- validate attachments before writing anything ------------------------

  const files = form.getAll('attachments').filter(f => f && typeof f === 'object' && 'size' in f && f.size > 0);
  if (files.length > MAX_ATTACHMENTS) {
    return badRequest(`Please attach no more than ${MAX_ATTACHMENTS} files.`, 'attachments');
  }
  for (const file of files) {
    if (file.size > MAX_ATTACHMENT_BYTES) {
      return badRequest(`"${file.name}" is larger than 5 MB.`, 'attachments');
    }
    if (!ALLOWED_ATTACHMENT_TYPES.includes(file.type)) {
      return badRequest(`"${file.name}" is not an accepted file type. Allowed: images, PDF, TXT, CSV.`, 'attachments');
    }
  }

  // --- persist -------------------------------------------------------------

  try {
    let companyId = null;
    if (companyName) {
      const c = await env.DB.prepare(
        'INSERT INTO companies (name, country) VALUES (?, ?) RETURNING id'
      ).bind(companyName, country || null).first();
      companyId = c?.id ?? null;
    }

    const cust = await env.DB.prepare(
      `INSERT INTO customers (company_id, name, email, phone, country, preferred_contact)
       VALUES (?, ?, ?, ?, ?, ?) RETURNING id`
    ).bind(companyId, name, email, phone || null, country || null, preferredContact || null).first();
    const customerId = cust?.id ?? null;

    // Reference collisions are astronomically unlikely (32^6) but the column
    // is UNIQUE, so retry rather than 500 on the off chance.
    let reference = null;
    let requirementId = null;
    for (let attempt = 0; attempt < 5; attempt++) {
      const candidate = generateReference();
      try {
        const r = await env.DB.prepare(
          `INSERT INTO requirements (
             reference, customer_id, company_id, description,
             users_count, devices_count, windows_devices, mac_devices,
             productivity_suite, endpoint_solution, other_technology,
             budget_range, urgency, extra_message, source, ip_country
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id`
        ).bind(
          candidate, customerId, companyId, description,
          env_users || null, env_devices || null, env_windows || null, env_mac || null,
          env_suite || null, env_endpoint || null, env_other || null,
          budget || null, urgency, extraMessage || null, source || null, ipCountry || null
        ).first();
        reference = candidate;
        requirementId = r?.id ?? null;
        break;
      } catch (err) {
        if (!String(err).includes('UNIQUE')) throw err;
      }
    }
    if (!requirementId) throw new Error('could not allocate a unique reference');

    for (const category of categories) {
      await env.DB.prepare(
        'INSERT OR IGNORE INTO requirement_categories (requirement_id, category) VALUES (?, ?)'
      ).bind(requirementId, category).run();
    }

    await env.DB.prepare(
      'INSERT INTO status_history (requirement_id, from_status, to_status) VALUES (?, NULL, ?)'
    ).bind(requirementId, 'new').run();

    // Attachments go to R2 if it's bound. A missing R2 binding shouldn't lose
    // the enquiry itself, so this is best-effort and logged.
    if (files.length > 0) {
      if (!env.ATTACHMENTS) {
        console.error('requirements: ATTACHMENTS R2 bucket not bound; skipping', files.length, 'file(s)');
      } else {
        for (const file of files) {
          const safeName = file.name.replace(/[^A-Za-z0-9._-]/g, '_').slice(0, 120);
          const key = `${reference}/${crypto.randomUUID()}-${safeName}`;
          try {
            await env.ATTACHMENTS.put(key, file.stream(), {
              httpMetadata: { contentType: file.type }
            });
            await env.DB.prepare(
              `INSERT INTO requirement_attachments (requirement_id, r2_key, filename, content_type, size_bytes)
               VALUES (?,?,?,?,?)`
            ).bind(requirementId, key, safeName, file.type, file.size).run();
          } catch (err) {
            console.error('requirements: attachment upload failed', key, err);
          }
        }
      }
    }

    // Notifications are fire-and-forget relative to the response the customer
    // sees — but we still await them inside waitUntil so failures get logged.
    context.waitUntil(
      notify(env, { reference, requirementId, name, email, companyName, categories, description, budget, urgency })
        .catch(err => console.error('requirements: notification error', err))
    );

    return json({ ok: true, reference });

  } catch (err) {
    console.error('requirements: submission failed', err);
    return json({ ok: false, error: 'We could not save your requirement. Please try again shortly.' }, 500);
  }
}

async function notify(env, r) {
  const adminEmail = env.ADMIN_NOTIFY_EMAIL;
  const site = 'https://services.itvedas.com';

  const customerHtml = `
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;color:#151A2E;">
      <h2 style="color:#4338CA;">We've received your IT requirement</h2>
      <p>Hi ${escapeHtml(r.name)},</p>
      <p>Thanks for getting in touch. Your requirement has been received and is now queued for review.</p>
      <p style="background:#EEF0FF;padding:14px 18px;border-radius:8px;">
        <strong>Your reference:</strong> ${escapeHtml(r.reference)}
      </p>
      <p>We'll review what you've sent and come back to you with next steps, including scope and pricing where relevant. Please keep your reference handy when you reply.</p>
      <p style="color:#606A85;font-size:13px;">— ITVedas Services<br><a href="${site}" style="color:#4338CA;">${site}</a></p>
    </div>`;

  const adminHtml = `
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;color:#151A2E;">
      <h2 style="color:#4338CA;">New IT requirement — ${escapeHtml(r.reference)}</h2>
      <table cellpadding="6" style="border-collapse:collapse;font-size:14px;">
        <tr><td><strong>Name</strong></td><td>${escapeHtml(r.name)}</td></tr>
        <tr><td><strong>Email</strong></td><td>${escapeHtml(r.email)}</td></tr>
        <tr><td><strong>Company</strong></td><td>${escapeHtml(r.companyName || '—')}</td></tr>
        <tr><td><strong>Categories</strong></td><td>${escapeHtml(r.categories.join(', '))}</td></tr>
        <tr><td><strong>Budget</strong></td><td>${escapeHtml(r.budget || 'not specified')}</td></tr>
        <tr><td><strong>Urgency</strong></td><td>${escapeHtml(r.urgency)}</td></tr>
      </table>
      <h3>Requirement</h3>
      <p style="white-space:pre-wrap;background:#F1F3F9;padding:14px;border-radius:8px;">${escapeHtml(r.description)}</p>
      <p><a href="${site}/admin/" style="color:#4338CA;">Open the admin dashboard</a></p>
    </div>`;

  const results = [];
  results.push(['customer_received', r.email, await sendEmail(env, {
    to: r.email,
    subject: `Your IT requirement ${r.reference} — ITVedas Services`,
    html: customerHtml
  })]);

  if (adminEmail) {
    results.push(['admin_notify', adminEmail, await sendEmail(env, {
      to: adminEmail,
      subject: `New IT requirement ${r.reference} (${r.urgency})`,
      html: adminHtml,
      replyTo: r.email
    })]);
  }

  for (const [template, recipient, result] of results) {
    try {
      await env.DB.prepare(
        'INSERT INTO email_events (requirement_id, template, recipient, status, error) VALUES (?,?,?,?,?)'
      ).bind(r.requirementId, template, recipient, result.status, result.error).run();
    } catch (err) {
      console.error('requirements: could not log email event', err);
    }
  }
}

// Explicit per-method rejections rather than a catch-all onRequest export —
// a catch-all would shadow onRequestPost above.
export async function onRequestGet() {
  return json({ ok: false, error: 'Method not allowed. Use POST.' }, 405);
}
