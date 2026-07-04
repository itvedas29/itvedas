/**
 * Related Content Recommendation System
 * Suggests related articles and pages based on keywords, topic, and content similarity
 */

const RelatedContent = (() => {
  let searchIndex = [];
  let isLoading = false;

  /**
   * Load search index from JSON file
   */
  async function loadSearchIndex() {
    if (isLoading) return;
    if (searchIndex.length > 0) return;

    isLoading = true;
    try {
      const response = await fetch('/search-index.json');
      if (!response.ok) throw new Error('Failed to load search index');
      searchIndex = await response.json();
    } catch (error) {
      console.warn('RelatedContent: Could not load search index', error);
      isLoading = false;
    }
    isLoading = false;
  }

  /**
   * Extract metadata from current page
   */
  function extractPageMetadata() {
    const metadata = {
      title: document.querySelector('meta[property="og:title"]')?.content ||
              document.querySelector('title')?.textContent || '',
      description: document.querySelector('meta[name="description"]')?.content ||
                  document.querySelector('meta[property="og:description"]')?.content || '',
      keywords: document.querySelector('meta[name="keywords"]')?.content || '',
      url: window.location.pathname,
    };

    // Extract topic from JSON-LD if available
    const jsonLdScript = document.querySelector('script[type="application/ld+json"]');
    if (jsonLdScript) {
      try {
        const data = JSON.parse(jsonLdScript.textContent);
        if (data.articleSection) {
          metadata.topic = data.articleSection;
        }
      } catch (e) {
        // Ignore parse errors
      }
    }

    return metadata;
  }

  /**
   * Calculate similarity score between two strings (simple keyword overlap)
   */
  function calculateSimilarity(str1, str2) {
    if (!str1 || !str2) return 0;

    const normalize = (s) => s.toLowerCase().split(/[\s,;]+/).filter(w => w.length > 3);
    const words1 = new Set(normalize(str1));
    const words2 = new Set(normalize(str2));

    let overlap = 0;
    words1.forEach(word => {
      if (words2.has(word)) overlap++;
    });

    return overlap / Math.max(words1.size, words2.size);
  }

  /**
   * Find related content based on various criteria
   * @param {number} limit - Maximum number of results
   * @param {object} options - Recommendation options
   */
  async function findRelated(limit = 5, options = {}) {
    await loadSearchIndex();

    if (searchIndex.length === 0) {
      console.warn('RelatedContent: Search index is empty');
      return [];
    }

    const pageMetadata = extractPageMetadata();
    const {
      byTopic = true,
      byKeywords = true,
      byTitle = true,
      excludeSelf = true
    } = options;

    const scored = searchIndex
      .filter(item => {
        // Exclude current page
        if (excludeSelf && item.file && pageMetadata.url.includes(item.file)) {
          return false;
        }
        // Exclude certain file types
        if (!item.title || !item.file) return false;
        return true;
      })
      .map(item => {
        let score = 0;
        let reasons = [];

        // Topic match (highest weight)
        if (byTopic && pageMetadata.topic && item.topic) {
          if (pageMetadata.topic.toLowerCase() === item.topic.toLowerCase()) {
            score += 40;
            reasons.push('topic');
          } else if (pageMetadata.topic.toLowerCase().includes(item.topic.toLowerCase())) {
            score += 20;
            reasons.push('topic');
          }
        }

        // Keyword overlap (medium weight)
        if (byKeywords && pageMetadata.keywords && item.keyword) {
          const keywordSimilarity = calculateSimilarity(pageMetadata.keywords, item.keyword);
          score += keywordSimilarity * 30;
          if (keywordSimilarity > 0.2) {
            reasons.push('keywords');
          }
        }

        // Title similarity (lower weight)
        if (byTitle && pageMetadata.title && item.title) {
          const titleSimilarity = calculateSimilarity(pageMetadata.title, item.title);
          score += titleSimilarity * 10;
          if (titleSimilarity > 0.3) {
            reasons.push('title');
          }
        }

        return {
          ...item,
          score,
          reasons
        };
      })
      .sort((a, b) => b.score - a.score)
      .filter(item => item.score > 0)
      .slice(0, limit);

    return scored;
  }

  /**
   * Generate HTML for related content
   */
  function renderRelated(items, options = {}) {
    if (!items || items.length === 0) {
      return '';
    }

    const {
      title = 'Related Articles',
      columns = 1,
      showReason = false,
      showExcerpt = true
    } = options;

    let html = `<section class="related-content">`;
    html += `<h3 class="related-title">${title}</h3>`;
    html += `<div class="related-grid" style="--cols: ${columns}">`;

    items.forEach(item => {
      html += `<article class="related-item">`;
      html += `<a href="/${item.file}" class="related-link">`;
      html += `<h4 class="related-item-title">${item.title}</h4>`;

      if (showExcerpt && item.description) {
        html += `<p class="related-item-excerpt">${item.description.substring(0, 120)}...</p>`;
      }

      if (showReason && item.reasons && item.reasons.length > 0) {
        html += `<div class="related-item-meta">`;
        html += `<span class="related-topic">${item.topic}</span>`;
        html += `</div>`;
      }

      html += `</a>`;
      html += `</article>`;
    });

    html += `</div>`;
    html += `</section>`;

    return html;
  }

  /**
   * Initialize and inject related content
   */
  async function init(options = {}) {
    const {
      containerId = 'related-content',
      limit = 5,
      title = 'Related Articles',
      columns = 3
    } = options;

    const container = document.getElementById(containerId);
    if (!container) {
      console.warn(`RelatedContent: Container with id "${containerId}" not found`);
      return [];
    }

    const related = await findRelated(limit, options);
    const html = renderRelated(related, {
      title,
      columns,
      showReason: false,
      showExcerpt: true
    });

    container.innerHTML = html;
    return related;
  }

  /**
   * Generate JSON-LD BreadcrumbList for related articles
   */
  function generateSchema(items) {
    if (!items || items.length === 0) {
      return null;
    }

    const relatedLinks = items.map(item => ({
      '@context': 'https://schema.org',
      '@type': 'Thing',
      'url': `${window.location.origin}/${item.file}`,
      'name': item.title
    }));

    return {
      '@context': 'https://schema.org',
      '@type': 'Article',
      'relatedLink': relatedLinks
    };
  }

  // Public API
  return {
    loadSearchIndex,
    extractPageMetadata,
    findRelated,
    renderRelated,
    init,
    generateSchema
  };
})();

// Auto-initialize on page load if related content container exists
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('related-content');
    if (container) {
      RelatedContent.init({
        containerId: 'related-content',
        limit: 5,
        title: 'Related Articles',
        columns: 3
      }).catch(e => console.warn('RelatedContent init failed', e));
    }
  });
} else {
  const container = document.getElementById('related-content');
  if (container) {
    RelatedContent.init({
      containerId: 'related-content',
      limit: 5,
      title: 'Related Articles',
      columns: 3
    }).catch(e => console.warn('RelatedContent init failed', e));
  }
}
