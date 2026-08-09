// functions/api/subscribe.js
//
// Cloudflare Pages Function — must use the onRequest* export convention
// (not the Workers `export default { fetch }` module convention) or Pages
// will never route requests to this handler.

const MAX_SUBSCRIBERS = 20000;

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

    // Store in KV
    const subscribers = await env.SUBSCRIBERS.get('list') || '[]';
    const list = JSON.parse(subscribers);

    // Check for duplicates
    if (list.some(s => s.email === email)) {
      return jsonResponse({ success: false, message: 'Already subscribed' }, 400);
    }

    // Cap unbounded growth — protects the KV value from hitting size limits
    if (list.length >= MAX_SUBSCRIBERS) {
      console.error('Subscribe error: subscriber list at capacity');
      return jsonResponse({ success: false, message: 'Unable to process subscription. Please try again later.' }, 503);
    }

    // Add new subscriber
    list.push({
      email,
      timestamp: timestamp || new Date().toISOString(),
      verified: false,
      source: 'homepage-signup'
    });

    await env.SUBSCRIBERS.put('list', JSON.stringify(list));

    return jsonResponse({
      success: true,
      message: 'Successfully subscribed',
      count: list.length
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
