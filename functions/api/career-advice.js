// functions/api/career-advice.js
//
// Cloudflare Pages Function — runs server-side on Cloudflare's edge.
// This is what keeps your ANTHROPIC_API_KEY hidden from visitors.
// Set ANTHROPIC_API_KEY as an environment variable in:
// Cloudflare Pages dashboard > your project > Settings > Environment variables
//
// Visitor's browser calls: POST /api/career-advice
// This function calls Claude, and returns ONLY the structured result.

const VALID_CHAPTERS = [
  "networking", "cloud", "security", "devops",
  "databases", "linux", "hardware", "compliance"
];

const CHAPTER_LABELS = {
  networking: "Networking",
  cloud: "Cloud Computing",
  security: "Cybersecurity",
  devops: "DevOps",
  databases: "Databases",
  linux: "Linux & Systems",
  hardware: "Hardware & Infrastructure",
  compliance: "IT Compliance & Risk"
};

export async function onRequestPost(context) {
  const { request, env } = context;

  // Basic origin check — not a security boundary, just reduces casual abuse
  // from random hotlinking. Update this to your actual domain.
  const origin = request.headers.get("Origin") || "";
  const allowedOrigins = [
    "https://itvedas.com",
    "https://www.itvedas.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080"
  ];

  if (origin && !allowedOrigins.includes(origin)) {
    return jsonResponse({ error: "Origin not allowed" }, 403);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON body" }, 400);
  }

  const answers = body.answers;
  if (!Array.isArray(answers) || answers.length === 0) {
    return jsonResponse({ error: "Missing answers array" }, 400);
  }

  // Cap input size defensively — prevents abuse via huge payloads driving up cost
  const totalChars = answers.reduce((sum, a) => sum + (a.question?.length || 0) + (a.answer?.length || 0), 0);
  if (totalChars > 6000) {
    return jsonResponse({ error: "Answers payload too large" }, 400);
  }

  const apiKey = env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return jsonResponse({ error: "Server misconfigured: missing API key" }, 500);
  }

  const formattedQA = answers
    .map((a, i) => `Q${i + 1}: ${a.question}\nA${i + 1}: ${a.answer}`)
    .join("\n\n");

  const systemPrompt = `You are the Career Navigator for ITVedas.com, a beginner-friendly IT education website. A visitor has answered a short quiz about their interests and work style. Your job is to recommend exactly ONE of these eight IT career paths based on their answers:

networking, cloud, security, devops, databases, linux, hardware, compliance

These map to ITVedas's own content chapters, so only ever pick one of these eight exact lowercase keys — never invent a new category.

Respond ONLY with valid JSON, no markdown formatting, no backticks, no preamble. Use exactly this shape:

{
  "chapter": "one of the eight keys above, lowercase",
  "explanation": "2-4 short sentences, written directly to the person (\\"you\\"), warm and specific, referencing at least one detail from their actual answers. No jargon. Explain WHY this path fits them specifically.",
  "next_steps": ["3 to 4 short, concrete, beginner-appropriate action items, each one sentence, ordered from easiest to start"]
}

Tone: encouraging, plain-spoken, like a knowledgeable friend — not corporate, not generic. Avoid hedging like "you might consider." Be direct about the recommendation while staying warm.`;

  const userPrompt = `Here are the quiz answers:\n\n${formattedQA}\n\nReturn the JSON object now.`;

  try {
    const claudeRes = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 600,
        system: systemPrompt,
        messages: [{ role: "user", content: userPrompt }]
      })
    });

    if (!claudeRes.ok) {
      const errText = await claudeRes.text();
      console.error("Claude API error:", claudeRes.status, errText);
      return jsonResponse({ error: "Analysis service error" }, 502);
    }

    const claudeData = await claudeRes.json();
    const rawText = (claudeData.content || [])
      .filter(block => block.type === "text")
      .map(block => block.text)
      .join("")
      .trim();

    const cleaned = rawText.replace(/^```json\s*/i, "").replace(/```$/, "").trim();

    let parsed;
    try {
      parsed = JSON.parse(cleaned);
    } catch {
      console.error("Failed to parse Claude response as JSON:", rawText);
      return jsonResponse({ error: "Could not parse analysis result" }, 502);
    }

    const chapter = VALID_CHAPTERS.includes(parsed.chapter) ? parsed.chapter : "networking";

    return jsonResponse({
      chapter,
      chapter_label: CHAPTER_LABELS[chapter],
      explanation: String(parsed.explanation || "").slice(0, 1000),
      next_steps: Array.isArray(parsed.next_steps) ? parsed.next_steps.slice(0, 5).map(s => String(s).slice(0, 300)) : []
    });

  } catch (err) {
    console.error("Career advice function error:", err);
    return jsonResponse({ error: "Unexpected server error" }, 500);
  }
}

// Reject non-POST methods explicitly
export async function onRequestGet() {
  return jsonResponse({ error: "Use POST" }, 405);
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}
