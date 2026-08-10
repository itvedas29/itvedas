// functions/api/whois-lookup.js
//
// Cloudflare Pages Function — real WHOIS lookups over raw TCP (port 43),
// using the Workers TCP Sockets API. WHOIS has no HTTP API, so this can't
// reuse the DoH pattern from dns-lookup.js; it speaks the WHOIS protocol
// directly.
//
// Flow: ask IANA's root WHOIS server which registry server owns the
// domain's TLD, query that registry, and if the registry response refers
// to a more specific server (the common "thin WHOIS" model for .com/.net,
// where the registry only stores which registrar holds the domain) follow
// that referral once more. Every hostname involved -- the input domain and
// every referral target -- is validated against the same strict hostname
// shape before it's ever written to a socket or connected to, so nothing
// user- or registry-supplied can inject extra WHOIS commands or steer a
// connection somewhere unexpected.

import { connect } from "cloudflare:sockets";

// RFC 1035 hostname shape: dot-separated labels of letters/digits/hyphens,
// 1-63 chars per label, no leading/trailing hyphen, <=253 chars overall.
const HOSTNAME_RE = /^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$/;

const IANA_WHOIS = "whois.iana.org";
const MAX_RESPONSE_BYTES = 200_000;
const HOP_TIMEOUT_MS = 6000;

// whois.iana.org is a single shared root server every lookup would
// otherwise hit first -- under repeated/concurrent traffic it intermittently
// rate-limits and returns an empty referral (confirmed while testing this
// tool: identical queries succeeded, then failed, then succeeded again
// within a couple minutes with no change on our end). For .com/.net/.org --
// which cover the large majority of real lookups -- short-circuiting IANA
// with their long-standing, essentially static registry hostnames removes
// that shared bottleneck entirely. Every other TLD still asks IANA
// dynamically (with a retry below) rather than risking a hand-maintained
// map going stale for less-common TLDs.
const KNOWN_REGISTRY_SERVERS = {
  com: "whois.verisign-grs.com",
  net: "whois.verisign-grs.com",
  org: "whois.publicinterestregistry.org"
};

export async function onRequestGet(context) {
  const { request } = context;
  const url = new URL(request.url);
  const domain = (url.searchParams.get("domain") || "").trim().toLowerCase().replace(/\.$/, "");

  if (!domain) {
    return jsonResponse({ error: "Enter a domain name, e.g. example.com" }, 400);
  }
  if (!HOSTNAME_RE.test(domain) || !domain.includes(".")) {
    return jsonResponse({ error: "Enter a valid registered domain, e.g. example.com" }, 400);
  }

  const tld = domain.split(".").pop();
  const started = Date.now();

  try {
    let registryHost = KNOWN_REGISTRY_SERVERS[tld];
    if (!registryHost) {
      registryHost = extractReferral(await queryWhois(IANA_WHOIS, tld));
      if (!registryHost) {
        // whois.iana.org occasionally returns an empty/referral-less
        // response under light repeated load rather than a hard error --
        // one retry after a short pause reliably recovers from that.
        await new Promise(r => setTimeout(r, 1200));
        registryHost = extractReferral(await queryWhois(IANA_WHOIS, tld));
      }
    }
    if (!registryHost) {
      return jsonResponse({
        error: `No public WHOIS server is registered for .${tld}. Try ICANN Lookup (lookup.icann.org) or your registry's RDAP service instead.`
      }, 404);
    }

    const registryText = await queryWhois(registryHost, domain);
    if (!registryText.trim()) {
      return jsonResponse({
        error: `${registryHost} didn't return any data (it may be rate-limiting or temporarily unavailable). Please try again in a moment.`
      }, 502);
    }

    let whoisServer = registryHost;
    let raw = registryText;

    const registrarHost = extractReferral(registryText);
    if (registrarHost && registrarHost !== registryHost) {
      try {
        const registrarText = await queryWhois(registrarHost, domain);
        if (registrarText.trim()) {
          raw = registrarText;
          whoisServer = registrarHost;
        }
      } catch {
        // Registrar-level server refused/timed out -- the registry-level
        // response we already have is still a valid, useful answer.
      }
    }

    return jsonResponse({
      domain,
      whoisServer,
      queryTimeMs: Date.now() - started,
      summary: extractSummary(raw),
      raw
    });
  } catch (err) {
    if (err.message === "TIMEOUT") {
      return jsonResponse({ error: "WHOIS server did not respond in time. Please try again." }, 504);
    }
    console.error("whois-lookup error:", err);
    return jsonResponse({ error: "Unexpected error while querying WHOIS." }, 500);
  }
}

export async function onRequestPost() {
  return jsonResponse({ error: "Use GET" }, 405);
}

async function queryWhois(host, query, timeoutMs = HOP_TIMEOUT_MS) {
  const socket = connect({ hostname: host, port: 43 });
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    socket.close().catch(() => {});
  }, timeoutMs);

  try {
    const writer = socket.writable.getWriter();
    await writer.write(new TextEncoder().encode(query + "\r\n"));
    await writer.close();

    const reader = socket.readable.getReader();
    const decoder = new TextDecoder();
    let result = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      result += decoder.decode(value, { stream: true });
      if (result.length > MAX_RESPONSE_BYTES) break;
    }

    if (timedOut) throw new Error("TIMEOUT");
    return result;
  } finally {
    clearTimeout(timer);
    socket.close().catch(() => {});
  }
}

function extractReferral(text) {
  const patterns = [
    /^\s*whois\s*:\s*(\S+)/im,
    /^\s*refer\s*:\s*(\S+)/im,
    /^\s*registrar whois server\s*:\s*(?:whois:\/\/)?(\S+)/im,
    /^\s*referralserver\s*:\s*whois:\/\/(\S+)/im
  ];
  for (const re of patterns) {
    const m = text.match(re);
    const candidate = m && m[1] ? m[1].toLowerCase().replace(/\/$/, "") : null;
    if (candidate && HOSTNAME_RE.test(candidate) && candidate.includes(".")) return candidate;
  }
  return null;
}

// Registry-level responses (e.g. Verisign's whois.verisign-grs.com) indent
// every line with leading spaces; registrar-level responses often don't --
// "^\s*" before each field name handles both.
const SUMMARY_FIELDS = [
  ["registrar", /^\s*registrar:\s*(.+)$/im],
  ["registrarUrl", /^\s*registrar url:\s*(.+)$/im],
  ["createdDate", /^\s*(?:creation date|created(?: on)?|domain registration date)\s*:\s*(.+)$/im],
  ["updatedDate", /^\s*(?:updated date|last updated(?: on)?|domain last updated date)\s*:\s*(.+)$/im],
  ["expiryDate", /^\s*(?:registry expiry date|registrar registration expiration date|expiration date|expiry date|paid-till)\s*:\s*(.+)$/im],
  ["dnssec", /^\s*dnssec:\s*(.+)$/im]
];

function extractSummary(text) {
  const summary = {};
  for (const [key, re] of SUMMARY_FIELDS) {
    const m = text.match(re);
    if (m) summary[key] = m[1].trim();
  }

  const nameServers = [...text.matchAll(/^\s*name server:\s*(.+)$/gim)]
    .map(m => m[1].trim().toLowerCase())
    .filter((v, i, arr) => v && arr.indexOf(v) === i);
  if (nameServers.length) summary.nameServers = nameServers;

  const statuses = [...text.matchAll(/^\s*domain status:\s*(.+)$/gim)]
    .map(m => m[1].trim())
    .filter((v, i, arr) => v && arr.indexOf(v) === i);
  if (statuses.length) summary.statuses = statuses;

  return summary;
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" }
  });
}
