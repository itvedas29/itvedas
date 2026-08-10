# ITVedas Services

Lead-generation and requirement-management platform for
[services.itvedas.com](https://services.itvedas.com) — a remote IT support
service for small businesses.

**This is a separate Cloudflare Pages project from the parent itvedas.com
site**, deployed from the same Git repository but with the root directory set
to `services/`. The parent site (repo root) is untouched by anything here.

The business flow this platform implements:

```
Traffic → customer posts an IT requirement → we review and scope it
       → we quote → project starts on Fiverr/Upwork → work delivered
```

V1 deliberately does **not** process payments. Payment happens on Fiverr or
Upwork; this site captures, qualifies and tracks the requirement.

## Stack

Plain static HTML/CSS/vanilla JS plus Cloudflare Pages Functions — the same
stack the parent site already uses. No build step, no framework, no npm
dependencies.

| Concern | Implementation |
| --- | --- |
| Pages | Static HTML, one file per route |
| Styling | Single shared stylesheet, `css/shared.css` |
| API | Pages Functions in `functions/` |
| Database | Cloudflare D1 (SQLite) — binding `DB` |
| Rate limiting | Cloudflare KV — binding `RATE_LIMIT` |
| Attachments | Cloudflare R2 — binding `ATTACHMENTS` |
| Email | Resend HTTP API (optional) |
| Admin auth | Server-side sessions + PBKDF2-SHA256 passwords |

## Layout

```
services/
├── index.html              Homepage
├── services/               Service catalog + 11 service detail pages
├── request-it-help.html    Multi-step requirement form (primary conversion)
├── pricing.html            Indicative pricing
├── how-it-works.html       Process, including the Fiverr/Upwork step
├── about.html  faq.html  case-studies.html
├── privacy-policy.html  terms-of-service.html  404.html
├── admin/index.html        Admin dashboard (login + enquiries + detail)
├── css/shared.css          Design system
├── js/                     nav.js, request-wizard.js, admin.js
├── functions/
│   ├── _lib.js             Validation, hashing, rate limiting, email
│   ├── _auth.js            Session creation/verification
│   └── api/
│       ├── requirements.js         POST — public submission
│       └── admin/                  login, logout, session, bootstrap,
│                                   requirements, requirement/[id],
│                                   attachment/[id]
├── migrations/             0001_initial.sql, 0002_seed.sql
├── wrangler.toml           Pages config + bindings
├── _headers                CSP and cache policy
├── robots.txt  sitemap.xml
└── .env.example            Environment variable reference
```

Files under `functions/` starting with `_` are shared modules, not routes —
Cloudflare Pages does not route them.

## Local development

Wrangler must run **from inside this directory**. Running
`wrangler pages dev services` from the repo root makes wrangler walk up and
load the parent site's `wrangler.toml`, which serves the parent's
`functions/` directory instead of this one — every `/api` route then 404s.

```bash
cd services && npx wrangler pages dev . --port 8790
```

First-time setup — create the local database:

```bash
cd services && npx wrangler d1 execute itvedas-services --local --file=./migrations/0001_initial.sql
```

```bash
cd services && npx wrangler d1 execute itvedas-services --local --file=./migrations/0002_seed.sql
```

Create the first local admin. Put `ADMIN_BOOTSTRAP_TOKEN=some-long-value` in
`services/.dev.vars` (gitignored), restart the dev server, then:

```bash
curl -X POST http://127.0.0.1:8790/api/admin/bootstrap -H "Content-Type: application/json" -d '{"token":"some-long-value","email":"you@example.com","name":"Admin","password":"a-long-password"}'
```

Then sign in at `http://127.0.0.1:8790/admin/`.

## Production deployment

None of the steps below have been run — no Cloudflare resources have been
created and no DNS has been changed.

### 1. Create the backing resources

```bash
cd services && npx wrangler d1 create itvedas-services
```

```bash
cd services && npx wrangler kv namespace create RATE_LIMIT
```

```bash
cd services && npx wrangler r2 bucket create itvedas-services-attachments
```

Copy the printed `database_id` and KV `id` into `wrangler.toml`, replacing the
`REPLACE_WITH_*` placeholders.

### 2. Apply migrations to the remote database

```bash
cd services && npx wrangler d1 execute itvedas-services --remote --file=./migrations/0001_initial.sql
```

```bash
cd services && npx wrangler d1 execute itvedas-services --remote --file=./migrations/0002_seed.sql
```

### 3. Create the Pages project

In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to
Git**, choose the `itvedas29/itvedas` repository, and set:

- **Project name**: `itvedas-services`
- **Production branch**: `main`
- **Build command**: *(blank — there is no build step)*
- **Build output directory**: *(blank)*
- **Root directory**: `services`

Root directory is the critical setting: it makes Cloudflare treat `services/`
as the site root, so `/api/...` resolves to `services/functions/api/...` and
the parent site's `functions/` is never involved.

### 4. Set environment variables

In **Settings → Environment variables** (or via `wrangler pages secret put`),
using `.env.example` as the reference: `RESEND_API_KEY` (secret), `EMAIL_FROM`,
`ADMIN_NOTIFY_EMAIL`, and temporarily `ADMIN_BOOTSTRAP_TOKEN`.

Confirm the `DB`, `RATE_LIMIT` and `ATTACHMENTS` bindings appear under
**Settings → Bindings**.

### 5. Create the first admin, then close the door

```bash
curl -X POST https://services.itvedas.com/api/admin/bootstrap -H "Content-Type: application/json" -d '{"token":"YOUR_BOOTSTRAP_TOKEN","email":"you@itvedas.com","name":"Your Name","password":"a-long-unique-password"}'
```

Then **delete `ADMIN_BOOTSTRAP_TOKEN`** from the environment variables and
redeploy. The endpoint also refuses to run once an admin exists, but removing
the token closes the path entirely.

### 6. DNS

Attach the custom domain in **Pages → itvedas-services → Custom domains → Set
up a custom domain → `services.itvedas.com`**. Because `itvedas.com` is
already on Cloudflare, adding it there creates the record automatically.

If you add it manually instead, the record is:

| Type | Name | Target | Proxy |
| --- | --- | --- | --- |
| CNAME | `services` | `itvedas-services.pages.dev` | Proxied (orange cloud) |

The exact `*.pages.dev` hostname is shown on the project page after the first
deploy — use that value rather than assuming this one.

## Security notes

- Every field is validated server-side in `functions/api/requirements.js`;
  client-side validation is a UX affordance only.
- All D1 access uses bound parameters.
- Uploads are restricted by size (5 MB), count (3) and MIME type, and are
  served back only to authenticated admins with
  `Content-Disposition: attachment` so nothing renders in the admin origin.
- The admin UI renders all customer text via `textContent`, never `innerHTML`.
- Session cookies are `HttpOnly; Secure; SameSite=Strict`; sessions are rows
  in `admin_sessions`, so revoking one is a row delete.
- Login responds identically for a wrong password and an unknown account, and
  still performs a real hash comparison, so admin emails can't be enumerated.
- The public form is protected by a honeypot field and KV-backed rate
  limiting (5 submissions per IP per hour).
- CSP in `_headers` is stricter than the parent site's: `script-src 'self'`
  with no `unsafe-inline`. Adding any third-party script means allowlisting it
  there explicitly.

## Extending later

The schema already separates `companies`, `customers`, `quotes`, `projects`
and `status_history` from `requirements`, so Phase 2 work (customer accounts,
invoices, direct payment, ticketing) adds columns and endpoints rather than
requiring a reshape. `service_catalog` and `settings` exist so pricing and
business configuration can move out of the HTML and into the database when an
admin settings screen is built.
