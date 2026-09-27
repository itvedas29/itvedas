// functions/api/reviews-admin.js
//
// Moderation API for user reviews, used by /software/reviews-admin/.
// Every request needs the header  Authorization: Bearer <REVIEWS_ADMIN_TOKEN>.
// Set REVIEWS_ADMIN_TOKEN as an encrypted environment variable (secret) in
// Cloudflare Pages > Settings > Environment variables. Use a long random value.
//
//   GET  /api/reviews-admin?status=pending|approved&product=<slug>
//   POST /api/reviews-admin  { action: "approve" | "delete", product, id }

import { PRODUCTS, publicView } from "./reviews.js";

export async function onRequestGet({ request, env }) {
  const denied = await authorise(request, env);
  if (denied) return denied;

  const url = new URL(request.url);
  const status = url.searchParams.get("status") === "approved" ? "approved" : "pending";
  const product = url.searchParams.get("product") || "";
  if (!PRODUCTS.has(product)) return json({ error: "Unknown product." }, 400);

  const listed = await env.REVIEWS.list({ prefix: `${status}:${product}:`, limit: 200 });
  const reviews = (await Promise.all(listed.keys.map(k => env.REVIEWS.get(k.name, "json"))))
    .filter(Boolean)
    .map(publicView)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return json({ status, product, reviews });
}

export async function onRequestPost({ request, env }) {
  const denied = await authorise(request, env);
  if (denied) return denied;

  let body;
  try { body = await request.json(); } catch { return json({ error: "Send JSON." }, 400); }
  const { action, product, id } = body || {};
  if (!PRODUCTS.has(product) || typeof id !== "string" || !/^[0-9a-f-]{8,40}$/i.test(id)) {
    return json({ error: "Unknown review." }, 400);
  }

  const pendingKey = `pending:${product}:${id}`;
  const approvedKey = `approved:${product}:${id}`;

  if (action === "approve") {
    const review = await env.REVIEWS.get(pendingKey, "json");
    if (!review) return json({ error: "That review is no longer waiting for approval." }, 404);
    review.status = "approved";
    review.approvedAt = new Date().toISOString();
    await env.REVIEWS.put(approvedKey, JSON.stringify(review));
    await env.REVIEWS.delete(pendingKey);
    return json({ ok: true, action: "approved", id });
  }

  if (action === "delete") {
    await env.REVIEWS.delete(pendingKey);
    await env.REVIEWS.delete(approvedKey);
    return json({ ok: true, action: "deleted", id });
  }

  return json({ error: "Action must be approve or delete." }, 400);
}

async function authorise(request, env) {
  if (!env.REVIEWS || !env.REVIEWS_ADMIN_TOKEN || env.REVIEWS_ADMIN_TOKEN.length < 24) {
    return json({ error: "Moderation is not set up. Add the REVIEWS KV binding and a REVIEWS_ADMIN_TOKEN of 24+ characters." }, 503);
  }
  const header = request.headers.get("Authorization") || "";
  const given = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!(await sameSecret(given, env.REVIEWS_ADMIN_TOKEN))) {
    return json({ error: "Wrong admin token." }, 401);
  }
  return null;
}

// Compare digests so the check takes the same time whatever the input.
async function sameSecret(a, b) {
  const enc = new TextEncoder();
  const [da, db] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b))
  ]);
  const x = new Uint8Array(da), y = new Uint8Array(db);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0 && a.length > 0;
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" }
  });
}
