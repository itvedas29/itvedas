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

  // Browsers always send Origin on POST, so requiring it blocks scripted signups
  // that simply omit the header.
  if (!ALLOWED_ORIGINS.includes(origin)) {
    return jsonResponse({ success: false, message: "Origin not allowed" }, 403);
  }

  if (!env.GOOGLE_SHEETS_WEB_APP_URL || !env.GOOGLE_SHEETS_WEBHOOK_SECRET) {
    console.error("Subscribe error: Google Sheets integration is not configured");
    return jsonResponse({ success: false, message: "Subscriptions are temporarily unavailable. Please try again later." }, 503);
  }

  try {
    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResponse({ success: false, message: "Invalid JSON body" }, 400);
    }
    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return jsonResponse({ success: false, message: "Invalid request body" }, 400);
    }
    const email = typeof body.email === "string" ? body.email.trim() : "";
    const consent = body.consent === true;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email) || email.length > 254) {
      return jsonResponse({ success: false, message: "Invalid email format" }, 400);
    }
    if (!consent) {
      return jsonResponse({ success: false, message: "Please confirm that you want to receive email updates." }, 400);
    }

    // If the optional KV namespace is configured, throttle without retaining
    // the visitor's IP address.
    if (env.SUBSCRIBE_RATE_LIMIT) {
      const clientIp = request.headers.get("CF-Connecting-IP") || "unknown";
      const rateKey = `subscribe-rate:${await anonymizedRateKey(clientIp)}`;
      if (await env.SUBSCRIBE_RATE_LIMIT.get(rateKey)) {
        return jsonResponse({ success: false, message: "Please wait before trying again." }, 429);
      }
      await env.SUBSCRIBE_RATE_LIMIT.put(rateKey, "1", { expirationTtl: RATE_LIMIT_SECONDS });
    }

    const response = await fetch(env.GOOGLE_SHEETS_WEB_APP_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        secret: env.GOOGLE_SHEETS_WEBHOOK_SECRET,
        email,
        source: "homepage-newsletter"
      })
    });
    if (!response.ok) {
      throw new Error(`Google Sheets endpoint returned HTTP ${response.status}`);
    }

    const result = await response.json();
    if (result.code === "already_subscribed") {
      return jsonResponse({ success: false, message: "This email is already subscribed." }, 409);
    }
    if (result.success !== true) {
      throw new Error(`Google Sheets endpoint did not confirm the subscription: ${result.code || "unknown"}`);
    }

    return jsonResponse({ success: true, message: "Successfully subscribed" });
  } catch (error) {
    console.error("Subscribe error:", error);
    return jsonResponse({ success: false, message: "Unable to process subscription. Please try again later." }, 500);
  }
}

export async function onRequestGet() {
  return jsonResponse({ success: false, message: "Use POST" }, 405);
}

async function anonymizedRateKey(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
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
