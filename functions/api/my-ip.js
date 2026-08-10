// functions/api/my-ip.js
//
// Cloudflare Pages Function — returns the visitor's own public IP,
// coarse network info, connection details, and reverse DNS, as seen by
// Cloudflare's edge. Accepts no user input from the request body/query
// (the only "input" is the visitor's own IP, read from a Cloudflare
// header, not user-suppliable) so there is no SSRF or injection surface.
// The one outbound call (reverse DNS) always targets a fixed resolver
// hostname, same as functions/api/dns-lookup.js.

export async function onRequestGet(context) {
  const { request } = context;
  const cf = request.cf || {};
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";

  const reverseDns = ip !== "unknown" ? await reverseLookup(ip) : null;

  return new Response(JSON.stringify({
    ip,
    reverseDns,
    country: cf.country || null,
    region: cf.region || null,
    city: cf.city || null,
    postalCode: cf.postalCode || null,
    timezone: cf.timezone || null,
    asn: cf.asn || null,
    asOrganization: cf.asOrganization || null,
    colo: cf.colo || null,
    httpProtocol: cf.httpProtocol || null,
    tlsVersion: cf.tlsVersion || null,
    tlsCipher: cf.tlsCipher || null
  }), {
    status: 200,
    headers: { "content-type": "application/json", "cache-control": "no-store" }
  });
}

export async function onRequestPost() {
  return new Response(JSON.stringify({ error: "Use GET" }), {
    status: 405,
    headers: { "content-type": "application/json" }
  });
}

function toArpaName(ip) {
  if (/^(\d{1,3}\.){3}\d{1,3}$/.test(ip)) {
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

async function reverseLookup(ip) {
  const arpaName = toArpaName(ip);
  if (!arpaName) return null;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);

  try {
    const doh = new URL("https://cloudflare-dns.com/dns-query");
    doh.searchParams.set("name", arpaName);
    doh.searchParams.set("type", "PTR");

    const res = await fetch(doh.toString(), {
      headers: { accept: "application/dns-json" },
      signal: controller.signal
    });
    if (!res.ok) return null;

    const data = await res.json();
    const ptr = (data.Answer || []).find(a => a.type === 12);
    return ptr ? ptr.data.replace(/\.$/, "") : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}
