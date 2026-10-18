// functions/api/quiz-questions.js
// Picks the questions for one quiz attempt. For each visitor IP (stored only as a
// salted SHA-256 hash), questions already served are skipped until the level's bank
// is used up. Records expire after 90 days.

const LEVELS = ["beginner", "intermediate", "advanced"];
const QUESTIONS_PER_QUIZ = 10;
const RETENTION_SECONDS = 90 * 24 * 60 * 60;

export async function onRequestPost(context) {
  const { request, env } = context;

  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ success: false, message: "Invalid JSON body" }, 400);
  }
  const level = body && typeof body.level === "string" ? body.level : "";
  if (!LEVELS.includes(level)) {
    return jsonResponse({ success: false, message: "Invalid level" }, 400);
  }

  const bank = await loadBank(request);
  if (!bank || !Array.isArray(bank[level])) {
    return jsonResponse({ success: false, message: "Questions are unavailable" }, 500);
  }
  const ids = bank[level].map((_, index) => `${level}:${index}`);

  if (!env.QUIZ_KV || !env.QUIZ_IP_SALT) {
    console.error("Quiz rotation is not configured; serving random questions without history.");
    return questionsResponse(pickRandom(ids, QUESTIONS_PER_QUIZ), bank, level);
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const key = `quizseen:${await hashValue(env.QUIZ_IP_SALT + ip)}`;
  const record = parseRecord(await env.QUIZ_KV.get(key));
  let seen = Array.isArray(record[level]) ? record[level] : [];

  const unseen = ids.filter(id => !seen.includes(id));
  let picked;
  if (unseen.length >= QUESTIONS_PER_QUIZ) {
    picked = pickRandom(unseen, QUESTIONS_PER_QUIZ);
    record[level] = seen.concat(picked);
  } else {
    const repeats = pickRandom(seen.filter(id => !unseen.includes(id)), QUESTIONS_PER_QUIZ - unseen.length);
    picked = pickRandom(unseen.concat(repeats), QUESTIONS_PER_QUIZ);
    record[level] = picked;
  }
  await env.QUIZ_KV.put(key, JSON.stringify(record), { expirationTtl: RETENTION_SECONDS });

  return questionsResponse(picked, bank, level);
}

export async function onRequestGet() {
  return jsonResponse({ success: false, message: "Use POST" }, 405);
}

async function loadBank(request) {
  try {
    const response = await fetch(new URL("/quiz-data.json", request.url));
    if (!response.ok) return null;
    const data = await response.json();
    return data.BANK || null;
  } catch {
    return null;
  }
}

function questionsResponse(ids, bank, level) {
  const questions = ids.map(id => {
    const index = Number(id.split(":")[1]);
    return { id, item: bank[level][index] };
  });
  return jsonResponse({ success: true, questions });
}

function pickRandom(items, count) {
  const copy = items.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, count);
}

function parseRecord(raw) {
  try {
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

async function hashValue(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
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
