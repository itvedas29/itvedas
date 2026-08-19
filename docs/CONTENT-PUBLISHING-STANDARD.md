# ITVedas Content Publishing Standard

## Purpose and audience
Write for IT practitioners who need a correct, usable answer. State the task, operating context, prerequisites, risk, and verification before expanding into background theory.

## Required page structure
- Unique title, description, canonical URL, one H1, and visible last-reviewed date.
- A direct answer or outcome in the first screenful.
- Prerequisites, numbered procedure, validation/rollback or failure handling, and source links for time-sensitive claims.
- At least two contextual internal links: one upward to a pillar and one sideways to a related tool or task guide.
- Descriptive link text and meaningful alt text; do not use screenshots as the only explanation.
- No secrets, customer data, fabricated tests, copied vendor copy, or unverified security claims.

## Quality gates
Before publishing, verify:
1. The page has a distinct search intent and does not duplicate an existing URL.
2. Commands are labeled by shell/platform and are safe to copy.
3. Dates, versions, prices, CVE status, and product claims cite a primary source and include a review date.
4. Generated HTML has no markdown fences, broken internal URLs, or placeholder text.
5. The sitemap and search index regenerate successfully.

## Search Console-led refreshes
Prioritize pages with high impressions and low CTR (improve title/description), pages ranking 6–20 (add the missing task detail and internal links), then pages with declining clicks (refresh facts and examples). Preserve URLs unless there is a documented canonical consolidation with a permanent redirect.

## Measurement
Use the existing GA4 tag only. Event names and parameters must be non-PII, snake_case, and stable. Measure outcomes such as tool success and service-request completion—not keystrokes, raw search queries, email addresses, IP addresses, tokens, or article body content.
