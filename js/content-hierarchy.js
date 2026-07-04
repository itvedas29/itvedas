/**
 * Content Hierarchy & Sitemap Generator
 * Builds intelligent content structure and generates dynamic sitemaps
 */

const ContentHierarchy = (() => {
  let hierarchy = null;
  let searchIndex = [];

  /**
   * Build content hierarchy from search index
   */
  async function buildHierarchy() {
    if (hierarchy) return hierarchy;

    await loadSearchIndex();

    hierarchy = {
      root: {
        name: 'IT Vedas',
        path: '/',
        children: {}
      },
      byTopic: {},
      byFile: {}
    };

    // Organize by topic
    searchIndex.forEach(item => {
      const topic = item.topic || 'Other';

      if (!hierarchy.byTopic[topic]) {
        hierarchy.byTopic[topic] = {
          name: topic,
          path: `/topics/${topic.toLowerCase()}`,
          items: [],
          count: 0
        };
      }

      hierarchy.byTopic[topic].items.push(item);
      hierarchy.byTopic[topic].count++;

      hierarchy.byFile[item.file] = item;
    });

    // Sort topics by item count
    const sortedTopics = Object.entries(hierarchy.byTopic)
      .sort((a, b) => b[1].count - a[1].count);

    hierarchy.topicsByPopularity = sortedTopics.map(([key, val]) => ({
      name: key,
      count: val.count
    }));

    return hierarchy;
  }

  /**
   * Load search index
   */
  async function loadSearchIndex() {
    if (searchIndex.length > 0) return;

    try {
      const response = await fetch('/search-index.json');
      if (response.ok) {
        searchIndex = await response.json();
      }
    } catch (error) {
      console.warn('ContentHierarchy: Could not load search index', error);
    }
  }

  /**
   * Get content by topic
   */
  async function getContentByTopic(topic) {
    if (!hierarchy) await buildHierarchy();

    return hierarchy.byTopic[topic] || null;
  }

  /**
   * Get all topics
   */
  async function getTopics() {
    if (!hierarchy) await buildHierarchy();

    return Object.keys(hierarchy.byTopic).sort();
  }

  /**
   * Get topic statistics
   */
  async function getTopicStats() {
    if (!hierarchy) await buildHierarchy();

    return {
      totalTopics: Object.keys(hierarchy.byTopic).length,
      totalItems: searchIndex.length,
      topicsById: hierarchy.byTopic,
      topicsByPopularity: hierarchy.topicsByPopularity
    };
  }

  /**
   * Generate XML sitemap
   */
  async function generateXMLSitemap() {
    if (!hierarchy) await buildHierarchy();

    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

    // Add main pages
    const mainPages = ['/', '/chapters.html', '/about.html', '/cve-listing.html'];
    mainPages.forEach(url => {
      xml += `  <url>\n`;
      xml += `    <loc>https://itvedas.com${url}</loc>\n`;
      xml += `    <changefreq>weekly</changefreq>\n`;
      xml += `    <priority>0.8</priority>\n`;
      xml += `  </url>\n`;
    });

    // Add content pages
    searchIndex.forEach(item => {
      if (item.file && !item.file.startsWith('venv')) {
        const url = `https://itvedas.com/${item.file}`;
        xml += `  <url>\n`;
        xml += `    <loc>${url}</loc>\n`;
        xml += `    <changefreq>monthly</changefreq>\n`;
        xml += `    <priority>0.6</priority>\n`;
        xml += `  </url>\n`;
      }
    });

    xml += '</urlset>';
    return xml;
  }

  /**
   * Generate JSON sitemap
   */
  async function generateJSONSitemap() {
    if (!hierarchy) await buildHierarchy();

    const sitemap = {
      siteUrl: 'https://itvedas.com',
      generatedAt: new Date().toISOString(),
      structure: {
        home: '/',
        chapters: '/chapters.html',
        about: '/about.html',
        cveDatabase: '/cve-listing.html',
        topics: hierarchy.byTopic
      },
      stats: {
        totalPages: searchIndex.length,
        totalTopics: Object.keys(hierarchy.byTopic).length,
        categorization: 'By topic'
      }
    };

    return sitemap;
  }

  /**
   * Get breadcrumb path for content
   */
  async function getBreadcrumbPath(filePath) {
    if (!hierarchy) await buildHierarchy();

    const item = hierarchy.byFile[filePath];
    if (!item) return [];

    const breadcrumbs = [
      { label: 'Home', path: '/' }
    ];

    if (item.topic) {
      breadcrumbs.push({
        label: item.topic,
        path: `/topics/${item.topic.toLowerCase()}`
      });
    }

    breadcrumbs.push({
      label: item.title,
      path: `/${filePath}`,
      current: true
    });

    return breadcrumbs;
  }

  /**
   * Get related topics
   */
  async function getRelatedTopics(topic, limit = 5) {
    if (!hierarchy) await buildHierarchy();

    const allTopics = Object.entries(hierarchy.byTopic);
    const currentTopic = hierarchy.byTopic[topic];

    if (!currentTopic) return [];

    // Find topics with keyword overlap
    const related = allTopics
      .filter(([key]) => key !== topic)
      .map(([key, val]) => {
        const similarity = calculateSimilarity(
          currentTopic.items.map(i => i.keyword).join(' '),
          val.items.map(i => i.keyword).join(' ')
        );
        return { name: key, similarity, count: val.count };
      })
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);

    return related;
  }

  /**
   * Calculate similarity between keyword sets
   */
  function calculateSimilarity(str1, str2) {
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
   * Get content tree for navigation
   */
  async function getContentTree(maxDepth = 2) {
    if (!hierarchy) await buildHierarchy();

    const tree = {
      name: 'Content',
      children: []
    };

    Object.entries(hierarchy.byTopic).forEach(([topic, data]) => {
      tree.children.push({
        name: topic,
        count: data.count,
        items: data.items.slice(0, maxDepth).map(item => ({
          name: item.title,
          path: `/${item.file}`
        }))
      });
    });

    tree.children.sort((a, b) => b.count - a.count);

    return tree;
  }

  /**
   * Log hierarchy stats
   */
  async function logStats() {
    const stats = await getTopicStats();

    console.log('\n📊 Content Hierarchy Statistics');
    console.log('='.repeat(60));
    console.log(`Total topics: ${stats.totalTopics}`);
    console.log(`Total items: ${stats.totalItems}`);
    console.log(`Average items per topic: ${(stats.totalItems / stats.totalTopics).toFixed(1)}`);
    console.log('\nTop Topics:');
    stats.topicsByPopularity.slice(0, 10).forEach((topic, i) => {
      console.log(`  ${i + 1}. ${topic.name}: ${topic.count} items`);
    });
    console.log('='.repeat(60) + '\n');
  }

  // Public API
  return {
    buildHierarchy,
    getContentByTopic,
    getTopics,
    getTopicStats,
    generateXMLSitemap,
    generateJSONSitemap,
    getBreadcrumbPath,
    getRelatedTopics,
    getContentTree,
    logStats
  };
})();

// Auto-initialize hierarchy on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ContentHierarchy.buildHierarchy().catch(e => console.warn('ContentHierarchy init failed', e));
  });
} else {
  ContentHierarchy.buildHierarchy().catch(e => console.warn('ContentHierarchy init failed', e));
}
