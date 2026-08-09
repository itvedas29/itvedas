// functions/api/my-ip.js
//
// Cloudflare Pages Function — returns the visitor's own public IP and
// coarse network info, as seen by Cloudflare's edge. Accepts no user
// input and makes no outbound requests, so there is no SSRF, injection,
// or abuse surface at all.

export async function onRequestGet(context) {
  const { request } = context;
  const cf = request.cf || {};
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";

  return new Response(JSON.stringify({
    ip,
    country: cf.country || null,
    region: cf.region || null,
    city: cf.city || null,
    postalCode: cf.postalCode || null,
    timezone: cf.timezone || null,
    asn: cf.asn || null,
    asOrganization: cf.asOrganization || null,
    colo: cf.colo || null
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
