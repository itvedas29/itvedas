/**
 * HTML Sanitizer - Safe DOM manipulation
 * Prevents XSS attacks by sanitizing user-generated content.
 *
 * This sanitizer is intentionally small and dependency-free because it is
 * also used by browser-only tools that render untrusted, user-supplied HTML.
 */

const HTMLSanitizer = (() => {
  const div = document.createElement('div');

  const ALLOWED_TAGS = {
    'a': ['href', 'title', 'target', 'rel'],
    'b': [],
    'blockquote': [],
    'br': [],
    'code': [],
    'em': [],
    'hr': [],
    'i': [],
    'li': [],
    'ol': [],
    'p': [],
    'pre': [],
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

  function sanitizeHTML(html) {
    if (!html || typeof html !== 'string') return '';

    div.innerHTML = html;
    const walker = document.createTreeWalker(div, NodeFilter.SHOW_ELEMENT, null, false);
    const nodesToRemove = [];
    let node;

    while (node = walker.nextNode()) {
      const tagName = node.tagName.toLowerCase();

      if (!ALLOWED_TAGS[tagName]) {
        nodesToRemove.push(node);
        continue;
      }

      // Snapshot attributes first because NamedNodeMap is live.
      const allowedAttrs = ALLOWED_TAGS[tagName];
      Array.from(node.attributes).forEach(attr => {
        if (!allowedAttrs.includes(attr.name.toLowerCase())) {
          node.removeAttribute(attr.name);
        }
      });

      if (tagName === 'a') {
        const href = node.getAttribute('href');
        if (href) {
          try {
            const url = new URL(href, window.location.origin);
            if (!['http:', 'https:'].includes(url.protocol)) {
              node.removeAttribute('href');
            }
          } catch {
            node.removeAttribute('href');
          }
        }

        // Never allow a new tab/window to retain an opener reference.
        if (node.getAttribute('target') === '_blank') {
          node.setAttribute('rel', 'noopener noreferrer');
        } else {
          node.removeAttribute('target');
          node.removeAttribute('rel');
        }
      }
    }

    nodesToRemove.forEach(n => n.remove());
    return div.innerHTML;
  }

  function setInnerHTML(element, html) {
    if (!element) return;
    element.innerHTML = sanitizeHTML(html);
  }

  function createTextNode(text) {
    return document.createTextNode(String(text || ''));
  }

  function setTextContent(element, text) {
    if (!element) return;
    element.textContent = String(text || '');
  }

  return {
    sanitizeHTML,
    setInnerHTML,
    createTextNode,
    setTextContent,

    createElement(tag, attrs = {}, content = '') {
      const el = document.createElement(tag);
      const allowed = ALLOWED_TAGS[tag.toLowerCase()] || [];
      for (const [key, value] of Object.entries(attrs)) {
        if (allowed.includes(key.toLowerCase())) {
          el.setAttribute(key, String(value));
        }
      }
      if (content) el.textContent = String(content);
      return el;
    }
  };
})();
