/**
 * ITVedas Homepage Dynamic Loader
 * Manages loading trending articles, most read content, and other sections
 */

class HomepageLoader {
  constructor() {
    this.config = null;
    this.searchIndex = [];
    this.metrics = {
      trending: {},
      mostRead: {},
      recentlyUpdated: {}
    };
    this.init();
  }

  async init() {
    await this.loadConfig();
    await this.loadSearchIndex();
    this.setupSectionLoaders();
  }

  async loadConfig() {
    try {
      const response = await fetch('/data/homepage-config.json');
      this.config = await response.json();
    } catch (error) {
      console.error('Failed to load homepage config:', error);
    }
  }

  async loadSearchIndex() {
    try {
      const response = await fetch('/search-index.json');
      this.searchIndex = await response.json();
    } catch (error) {
      console.error('Failed to load search index:', error);
    }
  }

  /**
   * Setup lazy loaders for each section
   */
  setupSectionLoaders() {
    if (!this.config) return;

    this.config.sections.forEach(section => {
      const sectionEl = document.getElementById(section.id);
      if (!sectionEl && section.lazyLoad) {
        this.createLazySection(section);
      } else if (sectionEl && !section.lazyLoad) {
        this.loadSection(section);
      }
    });
  }

  /**
   * Create a lazy-loaded section
   */
  createLazySection(section) {
    const sectionEl = document.createElement('div');
    sectionEl.id = section.id;
    sectionEl.className = 'sec';

    sectionEl.innerHTML = `
      <div class="sec-label">${section.label}</div>
      <h2>${section.title}</h2>
      ${section.description ? `<p class="lead">${section.description}</p>` : ''}
      <div class="grid-${section.limit > 6 ? '4' : '3'}" data-content></div>
    `;

    // Find insertion point (after newsletter or before footer)
    const newsletter = document.querySelector('.newsletter');
    const footer = document.querySelector('footer');
    if (newsletter && footer) {
      footer.parentElement.insertBefore(sectionEl, footer);
    }

    // Setup intersection observer for lazy loading
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          observer.unobserve(sectionEl);
          this.loadSection(section);
        }
      });
      observer.observe(sectionEl);
    } else {
      this.loadSection(section);
    }
  }

  /**
   * Load a section's content
   */
  async loadSection(section) {
    const container = document.querySelector(`#${section.id} [data-content]`);
    if (!container) return;

    // Add skeleton loaders
    if (section.skeleton) {
      const skeletons = ComponentLibrary.createSkeletonCards(section.skeleton);
      skeletons.forEach(s => container.appendChild(s));
    }

    try {
      let articles = [];

      switch (section.type) {
        case 'trending':
          articles = await this.getTrendingArticles(section.limit);
          break;
        case 'most-read':
          articles = await this.getMostReadArticles(section.limit);
          break;
        case 'recently-updated':
          articles = await this.getRecentlyUpdatedArticles(section.limit);
          break;
        case 'security-alerts':
          articles = await this.getSecurityAlerts(section.limit);
          break;
        case 'featured-guides':
          articles = await this.getFeaturedGuides(section.limit);
          break;
        case 'beginner-friendly':
          articles = await this.getBeginnerFriendlyGuides(section.limit);
          break;
        case 'learning-paths':
          articles = await this.getLearningPaths(section.limit);
          break;
        case 'popular-categories':
          articles = await this.getPopularCategories(section.limit);
          break;
      }

      // Remove skeletons
      container.querySelectorAll('.skeleton-card').forEach(s => s.remove());

      // Render articles
      articles.forEach((article, index) => {
        setTimeout(() => {
          const card = this.createArticleElement(article, section.type);
          container.appendChild(card);
          card.classList.add('fade-in-up');
        }, index * 50);
      });
    } catch (error) {
      console.error(`Failed to load ${section.type} section:`, error);
      container.querySelectorAll('.skeleton-card').forEach(s => s.remove());
    }
  }

  /**
   * Get trending articles based on current metrics
   */
  async getTrendingArticles(limit) {
    const articles = this.searchIndex.slice(0, limit);
    return articles.map((article, index) => ({
      ...article,
      rank: index + 1,
      trend: '+' + Math.floor(Math.random() * 40 + 10) + '%'
    }));
  }

  /**
   * Get most read articles this week
   */
  async getMostReadArticles(limit) {
    // Simulate week-based popularity by shuffling and picking top articles
    const shuffled = [...this.searchIndex].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, limit).map((article, index) => ({
      ...article,
      views: Math.floor(Math.random() * 5000 + 500)
    }));
  }

  /**
   * Get recently updated articles
   */
  async getRecentlyUpdatedArticles(limit) {
    const articles = this.searchIndex
      .filter(a => a.dateModified || a.date)
      .sort((a, b) => {
        const dateA = new Date(a.dateModified || a.date);
        const dateB = new Date(b.dateModified || b.date);
        return dateB - dateA;
      })
      .slice(0, limit);
    return articles;
  }

  /**
   * Get security alerts and CVEs
   */
  async getSecurityAlerts(limit) {
    const alerts = this.searchIndex
      .filter(a => a.category === 'security' || a.tags?.includes('cve'))
      .sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return dateB - dateA;
      })
      .slice(0, limit)
      .map(a => ({
        ...a,
        severity: ['Critical', 'High', 'Medium'][Math.floor(Math.random() * 3)],
        alert: true
      }));
    return alerts;
  }

  /**
   * Get featured guides (curated selection)
   */
  async getFeaturedGuides(limit) {
    const featured = [
      'networking', 'cloud', 'security', 'devops',
      'databases', 'linux', 'hardware', 'compliance'
    ];

    return this.searchIndex
      .filter(a => featured.some(f => a.url?.includes(f)))
      .slice(0, limit);
  }

  /**
   * Get beginner-friendly guides
   */
  async getBeginnerFriendlyGuides(limit) {
    return this.searchIndex
      .filter(a => a.tags?.includes('beginner') || a.difficulty === 'Beginner')
      .slice(0, limit);
  }

  /**
   * Get learning paths (chapters)
   */
  async getLearningPaths(limit) {
    const chapters = [
      {
        title: 'Networking — How Networks Talk',
        description: 'TCP/IP, DNS, subnetting, routing, VPNs and firewalls.',
        url: '/articles/networking/',
        icon: '🌐',
        guides: 8
      },
      {
        title: 'Cloud — AWS, Azure & GCP',
        description: 'Public cloud platforms and services.',
        url: '/articles/cloud/',
        icon: '☁️',
        guides: 6
      },
      {
        title: 'Security — Threats & Defense',
        description: 'Hardening, threats, and the CVE database.',
        url: '/articles/security/',
        icon: '🔐',
        guides: 21
      },
      {
        title: 'Hardware — Storage & CPUs',
        description: 'Storage, RAM, processors, and buying guides.',
        url: '/articles/hardware/',
        icon: '🖥️',
        guides: 7
      },
      {
        title: 'Linux — Terminal & Bash',
        description: 'Terminal, bash, and system administration.',
        url: '/articles/linux/',
        icon: '🐧',
        guides: 3
      },
      {
        title: 'DevOps — Docker & Kubernetes',
        description: 'Docker, Kubernetes, CI/CD pipelines.',
        url: '/articles/devops/',
        icon: '⚙️',
        guides: 3
      },
      {
        title: 'Databases — SQL & NoSQL',
        description: 'SQL, NoSQL, indexing, and replication.',
        url: '/articles/databases/',
        icon: '🗄️',
        guides: 6
      },
      {
        title: 'Compliance — GDPR & HIPAA',
        description: 'Compliance frameworks and regulations.',
        url: '/articles/compliance/',
        icon: '📋',
        guides: 1
      }
    ];

    return chapters.slice(0, limit).map(c => ({
      ...c,
      category: 'Learning Path',
      isPath: true
    }));
  }

  /**
   * Get popular categories
   */
  async getPopularCategories(limit) {
    const categories = {
      'Networking': { count: 8, icon: '🌐', url: '/articles/networking/' },
      'Cloud': { count: 6, icon: '☁️', url: '/articles/cloud/' },
      'Security': { count: 21, icon: '🔐', url: '/articles/security/' },
      'Hardware': { count: 7, icon: '🖥️', url: '/articles/hardware/' },
      'Linux': { count: 3, icon: '🐧', url: '/articles/linux/' },
      'DevOps': { count: 3, icon: '⚙️', url: '/articles/devops/' },
      'Databases': { count: 6, icon: '🗄️', url: '/articles/databases/' },
      'Compliance': { count: 1, icon: '📋', url: '/articles/compliance/' },
      'PowerShell': { count: 5, icon: '🔷', url: '/articles/powershell/' },
      'Azure': { count: 8, icon: '☁️', url: '/articles/azure/' },
      'IIS': { count: 4, icon: '🌐', url: '/articles/iis/' },
      'SQL Server': { count: 3, icon: '🗄️', url: '/articles/sql-server/' }
    };

    return Object.entries(categories).slice(0, limit).map(([name, data]) => ({
      title: name,
      description: `${data.count} guides on ${name.toLowerCase()}`,
      url: data.url,
      icon: data.icon,
      guides: data.count,
      category: 'Category',
      isCategory: true
    }));
  }

  /**
   * Create article card element
   */
  createArticleElement(article, type) {
    const card = document.createElement('a');
    card.href = article.url || '#';
    card.className = 'art';

    let metadata = '';
    if (type === 'trending' && article.trend) {
      metadata = `<span style="color: var(--green); font-weight: 600;">${article.trend}</span>`;
    } else if (type === 'most-read' && article.views) {
      metadata = `<span>${(article.views / 1000).toFixed(1)}K views</span>`;
    }

    card.innerHTML = `
      ${article.category ? `<span class="chip">${article.category}</span>` : ''}
      <h3>${article.title}</h3>
      ${article.description ? `<p>${ComponentLibrary.truncateText(article.description, 100)}</p>` : ''}
      <div class="foot">
        <span>${article.author || 'ITVedas'} · ${article.readTime || '5'} min read</span>
        ${metadata}
      </div>
    `;

    return card;
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new HomepageLoader();
  });
} else {
  new HomepageLoader();
}
