# ITVedas Platform Operating Strategy

## Product position
ITVedas is an IT engineer utility and knowledge platform: each tool solves a practical task, each guide explains the decision behind it, and services support teams that need implementation help.

## Operating model
1. **Tools:** Prioritize safe, browser-first utilities in Network Operations, Security Operations, Windows/Microsoft, Cloud/DevOps, and Data/Format. Every tool needs a clear input boundary, privacy note, empty/error states, accessible labels, one related guide, and one event call to `ITVedasAnalytics.trackToolUse()` when a calculation/query succeeds.
2. **Knowledge:** Build topic clusters around operational intent: diagnose, configure, secure, automate, and recover. A pillar page links to task guides; task guides link back to the pillar and to a relevant tool.
3. **Services:** Convert high-intent demand through a clearly scoped website-development and IT-operations support offer: discovery, technical SEO/performance, Cloudflare/edge deployment, analytics instrumentation, documentation, and ongoing care. Service claims must name deliverables, constraints, response expectations, and a contact path.
4. **Measurement:** GA4 remains the existing `G-D98BFZSJYP` implementation. The event layer sends no PII and records `tool_open`, `tool_used`, `site_search`, `article_cta_click`, `service_interest`, `service_request`, and `newsletter_submit`. Use Search Console landing pages and queries to choose content refreshes; never use GA4 event parameters to transmit query text, emails, IPs, or tokens.

## Weekly operator cadence
- Review GA4: tool opens/uses, service interest, engagement by landing page.
- Review Search Console: rising queries, pages with high impressions but low CTR, crawl/index coverage.
- Publish or refresh one operational cluster page, then add internal links from its pillar and tool.
- Validate generated content, sitemap and search index before merging.
- Review Cloudflare Function logs for timeout/error changes and abuse patterns.

## 90-day sequencing
- **Days 1–30:** Stabilize the tools hub; add task-oriented landing pages for Network Operations, Security Operations, and Windows/Microsoft; establish GA4 custom dimensions for `tool_name`, `tool_category`, and `page_type`.
- **Days 31–60:** Expand tool-to-guide pairs and launch an explicit website-development support page with a structured intake form.
- **Days 61–90:** Refresh pages selected by Search Console opportunity, publish case-study-style operational playbooks, and turn qualified service actions into GA4 key events.

## Definition of done for a new tool
A tool is launch-ready only when it works without credentials, has input validation and bounded external calls, is keyboard accessible, has a canonical URL and unique metadata, links to relevant guidance, emits a non-PII success event, and passes the static-site checks.
