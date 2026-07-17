/**
 * Accessibility Enhancements
 * Improves ARIA labels, semantic HTML, and keyboard navigation
 */

const AccessibilityEnhancements = (() => {
  /**
   * Add ARIA labels to navigation elements
   */
  function enhanceNavigation() {
    // Mark active navigation links
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a[href]').forEach(link => {
      const href = link.getAttribute('href');
      if (href === currentPath || href === currentPath + '/' ||
          (href.endsWith('.html') && currentPath.includes(href.replace('.html', '')))) {
        link.setAttribute('aria-current', 'page');
        link.classList.add('active');
      }
    });

    // Add ARIA labels to navigation
    const nav = document.querySelector('nav');
    if (nav && !nav.getAttribute('aria-label')) {
      nav.setAttribute('aria-label', 'Main navigation');
    }
  }

  /**
   * Fix landmark roles
   */
  function fixLandmarks() {
    const main = document.querySelector('main');
    if (!main && document.querySelector('article')) {
      const article = document.querySelector('article');
      if (article) {
        article.setAttribute('role', 'main');
      }
    }

    const footer = document.querySelector('footer');
    if (footer && !footer.getAttribute('role')) {
      footer.setAttribute('role', 'contentinfo');
    }
  }

  /**
   * Add alt text to images missing it
   */
  function fixImages() {
    document.querySelectorAll('img:not([alt])').forEach((img, index) => {
      if (img.src.includes('logo')) {
        img.setAttribute('alt', 'Logo');
      } else if (img.closest('a')) {
        img.setAttribute('alt', 'Link image');
      } else if (img.classList.contains('icon')) {
        img.setAttribute('alt', '');
        img.setAttribute('aria-hidden', 'true');
      } else {
        const title = document.querySelector('h1, title');
        const pageTitle = title ? title.textContent : 'Page';
        img.setAttribute('alt', `${pageTitle} image`);
      }
    });
  }

  /**
   * Add ARIA labels to icon-only buttons
   */
  function fixIconButtons() {
    document.querySelectorAll('button:not(:has(> *:not(svg, i, span.icon)))').forEach(btn => {
      const text = btn.textContent.trim();
      if (!text && !btn.getAttribute('aria-label')) {
        const title = btn.getAttribute('title') || btn.title;
        if (title) {
          btn.setAttribute('aria-label', title);
        } else {
          btn.setAttribute('aria-label', 'Action button');
        }
      }
    });
  }

  /**
   * Ensure buttons have proper type attribute
   */
  function fixButtonTypes() {
    document.querySelectorAll('button:not([type])').forEach(btn => {
      // If button is not in a form, set type="button"
      if (!btn.closest('form')) {
        btn.setAttribute('type', 'button');
      }
    });
  }

  /**
   * Add keyboard navigation to custom controls
   */
  function fixKeyboardNav() {
    document.querySelectorAll('[role="button"]:not(button)').forEach(el => {
      if (!el.hasAttribute('tabindex')) {
        el.setAttribute('tabindex', '0');
      }

      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          el.click();
        }
      });
    });
  }

  /**
   * Add skip to main content link
   */
  function addSkipLink() {
    const existing = document.querySelector('a.skip-to-main');
    if (existing) return;

    const skip = document.createElement('a');
    skip.href = '#main-content';
    skip.className = 'skip-to-main';
    skip.textContent = 'Skip to main content';
    skip.style.cssText = `
      position: absolute;
      left: -9999px;
      z-index: 999;
      padding: 1em;
      background-color: #000;
      color: #fff;
      text-decoration: none;
    `;

    skip.addEventListener('focus', () => {
      skip.style.left = '0';
    });

    skip.addEventListener('blur', () => {
      skip.style.left = '-9999px';
    });

    document.body.insertBefore(skip, document.body.firstChild);

    // Ensure main content has id
    const main = document.querySelector('main') || document.querySelector('[role="main"]');
    if (main && !main.id) {
      main.id = 'main-content';
    }
  }

  /**
   * Add headings hierarchy check
   */
  function checkHeadingHierarchy() {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let lastLevel = 0;

    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName[1]);
      if (index > 0 && level > lastLevel + 1) {
        console.warn(`Heading hierarchy issue: jumped from H${lastLevel} to H${level}`, heading);
      }
      lastLevel = level;
    });
  }

  /**
   * Announce dynamic content changes for screen readers
   */
  function setupLiveRegion() {
    let liveRegion = document.querySelector('[aria-live="polite"]');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.style.position = 'absolute';
      liveRegion.style.left = '-9999px';
      document.body.appendChild(liveRegion);
    }
    return liveRegion;
  }

  /**
   * Announce message to screen readers
   */
  function announce(message) {
    const region = setupLiveRegion();
    region.textContent = message;
    setTimeout(() => {
      region.textContent = '';
    }, 3000);
  }

  return {
    init() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          this.enhance();
        });
      } else {
        this.enhance();
      }
    },

    enhance() {
      enhanceNavigation();
      fixLandmarks();
      fixImages();
      fixIconButtons();
      fixButtonTypes();
      fixKeyboardNav();
      addSkipLink();
      checkHeadingHierarchy();
    },

    announce
  };
})();

// Auto-initialize on load
AccessibilityEnhancements.init();
