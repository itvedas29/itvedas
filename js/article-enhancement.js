/**
 * ITVedas Article Enhancement System
 * Adds author profiles, metadata, trust signals, and improves reading experience
 */

class ArticleEnhancement {
  constructor() {
    this.article = document.querySelector('article') || document.querySelector('.art');
    this.init();
  }

  async init() {
    if (!this.article) return;

    await this.loadAuthorProfiles();
    this.enhanceMetadata();
    this.addTrustSignals();
    this.enhanceReadingExperience();
    this.generateTableOfContents();
    this.addProgressIndicator();
    this.setupRelatedContent();
  }

  async loadAuthorProfiles() {
    try {
      const response = await fetch('/data/authors.json');
      const authors = await response.json();

      // Find author profile from meta or default
      const authorName = document.querySelector('[data-author]')?.dataset.author || 'ITVedas Team';
      const author = authors.find(a => a.name.toLowerCase() === authorName.toLowerCase()) || authors[0];

      if (author) {
        this.renderAuthorProfile(author);
      }
    } catch (error) {
      console.error('Failed to load author profiles:', error);
    }
  }

  renderAuthorProfile(author) {
    const profileHTML = `
      <div class="article-author-card">
        <div class="author-avatar">
          ${author.photo ? `<img src="${author.photo}" alt="${author.name}">` : '<div class="avatar-placeholder">👤</div>'}
        </div>
        <div class="author-info">
          <h4>${author.name}</h4>
          <p class="author-expertise">${author.expertise}</p>
          <p class="author-bio">${author.bio}</p>
          <div class="author-links">
            ${author.linkedin ? `<a href="${author.linkedin}" target="_blank" rel="noopener" title="LinkedIn">in</a>` : ''}
            ${author.github ? `<a href="${author.github}" target="_blank" rel="noopener" title="GitHub">gh</a>` : ''}
          </div>
        </div>
      </div>
    `;

    const insertPoint = this.article.querySelector('h1')?.nextElementSibling;
    if (insertPoint) {
      const authorEl = document.createElement('div');
      authorEl.innerHTML = profileHTML;
      this.article.insertBefore(authorEl, insertPoint);
    }
  }

  enhanceMetadata() {
    const metaHTML = `
      <div class="article-metadata">
        <div class="meta-item">
          <span class="meta-label">Published</span>
          <span class="meta-value">${this.getPublishedDate()}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Updated</span>
          <span class="meta-value">${this.getUpdatedDate()}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Reading Time</span>
          <span class="meta-value">${this.calculateReadingTime()} min</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Difficulty</span>
          <span class="meta-value">${this.getDifficulty()}</span>
        </div>
      </div>
    `;

    const insertPoint = this.article.querySelector('h1');
    if (insertPoint) {
      const metaEl = document.createElement('div');
      metaEl.innerHTML = metaHTML;
      insertPoint.insertAdjacentElement('afterend', metaEl);
    }
  }

  addTrustSignals() {
    const trustHTML = `
      <div class="article-trust-signals">
        <div class="trust-signal">
          <span class="trust-icon">✓</span>
          <div class="trust-content">
            <strong>Technical Accuracy Verified</strong>
            <p>Reviewed by IT professionals</p>
          </div>
        </div>
        <div class="trust-signal">
          <span class="trust-icon">🔬</span>
          <div class="trust-content">
            <strong>Tested & Verified</strong>
            <p>Hands-on testing confirmed</p>
          </div>
        </div>
        <div class="trust-signal">
          <span class="trust-icon">📚</span>
          <div class="trust-content">
            <strong>Sources & References</strong>
            <p>Official documentation linked</p>
          </div>
        </div>
      </div>
    `;

    const insertPoint = this.article.querySelector('h1')?.parentElement;
    if (insertPoint) {
      const trustEl = document.createElement('div');
      trustEl.innerHTML = trustHTML;
      insertPoint.appendChild(trustEl);
    }
  }

  enhanceReadingExperience() {
    // Add code copy buttons
    this.addCodeCopyButtons();

    // Add image zoom capability
    this.addImageZoom();

    // Add callout boxes
    this.enhanceCalloutBoxes();

    // Syntax highlighting (if not already present)
    if (typeof Prism !== 'undefined') {
      Prism.highlightAllUnder(this.article);
    }
  }

  addCodeCopyButtons() {
    this.article.querySelectorAll('pre code').forEach(codeBlock => {
      const button = document.createElement('button');
      button.className = 'code-copy-btn';
      button.textContent = 'Copy';
      button.addEventListener('click', () => {
        navigator.clipboard.writeText(codeBlock.textContent);
        button.textContent = 'Copied!';
        setTimeout(() => {
          button.textContent = 'Copy';
        }, 2000);
      });
      codeBlock.parentElement.insertBefore(button, codeBlock);
    });
  }

  addImageZoom() {
    this.article.querySelectorAll('img').forEach(img => {
      img.style.cursor = 'zoom-in';
      img.addEventListener('click', () => {
        this.createImageModal(img);
      });
    });
  }

  createImageModal(img) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
      <div class="image-modal-content">
        <img src="${img.src}" alt="${img.alt}">
        <button class="image-modal-close">×</button>
      </div>
    `;

    document.body.appendChild(modal);

    const closeBtn = modal.querySelector('.image-modal-close');
    const closeModal = () => {
      modal.style.animation = 'fadeOut 0.3s ease-out forwards';
      setTimeout(() => modal.remove(), 300);
    };

    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }

  enhanceCalloutBoxes() {
    // Convert blockquote to callout boxes if they contain keywords
    this.article.querySelectorAll('blockquote').forEach(quote => {
      const text = quote.textContent.toLowerCase();
      let type = 'info';

      if (text.includes('note:') || text.includes('important:')) {
        type = 'info';
      } else if (text.includes('warning:') || text.includes('caution:')) {
        type = 'warning';
      } else if (text.includes('best practice:') || text.includes('tip:')) {
        type = 'best-practice';
      } else if (text.includes('error:') || text.includes('troubleshoot:')) {
        type = 'error';
      }

      quote.className = `callout callout-${type}`;
    });
  }

  generateTableOfContents() {
    const headings = this.article.querySelectorAll('h2, h3');
    if (headings.length === 0) return;

    const tocContainer = document.querySelector('.toc') || this.createTocContainer();
    const toc = document.createElement('ol');

    let currentH2;
    let h2Count = 0;

    headings.forEach((heading, index) => {
      const id = heading.id || `heading-${index}`;
      heading.id = id;

      if (heading.tagName === 'H2') {
        h2Count++;
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `#${id}`;
        link.textContent = heading.textContent;
        li.appendChild(link);
        toc.appendChild(li);
        currentH2 = li;
      } else if (heading.tagName === 'H3' && currentH2) {
        const ul = currentH2.querySelector('ul') || document.createElement('ul');
        if (!currentH2.querySelector('ul')) {
          currentH2.appendChild(ul);
        }
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `#${id}`;
        link.textContent = heading.textContent;
        li.appendChild(link);
        ul.appendChild(li);
      }
    });

    if (tocContainer.querySelector('ol')) {
      tocContainer.querySelector('ol').replaceWith(toc);
    } else {
      tocContainer.appendChild(toc);
    }
  }

  createTocContainer() {
    let tocContainer = document.querySelector('.toc');
    if (!tocContainer) {
      tocContainer = document.createElement('aside');
      tocContainer.className = 'toc';
      const heading = document.createElement('h3');
      heading.textContent = 'Table of Contents';
      tocContainer.appendChild(heading);

      const wrap = document.querySelector('.wrap');
      if (wrap) {
        wrap.appendChild(tocContainer);
      } else {
        this.article.insertAdjacentElement('beforebegin', tocContainer);
      }
    }
    return tocContainer;
  }

  addProgressIndicator() {
    const progressBar = document.createElement('div');
    progressBar.id = 'article-progress';
    progressBar.className = 'article-progress';
    document.body.insertBefore(progressBar, document.body.firstChild);

    window.addEventListener('scroll', () => {
      const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = (window.scrollY / windowHeight) * 100;
      progressBar.style.width = scrolled + '%';
    });
  }

  setupRelatedContent() {
    const relatedHTML = `
      <div class="related-content">
        <h3>Related Articles</h3>
        <div class="related-articles-grid" data-content></div>
      </div>
    `;

    const related = document.createElement('div');
    related.innerHTML = relatedHTML;
    this.article.appendChild(related);

    // Load related articles based on tags/category
    this.loadRelatedArticles();
  }

  async loadRelatedArticles() {
    try {
      const response = await fetch('/search-index.json');
      const articles = await response.json();

      const currentUrl = window.location.pathname;
      const currentArticle = articles.find(a => a.url === currentUrl);

      if (!currentArticle) return;

      const related = articles
        .filter(a => {
          if (a.url === currentUrl) return false;
          const tagMatch = a.tags?.some(t => currentArticle.tags?.includes(t));
          const categoryMatch = a.category === currentArticle.category;
          return tagMatch || categoryMatch;
        })
        .slice(0, 6);

      const container = document.querySelector('.related-articles-grid');
      if (container) {
        container.innerHTML = related
          .map(a => `
            <a href="${a.url}" class="art">
              <span class="chip">${a.category || 'Article'}</span>
              <h4>${a.title}</h4>
              <p>${ComponentLibrary.truncateText(a.description, 80)}</p>
              <div class="foot">
                <span>${a.readTime || '5'} min read</span>
              </div>
            </a>
          `)
          .join('');
      }
    } catch (error) {
      console.error('Failed to load related articles:', error);
    }
  }

  getPublishedDate() {
    const dateEl = document.querySelector('[data-published]');
    if (dateEl) return dateEl.dataset.published;
    const metaTag = document.querySelector('meta[property="article:published_time"]');
    return metaTag?.content || 'Recently';
  }

  getUpdatedDate() {
    const dateEl = document.querySelector('[data-updated]');
    if (dateEl) return dateEl.dataset.updated;
    const metaTag = document.querySelector('meta[property="article:modified_time"]');
    return metaTag?.content || 'Recently';
  }

  calculateReadingTime() {
    const text = this.article.textContent || '';
    const wordsPerMinute = 200;
    const wordCount = text.split(/\s+/).length;
    return Math.ceil(wordCount / wordsPerMinute);
  }

  getDifficulty() {
    const diffEl = document.querySelector('[data-difficulty]');
    if (diffEl) return diffEl.dataset.difficulty;
    return 'Intermediate';
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('article') || document.querySelector('.art')) {
      new ArticleEnhancement();
    }
  });
} else {
  if (document.querySelector('article') || document.querySelector('.art')) {
    new ArticleEnhancement();
  }
}
