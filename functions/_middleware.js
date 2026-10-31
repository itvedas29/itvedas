// functions/_middleware.js
//
// Cloudflare Pages deploys the repository root as the site, so pipeline code,
// tests, internal docs and config would otherwise be downloadable. _routes.json
// sends /api/* plus exactly those non-site paths to Functions; static pages
// never reach this file. Anything here that isn't an API call gets the site's
// 404 page with a real 404 status. To hide another path, add it to the
// "include" list in _routes.json.

export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.pathname.startsWith("/api/")) {
    return context.next();
  }

  const page = await context.env.ASSETS.fetch(new URL("/404", url));
  return new Response(page.ok ? page.body : "Not found", {
    status: 404,
    headers: {
      "Content-Type": page.ok ? "text/html; charset=utf-8" : "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex"
    }
  });
}
