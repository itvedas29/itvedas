// functions/api/whois-lookup.js
//
// Cloudflare Pages Function — real domain registration lookups via RDAP
// (RFC 9083), the HTTP/JSON, IETF-standardized successor to WHOIS that
// ICANN has required all gTLD registries/registrars to support since 2023.
//
// This intentionally does NOT speak raw WHOIS (TCP port 43): an earlier
// version of this file used the Workers TCP Sockets API (`cloudflare:
// sockets`) and worked in local `wrangler pages dev`, but production
// Cloudflare Pages Functions returned a bare 502 for every request --
// Pages Functions don't support that API the way standalone Workers do.
// RDAP is plain HTTP, so it works the same way dns-lookup.js and
// my-ip.js's own fetch-based lookups do, and as a bonus returns
// structured JSON instead of registry-specific free-text formats that
// need per-registry regex scraping.
//
// Flow: fetch IANA's official RDAP bootstrap registry to find which RDAP
// server is authoritative for the domain's TLD, then query that server
// directly. No second-hop referral is needed (unlike thin WHOIS) since
// ICANN's RDAP profile requires registries to return full registrar and
// contact data in one response.

// RFC 1035 hostname shape: dot-separated labels of letters/digits/hyphens,
// 1-63 chars per label, no leading/trailing hyphen, <=253 chars overall.
const HOSTNAME_RE = /^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$/;

const RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json";
const FETCH_TIMEOUT_MS = 6000;

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
    const rdapBase = await getRdapBase(tld);
    if (!rdapBase) {
      return jsonResponse({
        error: `No RDAP/WHOIS service is registered for .${tld}. Try ICANN Lookup (lookup.icann.org) instead.`
      }, 404);
    }

    const domainUrl = `${rdapBase}domain/${encodeURIComponent(domain)}`;
    const { status, ok, text } = await fetchRdapDomainWithRetry(domainUrl);

    if (status === 404) {
      return jsonResponse({
        domain,
        rdapServer: rdapBase,
        queryTimeMs: Date.now() - started,
        notFound: true,
        summary: {},
        raw: text ? prettyJson(text) : "(registry sent no response body for this 404)"
      });
    }
    if (!ok) {
      return jsonResponse({
        error: `The registry's RDAP server returned an error (HTTP ${status}). Please try again.`
      }, 502);
    }

    return jsonResponse({
      domain,
      rdapServer: rdapBase,
      queryTimeMs: Date.now() - started,
      summary: extractSummary(JSON.parse(text)),
      raw: prettyJson(text)
    });
  } catch (err) {
    if (err.name === "AbortError") {
      return jsonResponse({ error: "Lookup timed out. Please try again." }, 504);
    }
    console.error("whois-lookup error:", err);
    return jsonResponse({ error: "Unexpected error while querying the registry." }, 500);
  }
}

export async function onRequestPost() {
  return jsonResponse({ error: "Use GET" }, 405);
}

async function getRdapBase(tld) {
  const res = await fetchWithTimeout(RDAP_BOOTSTRAP_URL, {
    cf: { cacheTtl: 3600, cacheEverything: true }
  });
  if (!res.ok) return null;

  const data = await res.json();
  for (const [tlds, urls] of data.services || []) {
    if (Array.isArray(tlds) && tlds.some(t => t.toLowerCase() === tld) && urls && urls.length) {
      return urls[0].endsWith("/") ? urls[0] : urls[0] + "/";
    }
  }
  return null;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = FETCH_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function fetchRdapDomain(url) {
  const res = await fetchWithTimeout(url, { headers: { accept: "application/rdap+json" } });
  const status = res.status;
  const ok = res.ok;

  try {
    return { status, ok, text: await res.text() };
  } catch (bodyErr) {
    // Confirmed against rdap.verisign.com: it sends 404s with no
    // Content-Length/chunked framing and closes the TLS connection
    // without a clean close_notify, so strict HTTP clients (this
    // includes Cloudflare's own fetch, not just local dev) fail to read
    // the body even though the status arrived fine. The status code
    // alone is a complete answer for a non-2xx result, so degrade to an
    // empty body instead of failing the whole lookup. A 2xx response we
    // can't read at all has no data to give back, so that's a real
    // failure worth retrying/surfacing.
    if (!ok) return { status, ok, text: "" };
    throw bodyErr;
  }
}

async function fetchRdapDomainWithRetry(url, attempts = 2) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fetchRdapDomain(url);
    } catch (err) {
      lastErr = err;
      if (err.name === "AbortError") throw err;
    }
  }
  throw lastErr;
}

function prettyJson(text) {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

function vcardField(vcardArray, field) {
  if (!Array.isArray(vcardArray) || !Array.isArray(vcardArray[1])) return null;
  const entry = vcardArray[1].find(e => Array.isArray(e) && e[0] === field);
  return entry && entry.length > 3 ? entry[3] : null;
}

function extractSummary(data) {
  const summary = {};

  const registrar = (data.entities || []).find(e => (e.roles || []).includes("registrar"));
  if (registrar) {
    const name = vcardField(registrar.vcardArray, "fn");
    if (name) summary.registrar = name;
    const urlEntry = (registrar.links || []).find(l => l.type === "text/html") || (registrar.links || [])[0];
    if (urlEntry && urlEntry.href) summary.registrarUrl = urlEntry.href;
  }

  const events = data.events || [];
  const eventDate = action => events.find(e => e.eventAction === action)?.eventDate;
  const created = eventDate("registration");
  const updated = eventDate("last changed");
  const expiry = eventDate("expiration");
  if (created) summary.createdDate = created;
  if (updated) summary.updatedDate = updated;
  if (expiry) summary.expiryDate = expiry;

  if (data.secureDNS) {
    summary.dnssec = data.secureDNS.delegationSigned ? "signed" : "unsigned";
  }

  if (Array.isArray(data.nameservers) && data.nameservers.length) {
    const names = data.nameservers.map(ns => (ns.ldhName || "").toLowerCase()).filter(Boolean);
    if (names.length) summary.nameServers = names;
  }

  if (Array.isArray(data.status) && data.status.length) {
    summary.statuses = data.status;
  }

  return summary;
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" }
  });
}
