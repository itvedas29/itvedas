/**
 * Breadcrumb Navigation Generator
 * Automatically generates breadcrumb trails based on URL hierarchy and content type
 */

const BreadcrumbGenerator = (() => {
  // Map URLs to breadcrumb hierarchy
  const urlMap = {
    // Root
    '': { label: 'Home', path: '/' },

    // Main sections
    'index.html': { label: 'Home', path: '/' },
    'chapters.html': { label: 'Chapters', path: '/chapters.html' },
    'about.html': { label: 'About', path: '/about.html' },
    'cve-listing.html': { label: 'CVE Database', path: '/cve-listing.html' },
    'cve-detail.html': { label: 'CVE Details', path: '/cve-listing.html' },

    // Article sections
    'articles/': { label: 'Articles', path: '/articles/' },
    'articles/networking/': { label: 'Networking', path: '/articles/networking/', parent: 'articles/' },
    'articles/cloud/': { label: 'Cloud', path: '/articles/cloud/', parent: 'articles/' },
    'articles/security/': { label: 'Security', path: '/articles/security/', parent: 'articles/' },
    'articles/devops/': { label: 'DevOps', path: '/articles/devops/', parent: 'articles/' },
    'articles/cve/': { label: 'CVE Explained', path: '/articles/cve/', parent: 'articles/' },
    'articles/databases/': { label: 'Databases', path: '/articles/databases/', parent: 'articles/' },
    'articles/linux/': { label: 'Linux', path: '/articles/linux/', parent: 'articles/' },
    'articles/hardware/': { label: 'Hardware', path: '/articles/hardware/', parent: 'articles/' },
    'articles/compliance/': { label: 'Compliance', path: '/articles/compliance/', parent: 'articles/' },

    // Chapter sections
    'chapters/': { label: 'Chapters', path: '/chapters.html' },
    'chapters/cloud/': { label: 'Cloud', path: '/chapters/', parent: 'chapters/' },
    'chapters/networking/': { label: 'Networking', path: '/chapters/', parent: 'chapters/' },
    'chapters/security/': { label: 'Security', path: '/chapters/', parent: 'chapters/' },
    'chapters/devops/': { label: 'DevOps', path: '/chapters/', parent: 'chapters/' },
    'chapters/servers/': { label: 'Servers', path: '/chapters/', parent: 'chapters/' },
    'chapters/linux/': { label: 'Linux', path: '/chapters/', parent: 'chapters/' },

    // News
    'news/': { label: 'News', path: '/news.html' },
  };

  /**
   * Get breadcrumb trail for current page
   * @param {string} currentPath - Current page path (relative or absolute)
   * @returns {Array} Array of breadcrumb items
   */
  function getBreadcrumb(currentPath = window.location.pathname) {
    const breadcrumbs = [
      { label: 'Home', path: '/' }
    ];

    // Remove trailing slashes and normalize path
    currentPath = currentPath.replace(/^\//, '').replace(/\/$/, '');

    if (!currentPath || currentPath === 'index.html') {
      return breadcrumbs;
    }

    // Extract path segments
    const segments = currentPath.split('/');
    let accumulatedPath = '';

    for (let i = 0; i < segments.length - 1; i++) {
      accumulatedPath += segments[i] + '/';
      if (urlMap[accumulatedPath]) {
        const breadcrumb = urlMap[accumulatedPath];
        breadcrumbs.push({
          label: breadcrumb.label,
          path: breadcrumb.path
        });
      }
    }

    // Add current page based on title or filename
    const filename = segments[segments.length - 1];
    const pageTitle = extractPageTitle();

    if (filename && filename !== 'index.html') {
      breadcrumbs.push({
        label: pageTitle,
        path: currentPath,
        current: true
      });
    }

    return breadcrumbs;
  }

  /**
   * Extract page title from meta tags or h1
   */
  function extractPageTitle() {
    // Try og:title first (most descriptive)
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      let title = ogTitle.content;
      // Remove " | ITVedas" suffix if present
      title = title.split(' | ')[0];
      return title;
    }

    // Fallback to title tag
    const titleTag = document.querySelector('title');
    if (titleTag) {
      let title = titleTag.innerText;
      title = title.split(' | ')[0];
      return title;
    }

    // Fallback to h1
    const h1 = document.querySelector('h1');
    if (h1) {
      return h1.innerText.split(' | ')[0];
    }

    return 'Page';
  }

  /**
   * Render breadcrumb HTML
   * @param {Array} breadcrumbs - Array of breadcrumb items
   * @param {string} containerId - ID of container element (optional)
   */
  function render(breadcrumbs, containerId) {
    if (!breadcrumbs || breadcrumbs.length === 0) {
      return '';
    }

    let html = '<nav class="breadcrumb" aria-label="Breadcrumb">';
    html += '<ol class="breadcrumb-list">';

    breadcrumbs.forEach((crumb, index) => {
      const isLast = index === breadcrumbs.length - 1;

      if (isLast || crumb.current) {
        html += `<li class="breadcrumb-item current" aria-current="page">${crumb.label}</li>`;
      } else {
        html += `<li class="breadcrumb-item"><a href="${crumb.path}">${crumb.label}</a></li>`;
      }

      if (!isLast) {
        html += '<li class="breadcrumb-separator" aria-hidden="true">/</li>';
      }
    });

    html += '</ol></nav>';

    if (containerId) {
      const container = document.getElementById(containerId);
      if (container) {
        container.innerHTML = html;
      }
    }

    return html;
  }

  /**
   * Initialize and inject breadcrumbs into page
   * @param {string} containerId - ID of container to inject breadcrumbs (optional)
   */
  function init(containerId = 'breadcrumb-container') {
    // Check if breadcrumb container exists or needs to be created
    let container = document.getElementById(containerId);

    if (!container) {
      // Try to find common breadcrumb locations
      const possibleLocations = [
        document.querySelector('.breadcrumb'),
        document.querySelector('nav .breadcrumb'),
        document.querySelector('main'),
        document.querySelector('article'),
        document.body
      ];

      for (const location of possibleLocations) {
        if (location && location.id) {
          container = location;
          break;
        }
      }

      // If still no container, try to create one
      if (!container) {
        const article = document.querySelector('article');
        if (article) {
          container = document.createElement('div');
          container.id = containerId;
          article.parentNode.insertBefore(container, article);
        } else {
          // Create and prepend to body
          container = document.createElement('nav');
          container.id = containerId;
          container.className = 'breadcrumb-container';
          document.body.insertBefore(container, document.body.firstChild);
        }
      }
    }

    const breadcrumbs = getBreadcrumb();
    const html = render(breadcrumbs, containerId);

    if (container) {
      container.innerHTML = html;
    }

    return breadcrumbs;
  }

  /**
   * Generate JSON-LD BreadcrumbList schema
   * @param {Array} breadcrumbs - Array of breadcrumb items
   * @returns {Object} JSON-LD schema
   */
  function generateSchema(breadcrumbs) {
    if (!breadcrumbs || breadcrumbs.length === 0) {
      return null;
    }

    const itemListElement = breadcrumbs
      .filter(crumb => !crumb.current)
      .map((crumb, index) => ({
        '@type': 'ListItem',
        'position': index + 1,
        'name': crumb.label,
        'item': new URL(crumb.path, window.location.origin).href
      }));

    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      'itemListElement': itemListElement
    };
  }

  /**
   * Inject BreadcrumbList schema into page
   */
  function injectSchema() {
    const breadcrumbs = getBreadcrumb();
    const schema = generateSchema(breadcrumbs);

    if (schema) {
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.textContent = JSON.stringify(schema);

      // Inject before first JSON-LD if exists, otherwise in head
      const existingJsonLd = document.querySelector('script[type="application/ld+json"]');
      if (existingJsonLd) {
        existingJsonLd.parentNode.insertBefore(script, existingJsonLd.nextSibling);
      } else {
        document.head.appendChild(script);
      }
    }
  }

  // Public API
  return {
    getBreadcrumb,
    render,
    init,
    generateSchema,
    injectSchema,
    extractPageTitle
  };
})();

// Auto-initialize on page load if breadcrumb container exists
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('breadcrumb-container');
    if (container) {
      BreadcrumbGenerator.init();
    }
  });
} else {
  const container = document.getElementById('breadcrumb-container');
  if (container) {
    BreadcrumbGenerator.init();
  }
}
