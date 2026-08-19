/* ITVedas GA4 event layer.
 * This file never installs GA4 or creates a measurement ID. It only uses the
 * site's existing gtag() instance (G-D98BFZSJYP) when it is available.
 * Do not send email addresses, search text, IP addresses, tokens, or other PII.
 */
(function (window, document) {
  "use strict";

  function clean(value, maxLength) {
    return String(value || "")
      .replace(/[^a-zA-Z0-9 _./:-]/g, "")
      .trim()
      .slice(0, maxLength || 100);
  }

  function pageType() {
    var path = window.location.pathname;
    if (path.indexOf("/tools/") === 0) return "tool";
    if (path.indexOf("/articles/") === 0) return "article";
    if (path.indexOf("/news/") === 0 || path === "/news") return "news";
    if (path.indexOf("/services") === 0) return "service";
    return "site";
  }

  function send(name, params) {
    if (typeof window.gtag !== "function") return false;
    var payload = Object.assign({ page_type: pageType() }, params || {});
    window.gtag("event", name, payload);
    return true;
  }

  function toolName(element, href) {
    var label = element.getAttribute("data-tool-name") ||
      element.getAttribute("aria-label") ||
      element.textContent ||
      href.split("/").filter(Boolean).pop() ||
      "unknown";
    return clean(label, 80).toLowerCase().replace(/\s+/g, "_");
  }

  function trackLink(event) {
    var link = event.target.closest("a, [data-href]");
    if (!link) return;
    var href = link.getAttribute("href") || link.getAttribute("data-href") || "";
    if (!href) return;

    if (/^\/tools\//.test(href)) {
      send("tool_open", { tool_name: toolName(link, href), tool_category: clean((link.closest("[data-category]") || {}).getAttribute && link.closest("[data-category]").getAttribute("data-category"), 40) || "unknown" });
    } else if (/^\/services(?:\/|$)/.test(href)) {
      send("service_interest", { service_name: toolName(link, href) });
    } else if (/^\/articles\//.test(href)) {
      send("article_cta_click", { destination_path: clean(href, 100) });
    }
  }

  function trackSearch(event) {
    if (event.key !== "Enter") return;
    var input = event.target;
    if (!input.matches("input[type='search'], #searchInput, #toolSearch, [data-analytics-search]")) return;
    // Intentionally report only that a search occurred, never its query.
    send("site_search", { search_area: clean(input.id || input.name || "site", 40) });
  }

  function init() {
    document.addEventListener("click", trackLink, true);
    document.addEventListener("keydown", trackSearch, true);
    document.addEventListener("submit", function (event) {
      var form = event.target;
      if (form.matches("[data-analytics-form='service-request']")) send("service_request");
      if (form.matches("[data-analytics-form='newsletter']")) send("newsletter_submit");
    }, true);
  }

  window.ITVedasAnalytics = {
    track: send,
    trackToolUse: function (name, category) {
      return send("tool_used", { tool_name: clean(name, 80), tool_category: clean(category, 40) || "unknown" });
    }
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})(window, document);
