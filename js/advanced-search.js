/**
 * Advanced Search with Filters & Facets
 * Full-text search with topic, date, and keyword filtering
 */

const AdvancedSearch = (() => {
  let searchIndex = [];
  let searchCache = new Map();
  const CACHE_DURATION = 3600000; // 1 hour

  /**
   * Load search index
   */
  async function loadSearchIndex() {
    if (searchIndex.length > 0) return searchIndex;

    try {
      const response = await fetch('/search-index.json');
      if (response.ok) {
        searchIndex = await response.json();
      }
    } catch (error) {
      console.warn('AdvancedSearch: Could not load search index', error);
    }

    return searchIndex;
  }

  /**
   * Perform advanced search with filters
   */
  async function search(query, options = {}) {
    await loadSearchIndex();

    const {
      topic = null,
      minScore = 0.3,
      limit = 20,
      offset = 0,
      sortBy = 'relevance' // relevance, date, title
    } = options;

    // Create cache key
    const cacheKey = JSON.stringify({ query, topic, limit, offset, sortBy });
    const cached = searchCache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.result;
    }

    // Tokenize query
    const queryTokens = tokenize(query);

    // Search and score
    const results = searchIndex
      .map(item => {
        let score = 0;

        // Topic filter
        if (topic && item.topic !== topic) {
          return null;
        }

        // Title match (highest weight)
        const titleScore = calculateScoreForString(item.title, queryTokens);
        score += titleScore * 0.5;

        // Keywords match
        const keywordScore = calculateScoreForString(item.keyword, queryTokens);
        score += keywordScore * 0.3;

        // Description match
        const descScore = calculateScoreForString(item.description, queryTokens);
        score += descScore * 0.2;

        return score > minScore ? { ...item, score } : null;
      })
      .filter(item => item !== null)
      .sort((a, b) => {
        if (sortBy === 'relevance') {
          return b.score - a.score;
        } else if (sortBy === 'title') {
          return a.title.localeCompare(b.title);
        }
        return 0;
      });

    // Paginate
    const paginated = results.slice(offset, offset + limit);

    const result = {
      query,
      totalResults: results.length,
      results: paginated,
      hasMore: results.length > offset + limit,
      offset,
      limit
    };

    // Cache result
    searchCache.set(cacheKey, { result, timestamp: Date.now() });

    return result;
  }

  /**
   * Tokenize search query
   */
  function tokenize(query) {
    return query
      .toLowerCase()
      .split(/[\s,;]+/)
      .filter(token => token.length > 2);
  }

  /**
   * Calculate search score for string
   */
  function calculateScoreForString(text, tokens) {
    if (!text) return 0;

    const textLower = text.toLowerCase();
    let matches = 0;

    tokens.forEach(token => {
      if (textLower.includes(token)) {
        matches++;
      }
    });

    return matches / Math.max(tokens.length, 1);
  }

  /**
   * Get available filters (topics, etc.)
   */
  async function getFilters() {
    await loadSearchIndex();

    const topics = {};
    const keywords = new Set();

    searchIndex.forEach(item => {
      // Count topics
      topics[item.topic] = (topics[item.topic] || 0) + 1;

      // Collect keywords
      if (item.keyword) {
        item.keyword.split(',').forEach(kw => {
          keywords.add(kw.trim());
        });
      }
    });

    return {
      topics: Object.entries(topics)
        .sort((a, b) => b[1] - a[1])
        .map(([name, count]) => ({ name, count })),
      keywordCount: keywords.size
    };
  }

  /**
   * Get search suggestions (autocomplete)
   */
  async function getSuggestions(partial, limit = 10) {
    await loadSearchIndex();

    const partialLower = partial.toLowerCase();
    const suggestions = new Set();

    searchIndex.forEach(item => {
      // Title suggestions
      if (item.title.toLowerCase().includes(partialLower)) {
        suggestions.add(item.title);
      }

      // Keyword suggestions
      if (item.keyword) {
        item.keyword.split(',').forEach(kw => {
          const trimmed = kw.trim();
          if (trimmed.toLowerCase().includes(partialLower)) {
            suggestions.add(trimmed);
          }
        });
      }
    });

    return Array.from(suggestions)
      .sort()
      .slice(0, limit);
  }

  /**
   * Perform faceted search
   */
  async function searchWithFacets(query, options = {}) {
    const { topic = null, limit = 20, offset = 0 } = options;

    const searchResult = await search(query, {
      topic,
      limit,
      offset
    });

    const facets = {
      topicDistribution: {},
      keywordDistribution: {}
    };

    // Build facet distributions from results
    searchResult.results.forEach(item => {
      facets.topicDistribution[item.topic] =
        (facets.topicDistribution[item.topic] || 0) + 1;

      if (item.keyword) {
        item.keyword.split(',').forEach(kw => {
          const trimmed = kw.trim();
          facets.keywordDistribution[trimmed] =
            (facets.keywordDistribution[trimmed] || 0) + 1;
        });
      }
    });

    return {
      ...searchResult,
      facets
    };
  }

  /**
   * Clear cache
   */
  function clearCache() {
    searchCache.clear();
  }

  /**
   * Get search statistics
   */
  async function getStats() {
    await loadSearchIndex();

    return {
      indexSize: searchIndex.length,
      cacheSize: searchCache.size,
      topics: new Set(searchIndex.map(i => i.topic)).size,
      keywords: new Set(
        searchIndex
          .flatMap(i => i.keyword?.split(',') || [])
          .map(k => k.trim())
      ).size
    };
  }

  // Public API
  return {
    search,
    getFilters,
    getSuggestions,
    searchWithFacets,
    clearCache,
    getStats,
    loadSearchIndex
  };
})();
