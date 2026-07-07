/**
 * ITVEDAS Component Library
 * Reusable UI components and utilities for consistent design system
 */

const ComponentLibrary = {
  /**
   * Create a card element with optional link and configuration
   * @param {Object} config - Card configuration
   * @returns {HTMLElement} Card element
   */
  createCard(config) {
    const {
      title,
      description,
      icon,
      link,
      meta = [],
      className = '',
      iconBg = 'rgba(255, 107, 53, 0.13)'
    } = config;

    const card = document.createElement('a');
    card.href = link || '#';
    card.className = `card ${className}`;
    card.style.setProperty('--icon-bg', iconBg);

    card.innerHTML = `
      ${icon ? `<div class="card-icon">${icon}</div>` : ''}
      <h3>${title}</h3>
      ${description ? `<p>${description}</p>` : ''}
      ${meta.length > 0 ? `<div class="meta">${meta.map(m => `<span>${m}</span>`).join('')}</div>` : ''}
      <div class="go">↗</div>
    `;

    return card;
  },

  /**
   * Create an article card element
   * @param {Object} config - Article configuration
   * @returns {HTMLElement} Article card element
   */
  createArticleCard(config) {
    const {
      title,
      description,
      category,
      link,
      author,
      readTime,
      date
    } = config;

    const art = document.createElement('a');
    art.href = link || '#';
    art.className = 'art';

    art.innerHTML = `
      ${category ? `<span class="chip">${category}</span>` : ''}
      <h3>${title}</h3>
      ${description ? `<p>${description}</p>` : ''}
      <div class="foot">
        <span>${author || 'ITVedas'} · ${readTime || '5 min read'}</span>
        <b>${date || new Date().toLocaleDateString()}</b>
      </div>
    `;

    return art;
  },

  /**
   * Create a skeleton loader card
   * @param {number} count - Number of skeleton cards to create
   * @returns {HTMLElement[]} Array of skeleton card elements
   */
  createSkeletonCards(count = 3) {
    const skeletons = [];
    for (let i = 0; i < count; i++) {
      const skeleton = document.createElement('div');
      skeleton.className = 'skeleton-card skeleton';
      skeleton.innerHTML = `
        <div class="skeleton-icon"></div>
        <div class="skeleton-title"></div>
        <div class="skeleton-text"></div>
        <div class="skeleton-text"></div>
        <div class="skeleton-meta">
          <div></div>
          <div></div>
        </div>
      `;
      skeletons.push(skeleton);
    }
    return skeletons;
  },

  /**
   * Create a badge element
   * @param {Object} config - Badge configuration
   * @returns {HTMLElement} Badge element
   */
  createBadge(config) {
    const {
      text,
      variant = 'primary'
    } = config;

    const badge = document.createElement('span');
    badge.className = `badge badge-${variant}`;
    badge.textContent = text;

    return badge;
  },

  /**
   * Create a button element
   * @param {Object} config - Button configuration
   * @returns {HTMLElement} Button element
   */
  createButton(config) {
    const {
      text,
      onClick,
      href,
      variant = 'primary',
      size = 'md',
      className = ''
    } = config;

    const element = href ? document.createElement('a') : document.createElement('button');
    element.className = `btn btn-${variant} btn-${size} ${className}`;
    element.textContent = text;

    if (href) {
      element.href = href;
    } else if (onClick) {
      element.addEventListener('click', onClick);
    }

    if (!href) {
      element.type = 'button';
    }

    return element;
  },

  /**
   * Create a grid layout
   * @param {Object} config - Grid configuration
   * @returns {HTMLElement} Grid container
   */
  createGrid(config) {
    const {
      cols = 3,
      gap = '1rem',
      items = [],
      className = ''
    } = config;

    const grid = document.createElement('div');
    grid.className = `grid-${cols} ${className}`;
    grid.style.gap = gap;

    items.forEach(item => {
      grid.appendChild(item);
    });

    return grid;
  },

  /**
   * Create a section wrapper
   * @param {Object} config - Section configuration
   * @returns {HTMLElement} Section element
   */
  createSection(config) {
    const {
      label,
      title,
      description,
      className = '',
      children = []
    } = config;

    const section = document.createElement('div');
    section.className = `sec ${className}`;

    let html = '';
    if (label) html += `<div class="sec-label">${label}</div>`;
    if (title) html += `<h2>${title}</h2>`;
    if (description) html += `<p class="lead">${description}</p>`;

    section.innerHTML = html;

    children.forEach(child => {
      section.appendChild(child);
    });

    return section;
  },

  /**
   * Lazy load images with intersection observer
   * @param {string} selector - Image selector
   */
  lazyLoadImages(selector = 'img[data-src]') {
    if (!('IntersectionObserver' in window)) {
      document.querySelectorAll(selector).forEach(img => {
        if (img.dataset.src) {
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
        }
      });
      return;
    }

    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          observer.unobserve(img);
        }
      });
    });

    document.querySelectorAll(selector).forEach(img => imageObserver.observe(img));
  },

  /**
   * Lazy load sections with skeleton loaders
   * @param {string} selector - Section selector
   * @param {Function} loadFn - Function to load content
   * @param {number} skeletonCount - Number of skeleton loaders
   */
  lazyLoadSection(selector, loadFn, skeletonCount = 3) {
    const section = document.querySelector(selector);
    if (!section) return;

    const container = section.querySelector('[data-content]') || section;
    const skeletons = this.createSkeletonCards(skeletonCount);
    skeletons.forEach(skeleton => container.appendChild(skeleton));

    if (!('IntersectionObserver' in window)) {
      loadFn();
      skeletons.forEach(s => s.remove());
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        observer.unobserve(section);
        loadFn().then(() => {
          skeletons.forEach(s => s.remove());
        });
      }
    });

    observer.observe(section);
  },

  /**
   * Add pagination to a list
   * @param {Object} config - Pagination configuration
   * @returns {Object} Pagination control object
   */
  createPagination(config) {
    const {
      items = [],
      itemsPerPage = 12,
      onPageChange = () => {}
    } = config;

    let currentPage = 1;
    const totalPages = Math.ceil(items.length / itemsPerPage);

    const getPage = (page) => {
      const start = (page - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      return items.slice(start, end);
    };

    const createControl = () => {
      const control = document.createElement('div');
      control.className = 'pagination-control';
      control.style.cssText = `
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 2rem;
        flex-wrap: wrap;
      `;

      const createPageBtn = (page, isCurrent = false) => {
        const btn = document.createElement('button');
        btn.textContent = page;
        btn.className = isCurrent ? 'btn btn-sm' : 'btn btn-secondary btn-sm';
        btn.onclick = () => {
          currentPage = page;
          onPageChange(getPage(page), page, totalPages);
          updateControl();
        };
        return btn;
      };

      const updateControl = () => {
        control.innerHTML = '';
        for (let i = 1; i <= totalPages; i++) {
          control.appendChild(createPageBtn(i, i === currentPage));
        }
      };

      updateControl();
      return control;
    };

    return {
      getPage,
      getCurrentPage: () => currentPage,
      getTotalPages: () => totalPages,
      getControl: createControl,
      setPage: (page) => {
        currentPage = Math.max(1, Math.min(page, totalPages));
      }
    };
  },

  /**
   * Create a modal dialog
   * @param {Object} config - Modal configuration
   * @returns {Object} Modal control object
   */
  createModal(config) {
    const {
      title,
      content,
      onClose = () => {}
    } = config;

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.cssText = `
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    `;

    const dialog = document.createElement('div');
    dialog.className = 'modal-dialog';
    dialog.style.cssText = `
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 2rem;
      max-width: 500px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
    `;

    dialog.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h2 style="margin: 0; font-family: var(--font-display);">${title}</h2>
        <button class="modal-close" style="background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1.5rem;">×</button>
      </div>
      <div class="modal-content">${content}</div>
    `;

    modal.appendChild(dialog);

    const close = () => {
      modal.style.display = 'none';
      onClose();
    };

    dialog.querySelector('.modal-close').addEventListener('click', close);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) close();
    });

    return {
      element: modal,
      open: () => {
        modal.style.display = 'flex';
      },
      close
    };
  },

  /**
   * Create a toast notification
   * @param {Object} config - Toast configuration
   */
  createToast(config) {
    const {
      message,
      variant = 'info',
      duration = 3000
    } = config;

    const toast = document.createElement('div');
    toast.className = `toast toast-${variant}`;
    toast.style.cssText = `
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: ${variant === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255, 107, 53, 0.12)'};
      border: 1px solid ${variant === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255, 107, 53, 0.3)'};
      color: ${variant === 'success' ? 'var(--green)' : 'var(--accent)'};
      padding: 1rem 1.5rem;
      border-radius: var(--radius-sm);
      font-weight: 600;
      z-index: 10000;
      animation: slideInRight 0.3s ease-out;
      max-width: 400px;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  /**
   * Format date for display
   * @param {Date|string} date - Date to format
   * @param {string} format - Format string
   * @returns {string} Formatted date
   */
  formatDate(date, format = 'short') {
    const d = new Date(date);
    const options = format === 'short'
      ? { year: 'numeric', month: 'short', day: 'numeric' }
      : { year: 'numeric', month: 'long', day: 'numeric' };
    return d.toLocaleDateString('en-US', options);
  },

  /**
   * Calculate reading time for text
   * @param {string} text - Text content
   * @returns {number} Estimated reading time in minutes
   */
  calculateReadingTime(text) {
    const wordsPerMinute = 200;
    const wordCount = (text || '').split(/\s+/).length;
    return Math.ceil(wordCount / wordsPerMinute);
  },

  /**
   * Truncate text with ellipsis
   * @param {string} text - Text to truncate
   * @param {number} maxLength - Maximum length
   * @returns {string} Truncated text
   */
  truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  },

  /**
   * Debounce a function
   * @param {Function} fn - Function to debounce
   * @param {number} delay - Delay in ms
   * @returns {Function} Debounced function
   */
  debounce(fn, delay = 300) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  },

  /**
   * Throttle a function
   * @param {Function} fn - Function to throttle
   * @param {number} limit - Limit in ms
   * @returns {Function} Throttled function
   */
  throttle(fn, limit = 300) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        fn.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Get query parameters from URL
   * @returns {Object} Query parameters
   */
  getQueryParams() {
    const params = {};
    const searchParams = new URLSearchParams(window.location.search);
    for (const [key, value] of searchParams.entries()) {
      params[key] = value;
    }
    return params;
  },

  /**
   * Set query parameters in URL without reload
   * @param {Object} params - Parameters to set
   */
  setQueryParams(params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value) searchParams.set(key, value);
    }
    const newUrl = window.location.pathname + (searchParams.toString() ? '?' + searchParams.toString() : '');
    window.history.replaceState({}, '', newUrl);
  }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ComponentLibrary;
}
