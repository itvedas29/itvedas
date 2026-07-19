/**
 * HTML Sanitizer - Safe DOM manipulation
 * Prevents XSS attacks by sanitizing user-generated content
 */

const HTMLSanitizer = (() => {
  // Create a safe element for parsing
  const div = document.createElement('div');

  // Allowed tags for sanitization
  const ALLOWED_TAGS = {
    'a': ['href', 'title', 'target'],
    'b': [],
    'br': [],
    'em': [],
    'i': [],
    'li': [],
    'ol': [],
    'p': [],
    'span': ['class'],
    'strong': [],
    'ul': [],
    'h1': [],
    'h2': [],
    'h3': [],
    'h4': [],
    'h5': [],
    'h6': []
  };

  /**
   * Sanitize HTML string by stripping dangerous tags
   * @param {string} html - HTML string to sanitize
   * @returns {string} Safe HTML string
   */
  function sanitizeHTML(html) {
    if (!html || typeof html !== 'string') return '';

    div.innerHTML = html;
    const walker = document.createTreeWalker(
      div,
      NodeFilter.SHOW_ELEMENT,
      null,
      false
    );

    const nodesToRemove = [];
    let node;

    while (node = walker.nextNode()) {
      const tagName = node.tagName.toLowerCase();

      if (!ALLOWED_TAGS[tagName]) {
        nodesToRemove.push(node);
        continue;
      }

      // Remove disallowed attributes
      const allowedAttrs = ALLOWED_TAGS[tagName];
      for (let attr of node.attributes) {
        if (!allowedAttrs.includes(attr.name)) {
          node.removeAttribute(attr.name);
        }
      }

      // Validate href for links
      if (tagName === 'a' && node.href) {
        try {
          const url = new URL(node.href, window.location.origin);
          // Only allow http, https, and relative URLs
          if (!['http:', 'https:', ''].includes(url.protocol)) {
            node.removeAttribute('href');
          }
        } catch {
          node.removeAttribute('href');
        }
      }
    }

    // Remove disallowed nodes
    nodesToRemove.forEach(n => n.remove());

    return div.innerHTML;
  }

  /**
   * Safely insert HTML into a DOM element
   * @param {Element} element - Target element
   * @param {string} html - HTML to insert
   */
  function setInnerHTML(element, html) {
    if (!element) return;
    const clean = sanitizeHTML(html);
    element.innerHTML = clean;
  }

  /**
   * Create a safe text node
   * @param {string} text - Text content
   * @returns {Text} Text node
   */
  function createTextNode(text) {
    return document.createTextNode(String(text || ''));
  }

  /**
   * Safely set element text content
   * @param {Element} element - Target element
   * @param {string} text - Text content
   */
  function setTextContent(element, text) {
    if (!element) return;
    element.textContent = String(text || '');
  }

  return {
    sanitizeHTML,
    setInnerHTML,
    createTextNode,
    setTextContent,

    /**
     * Create a safe element with attributes
     * @param {string} tag - Tag name
     * @param {Object} attrs - Attributes object
     * @param {string} content - Text content
     * @returns {Element} Created element
     */
    createElement(tag, attrs = {}, content = '') {
      const el = document.createElement(tag);

      // Set allowed attributes
      const allowed = ALLOWED_TAGS[tag.toLowerCase()] || [];
      for (const [key, value] of Object.entries(attrs)) {
        if (allowed.includes(key)) {
          el.setAttribute(key, String(value));
        }
      }

      if (content) {
        el.textContent = String(content);
      }

      return el;
    }
  };
})();
