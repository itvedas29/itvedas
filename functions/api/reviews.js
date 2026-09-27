// functions/api/reviews.js
//
// Cloudflare Pages Function for user reviews and feedback on /software/ spec sheets.
//
//   GET  /api/reviews?product=<slug>   -> approved reviews + rating summary
//   POST /api/reviews                  -> submit a review (held for moderation)
//
// Storage: the REVIEWS KV namespace (bind it in Cloudflare Pages > Settings >
// Functions > KV namespace bindings, variable name REVIEWS).
//   pending:<product>:<id>   review waiting for approval
//   approved:<product>:<id>  published review
// Moderation happens in /software/reviews-admin/ via functions/api/reviews-admin.js.
//
// Everything is stored and returned as plain text. The pages render it with
// textContent, never innerHTML, so submitted text cannot inject markup.

export const PRODUCTS = new Set(["manageengine-endpoint-central"]);
export const TOPICS = new Set(["software", "specs"]);

const ALLOWED_ORIGINS = ["https://itvedas.com", "https://www.itvedas.com"];
const RATE_LIMIT_SECONDS = 600;   // one submission per visitor per 10 minutes
const MAX_LIST = 100;

export async function onRequestGet({ request, env }) {
  if (!env.REVIEWS) return json({ error: "Reviews are not set up yet." }, 503);

  const product = new URL(request.url).searchParams.get("product") || "";
  if (!PRODUCTS.has(product)) return json({ error: "Unknown product." }, 400);

  const listed = await env.REVIEWS.list({ prefix: `approved:${product}:`, limit: MAX_LIST });
  const reviews = (await Promise.all(listed.keys.map(k => env.REVIEWS.get(k.name, "json"))))
    .filter(Boolean)
    .map(publicView)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  const rated = reviews.filter(r => r.topic === "software" && r.rating);
  const average = rated.length ? Math.round((rated.reduce((s, r) => s + r.rating, 0) / rated.length) * 10) / 10 : null;
  const counts = [5, 4, 3, 2, 1].map(stars => ({ stars, count: rated.filter(r => r.rating === stars).length }));

  return json({ product, total: reviews.length, rated: rated.length, average, counts, reviews }, 200, {
    "Cache-Control": "public, max-age=60"
  });
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get("Origin") || "";
  const isDev = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  if (origin && !ALLOWED_ORIGINS.includes(origin) && !isDev) {
    return json({ error: "Origin not allowed." }, 403);
  }
  if (!env.REVIEWS) return json({ error: "Reviews are not set up yet. Please try again later." }, 503);

  let body;
  try { body = await request.json(); } catch { return json({ error: "Send the form as JSON." }, 400); }

  // Honeypot: real visitors never see or fill this field.
  if (body && typeof body.website === "string" && body.website.trim() !== "") {
    return json({ ok: true, status: "pending" }, 202);
  }

  const check = validate(body);
  if (check.error) return json({ error: check.error }, 400);

  const ip = request.headers.get("CF-Connecting-IP") || "";
  if (ip) {
    const rateKey = `rate:${await sha256(ip)}`;
    if (await env.REVIEWS.get(rateKey)) {
      return json({ error: "You've just sent a review. Please wait 10 minutes before sending another." }, 429);
    }
    await env.REVIEWS.put(rateKey, "1", { expirationTtl: RATE_LIMIT_SECONDS });
  }

  const now = new Date().toISOString();
  const id = `${now.replace(/[-:.TZ]/g, "")}-${crypto.randomUUID().slice(0, 8)}`;
  const review = { id, ...check.value, createdAt: now, status: "pending" };
  await env.REVIEWS.put(`pending:${review.product}:${id}`, JSON.stringify(review));

  return json({ ok: true, status: "pending" }, 202);
}

export function validate(body) {
  if (!body || typeof body !== "object") return { error: "Fill in the form and try again." };

  const product = str(body.product);
  if (!PRODUCTS.has(product)) return { error: "Unknown product." };

  const topic = str(body.topic);
  if (!TOPICS.has(topic)) return { error: "Choose what your feedback is about." };

  const name = clean(body.name, 40);
  if (name.length < 2) return { error: "Enter a name of at least 2 characters." };

  const role = clean(body.role, 60);

  const text = clean(body.text, 1500, true);
  if (text.length < 20) return { error: "Write at least 20 characters so others can learn from it." };

  let rating = null;
  if (topic === "software") {
    rating = Number(body.rating);
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) return { error: "Choose a rating from 1 to 5 stars." };
  }

  if (/(https?:\/\/|www\.)\S+/i.test(text) && (text.match(/https?:\/\//gi) || []).length > 2) {
    return { error: "Please remove the links from your review." };
  }

  return { value: { product, topic, name, role, text, rating } };
}

export function publicView(r) {
  return { id: r.id, topic: r.topic, name: r.name, role: r.role || "", text: r.text, rating: r.rating ?? null, createdAt: r.createdAt };
}

function str(v) { return typeof v === "string" ? v.trim() : ""; }

// Plain text only: drop control characters, collapse runs of spaces, cap the length.
function clean(v, max, keepNewlines = false) {
  let s = typeof v === "string" ? v : "";
  s = s.replace(keepNewlines ? /[\u0000-\u0009\u000B-\u001F\u007F]/g : /[\u0000-\u001F\u007F]/g, "");
  s = keepNewlines ? s.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n") : s.replace(/\s+/g, " ");
  return s.trim().slice(0, max);
}

async function sha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
}

function json(obj, status = 200, extra = {}) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...extra }
  });
}
