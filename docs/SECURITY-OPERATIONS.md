# ITVedas Security Operations

## Production checklist

### Cloudflare Pages
- Keep the `RATE_LIMIT_KV` binding configured for `/api/career-advice`.
- Review Cloudflare WAF/rate-limiting events monthly.
- Keep HSTS enabled.

### GitHub Actions
- Workflows should use `contents: read` unless they publish generated files.
- Publishing workflows should use a single bot identity and avoid force pushes.
- Pull-request validation must pass before merging.

### Third-party scripts
- GA4 `gtag.js` must not use fixed SRI hashes because the resource is mutable.
- Keep third-party origins explicit in `_headers` CSP.

### AI endpoints
- Never expose provider API keys to client-side JavaScript.
- Enforce request size/count limits before calling a paid provider.
- Use Cloudflare KV rate limiting in production.

### Generated content
- News passes the quality gate before sitemap generation.
- Noindex pages remain accessible to users but are excluded from XML sitemap discovery.
- CVE data is generated from the single unified pipeline.
