// functions/api/subscribe.js
//
// Cloudflare Pages Function — must use the onRequest* export convention
// (not the Workers `export default { fetch }` module convention) or Pages
// will never route requests to this handler.

const ALLOWED_ORIGINS = [
  "https://itvedas.com",
  "https://www.itvedas.com",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
  "http://localhost:8080",
  "http://127.0.0.1:8080"
];

export async function onRequestPost(context) {
  const { request, env } = context;

  // Basic origin check — not a security boundary, just reduces casual abuse
  // from random hotlinking.
  const origin = request.headers.get("Origin") || "";
  if (origin && !ALLOWED_ORIGINS.includes(origin)) {
    return jsonResponse({ success: false, message: 'Origin not allowed' }, 403);
  }

  try {
    const { email, timestamp } = await request.json();

    if (!email || typeof email !== 'string' || !email.includes('@')) {
      return jsonResponse({ success: false, message: 'Invalid email' }, 400);
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email) || email.length > 254) {
      return jsonResponse({ success: false, message: 'Invalid email format' }, 400);
    }

    if (!env.SUBSCRIBERS) {
      console.error('Subscribe error: SUBSCRIBERS KV namespace not bound');
      return jsonResponse({ success: false, message: 'Unable to process subscription. Please try again later.' }, 500);
    }

    // One KV entry per subscriber, keyed by normalized email — avoids the
    // read-modify-write race a single shared list value had (two concurrent
    // signups could clobber each other) and makes dedup case-insensitive
    // for free, since the key itself is normalized.
    const key = `subscriber:${email.toLowerCase()}`;

    const existing = await env.SUBSCRIBERS.get(key);
    if (existing) {
      return jsonResponse({ success: false, message: 'Already subscribed' }, 400);
    }

    await env.SUBSCRIBERS.put(key, JSON.stringify({
      email,
      timestamp: timestamp || new Date().toISOString(),
      verified: false,
      source: 'homepage-signup'
    }));

    return jsonResponse({
      success: true,
      message: 'Successfully subscribed'
    });

  } catch (error) {
    console.error('Subscribe error:', error);
    // Log full error server-side, return generic message to client
    return jsonResponse({ success: false, message: 'Unable to process subscription. Please try again later.' }, 500);
  }
}

// Reject non-POST methods explicitly
export async function onRequestGet() {
  return jsonResponse({ success: false, message: 'Use POST' }, 405);
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });
}
