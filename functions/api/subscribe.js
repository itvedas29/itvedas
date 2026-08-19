// functions/api/subscribe.js
// Cloudflare Pages Function for newsletter signups.

const ALLOWED_ORIGINS = [
  "https://itvedas.com",
  "https://www.itvedas.com",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
  "http://localhost:8080",
  "http://127.0.0.1:8080"
];
const RATE_LIMIT_SECONDS = 60;

export async function onRequestPost(context) {
  const { request, env } = context;
  const origin = request.headers.get("Origin") || "";

  if (origin && !ALLOWED_ORIGINS.includes(origin)) {
    return jsonResponse({ success: false, message: "Origin not allowed" }, 403);
  }

  if (!env.SUBSCRIBERS) {
    console.error("Subscribe error: SUBSCRIBERS KV namespace not bound");
    return jsonResponse({ success: false, message: "Unable to process subscription. Please try again later." }, 500);
  }

  try {
    const body = await request.json();
    const email = typeof body.email === "string" ? body.email.trim() : "";

    // This intentionally ignores all client-controlled metadata. Receipt time is
    // established at the edge so it cannot be forged by the browser.
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email) || email.length > 254) {
      return jsonResponse({ success: false, message: "Invalid email format" }, 400);
    }

    // A short edge-side throttle reduces automated writes without retaining a
    // permanent IP profile. KV is eventually consistent, so this is abuse
    // reduction rather than a hard global quota.
    const clientIp = request.headers.get("CF-Connecting-IP") || "";
    if (clientIp) {
      const rateKey = `subscribe-rate:${clientIp}`;
      if (await env.SUBSCRIBERS.get(rateKey)) {
        return jsonResponse({ success: false, message: "Please wait before trying again." }, 429);
      }
      await env.SUBSCRIBERS.put(rateKey, "1", { expirationTtl: RATE_LIMIT_SECONDS });
    }

    const normalizedEmail = email.toLowerCase();
    const key = `subscriber:${normalizedEmail}`;
    if (await env.SUBSCRIBERS.get(key)) {
      return jsonResponse({ success: false, message: "Already subscribed" }, 400);
    }

    await env.SUBSCRIBERS.put(key, JSON.stringify({
      email,
      timestamp: new Date().toISOString(),
      verified: false,
      source: "homepage-signup"
    }));

    return jsonResponse({ success: true, message: "Successfully subscribed" });
  } catch (error) {
    console.error("Subscribe error:", error);
    return jsonResponse({ success: false, message: "Unable to process subscription. Please try again later." }, 500);
  }
}

export async function onRequestGet() {
  return jsonResponse({ success: false, message: "Use POST" }, 405);
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store"
    }
  });
}
