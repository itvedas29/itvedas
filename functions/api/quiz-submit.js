// functions/api/quiz-submit.js
// Cloudflare Pages Function that stores quiz results in the newsletter spreadsheet's
// "Quiz Participants" tab. Shares the Apps Script endpoint with /api/subscribe.

const ALLOWED_ORIGINS = [
  "https://itvedas.com",
  "https://www.itvedas.com",
  "http://localhost:3000",
  "http://127.0.0.1:3000",
  "http://localhost:8080",
  "http://127.0.0.1:8080"
];
const LEVELS = ["beginner", "intermediate", "advanced"];
const RATE_LIMIT_SECONDS = 60;

export async function onRequestPost(context) {
  const { request, env } = context;
  const origin = request.headers.get("Origin") || "";

  if (!ALLOWED_ORIGINS.includes(origin)) {
    return jsonResponse({ success: false, message: "Origin not allowed" }, 403);
  }
  if (!env.GOOGLE_SHEETS_WEB_APP_URL || !env.GOOGLE_SHEETS_WEBHOOK_SECRET) {
    console.error("Quiz submit error: Google Sheets integration is not configured");
    return jsonResponse({ success: false, message: "Results cannot be saved right now." }, 503);
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

    const name = typeof body.name === "string" ? body.name.trim() : "";
    const email = typeof body.email === "string" ? body.email.trim() : "";
    const consent = body.consent === true;

    if (!name || name.length > 100) {
      return jsonResponse({ success: false, message: "Please enter your name." }, 400);
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254) {
      return jsonResponse({ success: false, message: "Invalid email format" }, 400);
    }
    if (!consent) {
      return jsonResponse({ success: false, message: "Please confirm that we can store your details." }, 400);
    }

    const forward = { secret: env.GOOGLE_SHEETS_WEBHOOK_SECRET, name, email };
    if (body.stage === "start") {
      forward.type = "quiz_start";
    } else {
      const level = typeof body.level === "string" ? body.level : "";
      const score = body.score;
      if (!LEVELS.includes(level) || !Number.isInteger(score) || score < 0 || score > 10) {
        return jsonResponse({ success: false, message: "Invalid quiz result" }, 400);
      }
      forward.type = "quiz";
      forward.level = level;
      forward.score = score;
      forward.topics = JSON.stringify(body.topics && typeof body.topics === "object" ? body.topics : {}).slice(0, 1000);
    }

    // Every accepted request appends a sheet row, so throttle each stage per
    // visitor (keyed by a hash, never the raw IP) when the quiz KV is bound.
    if (env.QUIZ_KV) {
      const clientIp = request.headers.get("CF-Connecting-IP") || "unknown";
      const rateKey = `quiz-submit-rate:${forward.type}:${await anonymizedRateKey(clientIp)}`;
      if (await env.QUIZ_KV.get(rateKey)) {
        return jsonResponse({ success: false, message: "Please wait before trying again." }, 429);
      }
      await env.QUIZ_KV.put(rateKey, "1", { expirationTtl: RATE_LIMIT_SECONDS });
    }

    const response = await fetch(env.GOOGLE_SHEETS_WEB_APP_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(forward)
    });
    if (!response.ok) {
      throw new Error(`Google Sheets endpoint returned HTTP ${response.status}`);
    }
    const result = await response.json();
    if (result.success !== true) {
      throw new Error(`Google Sheets endpoint rejected the result: ${result.code || "unknown"}`);
    }
    return jsonResponse({ success: true });
  } catch (error) {
    console.error("Quiz submit error:", error);
    return jsonResponse({ success: false, message: "Unable to save your result. Please try again later." }, 500);
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
