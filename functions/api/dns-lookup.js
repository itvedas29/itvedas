// functions/api/dns-lookup.js
//
// Cloudflare Pages Function — real DNS record lookups.
// Browser JavaScript has no DNS API, so this runs server-side. It always
// queries Cloudflare's own DNS-over-HTTPS resolver at a fixed hostname —
// it never connects to the domain being looked up, so user input only
// ever becomes a query parameter sent to cloudflare-dns.com. There is no
// SSRF surface: the fetch target is hardcoded regardless of input.

const ALLOWED_TYPES = new Set(["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "CAA"]);
const TYPE_CODES = { A: 1, NS: 2, CNAME: 5, SOA: 6, MX: 15, TXT: 16, AAAA: 28, CAA: 257 };

// RFC 1035 hostname shape: dot-separated labels of letters/digits/hyphens,
// 1-63 chars per label, no leading/trailing hyphen, <=253 chars overall.
const HOSTNAME_RE = /^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$/;

export async function onRequestGet(context) {
  const { request } = context;
  const url = new URL(request.url);
  const domain = (url.searchParams.get("domain") || "").trim().toLowerCase().replace(/\.$/, "");
  const type = (url.searchParams.get("type") || "A").toUpperCase();

  if (!domain || !HOSTNAME_RE.test(domain)) {
    return jsonResponse({ error: "Enter a valid domain name, e.g. example.com" }, 400);
  }
  if (!ALLOWED_TYPES.has(type)) {
    return jsonResponse({ error: `Unsupported record type. Use one of: ${[...ALLOWED_TYPES].join(", ")}` }, 400);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const doh = new URL("https://cloudflare-dns.com/dns-query");
    doh.searchParams.set("name", domain);
    doh.searchParams.set("type", type);

    const res = await fetch(doh.toString(), {
      headers: { accept: "application/dns-json" },
      signal: controller.signal
    });

    if (!res.ok) {
      return jsonResponse({ error: "Resolver error" }, 502);
    }

    const data = await res.json();
    const wantCode = TYPE_CODES[type];
    const records = (data.Answer || [])
      .filter(a => a.type === wantCode)
      .map(a => ({ name: a.name, ttl: a.TTL, data: a.data }));

    return jsonResponse({
      domain,
      type,
      status: dnsStatus(data.Status),
      records,
      resolver: "Cloudflare 1.1.1.1 (DNS-over-HTTPS)"
    });
  } catch (err) {
    if (err.name === "AbortError") {
      return jsonResponse({ error: "Lookup timed out" }, 504);
    }
    console.error("dns-lookup error:", err);
    return jsonResponse({ error: "Unexpected server error" }, 500);
  } finally {
    clearTimeout(timeout);
  }
}

export async function onRequestPost() {
  return jsonResponse({ error: "Use GET" }, 405);
}

function dnsStatus(code) {
  if (code === 0) return "NOERROR";
  if (code === 3) return "NXDOMAIN";
  return `RCODE_${code}`;
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" }
  });
}
