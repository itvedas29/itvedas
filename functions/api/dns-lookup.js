// functions/api/dns-lookup.js
//
// Cloudflare Pages Function — real DNS record lookups, plus reverse
// (PTR) lookups and an "all types" mode. Browser JavaScript has no DNS
// API, so this runs server-side. It always queries Cloudflare's own
// DNS-over-HTTPS resolver at a fixed hostname — it never connects to
// the domain being looked up, so user input only ever becomes a query
// parameter sent to cloudflare-dns.com. There is no SSRF surface: the
// fetch target is hardcoded regardless of input.

const ALLOWED_TYPES = new Set(["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "CAA", "PTR"]);
const TYPE_CODES = { A: 1, NS: 2, CNAME: 5, SOA: 6, PTR: 12, MX: 15, TXT: 16, AAAA: 28, CAA: 257 };
const ALL_TYPES = ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "CAA"];

// RFC 1035 hostname shape: dot-separated labels of letters/digits/hyphens,
// 1-63 chars per label, no leading/trailing hyphen, <=253 chars overall.
const HOSTNAME_RE = /^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$/;
const IPV4_RE = /^(\d{1,3}\.){3}\d{1,3}$/;

export async function onRequestGet(context) {
  const { request } = context;
  const url = new URL(request.url);
  const rawInput = (url.searchParams.get("domain") || "").trim().toLowerCase().replace(/\.$/, "");
  const type = (url.searchParams.get("type") || "A").toUpperCase();

  if (!rawInput) {
    return jsonResponse({ error: "Enter a domain name, e.g. example.com" }, 400);
  }
  if (type !== "ALL" && !ALLOWED_TYPES.has(type)) {
    return jsonResponse({ error: `Unsupported record type. Use one of: ${[...ALLOWED_TYPES].join(", ")}, ALL` }, 400);
  }

  let queryName = rawInput;
  let isReverse = false;

  if (type === "PTR") {
    const arpaName = toArpaName(rawInput);
    if (!arpaName) {
      return jsonResponse({ error: "For PTR lookups, enter a valid IPv4 or IPv6 address" }, 400);
    }
    queryName = arpaName;
    isReverse = true;
  } else if (!HOSTNAME_RE.test(rawInput)) {
    return jsonResponse({ error: "Enter a valid domain name, e.g. example.com" }, 400);
  }

  const started = Date.now();

  try {
    if (type === "ALL") {
      const results = await Promise.all(ALL_TYPES.map(t => queryDoh(queryName, t)));
      const byType = {};
      let dnssecValidated = false;
      for (let i = 0; i < ALL_TYPES.length; i++) {
        const r = results[i];
        if (r.error) continue;
        byType[ALL_TYPES[i]] = { status: dnsStatus(r.data.Status), records: extractRecords(r.data, ALL_TYPES[i]) };
        if (r.data.AD) dnssecValidated = true;
      }
      return jsonResponse({
        domain: rawInput,
        type: "ALL",
        queryTimeMs: Date.now() - started,
        dnssecValidated,
        results: byType,
        resolver: "Cloudflare 1.1.1.1 (DNS-over-HTTPS)"
      });
    }

    const result = await queryDoh(queryName, type);
    if (result.error) {
      return jsonResponse({ error: result.error }, result.status || 502);
    }

    return jsonResponse({
      domain: rawInput,
      type,
      queryTimeMs: Date.now() - started,
      status: dnsStatus(result.data.Status),
      dnssecValidated: !!result.data.AD,
      isReverse,
      records: extractRecords(result.data, type),
      resolver: "Cloudflare 1.1.1.1 (DNS-over-HTTPS)"
    });
  } catch (err) {
    if (err.name === "AbortError") {
      return jsonResponse({ error: "Lookup timed out" }, 504);
    }
    console.error("dns-lookup error:", err);
    return jsonResponse({ error: "Unexpected server error" }, 500);
  }
}

export async function onRequestPost() {
  return jsonResponse({ error: "Use GET" }, 405);
}

async function queryDoh(name, type) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const doh = new URL("https://cloudflare-dns.com/dns-query");
    doh.searchParams.set("name", name);
    doh.searchParams.set("type", type);

    const res = await fetch(doh.toString(), {
      headers: { accept: "application/dns-json" },
      signal: controller.signal
    });
    if (!res.ok) return { error: "Resolver error", status: 502 };

    const data = await res.json();
    return { data };
  } catch (err) {
    if (err.name === "AbortError") return { error: "Lookup timed out", status: 504 };
    return { error: "Unexpected resolver error", status: 500 };
  } finally {
    clearTimeout(timeout);
  }
}

function extractRecords(data, type) {
  const wantCode = TYPE_CODES[type];
  return (data.Answer || [])
    .filter(a => a.type === wantCode)
    .map(a => ({ name: a.name, ttl: a.TTL, data: a.data }));
}

function toArpaName(ip) {
  if (IPV4_RE.test(ip)) {
    const parts = ip.split(".");
    if (parts.some(p => Number(p) > 255)) return null;
    return parts.reverse().join(".") + ".in-addr.arpa";
  }

  if (ip.includes(":")) {
    let groups;
    if (ip.includes("::")) {
      const [head, tail] = ip.split("::");
      const headParts = head ? head.split(":") : [];
      const tailParts = tail ? tail.split(":") : [];
      const missing = 8 - headParts.length - tailParts.length;
      if (missing < 0) return null;
      groups = [...headParts, ...Array(missing).fill("0"), ...tailParts];
    } else {
      groups = ip.split(":");
    }
    if (groups.length !== 8 || groups.some(g => !/^[0-9a-fA-F]{1,4}$/.test(g))) return null;

    const hex = groups.map(g => g.padStart(4, "0")).join("").toLowerCase();
    return hex.split("").reverse().join(".") + ".ip6.arpa";
  }

  return null;
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
