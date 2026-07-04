/**
 * Documentation UI Module
 * Handles reading time, difficulty badges, TOC, progress indicators, copy buttons
 */

const DocumentationUI = (() => {
  const config = {
    wordsPerMinute: 200,
    tocSelector: '.doc-toc-list',
    contentSelector: 'main, article, .article-content',
    headingSelector: 'h1, h2, h3, h4, h5, h6',
    codeBlockSelector: 'pre'
  };

  /**
   * Initialize all documentation UI features
   */
  function init() {
    addReadingTime();
    generateTableOfContents();
    setupTableOfContentsListener();
    addCopyCodeButtons();
    setupCollapsibleSections();
    setupReadingProgress();
    setupStickyTOC();
  }

  /**
   * Calculate and display reading time
   */
  function addReadingTime() {
    const content = document.querySelector(config.contentSelector);
    if (!content) return;

    const text = content.innerText || content.textContent;
    const words = text.trim().split(/\s+/).length;
    const readingTime = Math.ceil(words / config.wordsPerMinute);

    const readingTimeEl = document.querySelector('.reading-time');
    if (readingTimeEl) {
      readingTimeEl.textContent = `${readingTime} min read`;
      readingTimeEl.insertAdjacentHTML('afterbegin', '⏱ ');
    }
  }

  /**
   * Generate table of contents from headings
   */
  function generateTableOfContents() {
    const content = document.querySelector(config.contentSelector);
    if (!content) return;

    const headings = content.querySelectorAll(config.headingSelector);
    if (headings.length === 0) return;

    const tocList = document.querySelector(config.tocSelector);
    if (!tocList) return;

    const toc = [];
    headings.forEach((heading, index) => {
      if (!heading.id) {
        heading.id = `heading-${index}`;
      }

      const level = parseInt(heading.tagName[1]);
      const text = heading.textContent.trim();

      toc.push({
        id: heading.id,
        level,
        text,
        element: heading
      });
    });

    // Build hierarchical TOC
    let html = '';
    let currentLevel = 0;

    toc.forEach(item => {
      if (item.level > currentLevel) {
        for (let i = currentLevel; i < item.level; i++) {
          html += '<ul class="doc-toc-list-nested">';
        }
      } else if (item.level < currentLevel) {
        for (let i = item.level; i < currentLevel; i++) {
          html += '</ul>';
        }
      }

      html += `
        <li class="doc-toc-item level-${item.level}">
          <a href="#${item.id}" class="doc-toc-link">${item.text}</a>
        </li>
      `;
      currentLevel = item.level;
    });

    // Close any remaining open lists
    for (let i = 1; i < currentLevel; i++) {
      html += '</ul>';
    }

    tocList.innerHTML = html;
  }

  /**
   * Update TOC highlighting as user scrolls
   */
  function setupTableOfContentsListener() {
    const content = document.querySelector(config.contentSelector);
    if (!content) return;

    const headings = content.querySelectorAll(config.headingSelector);
    if (headings.length === 0) return;

    window.addEventListener('scroll', () => {
      let current = null;
      headings.forEach(heading => {
        const rect = heading.getBoundingClientRect();
        if (rect.top <= 150) {
          current = heading;
        }
      });

      // Update active link in TOC
      document.querySelectorAll('.doc-toc-link').forEach(link => {
        link.classList.remove('active');
      });

      if (current) {
        const activeLink = document.querySelector(`.doc-toc-link[href="#${current.id}"]`);
        if (activeLink) {
          activeLink.classList.add('active');
          activeLink.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }
    });
  }

  /**
   * Add copy-to-clipboard buttons to code blocks
   */
  function addCopyCodeButtons() {
    const codeBlocks = document.querySelectorAll(config.codeBlockSelector);

    codeBlocks.forEach((block, index) => {
      if (block.querySelector('.copy-code-button')) return; // Already has button

      const wrapper = document.createElement('div');
      wrapper.className = 'code-block-wrapper';

      const button = document.createElement('button');
      button.className = 'copy-code-button';
      button.setAttribute('aria-label', 'Copy code to clipboard');
      button.textContent = '📋 Copy';

      button.addEventListener('click', () => {
        const code = block.textContent;
        navigator.clipboard.writeText(code).then(() => {
          button.classList.add('copied');
          setTimeout(() => {
            button.classList.remove('copied');
          }, 2000);
        });
      });

      block.parentNode.insertBefore(wrapper, block);
      wrapper.appendChild(block);
      wrapper.insertBefore(button, block);
    });
  }

  /**
   * Setup collapsible sections for advanced content
   */
  function setupCollapsibleSections() {
    const headers = document.querySelectorAll('.collapsible-header');

    headers.forEach(header => {
      header.addEventListener('click', () => {
        header.classList.toggle('expanded');
      });

      // Allow keyboard navigation
      header.setAttribute('tabindex', '0');
      header.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          header.click();
        }
      });
    });
  }

  /**
   * Setup reading progress indicator
   */
  function setupReadingProgress() {
    const progressBar = document.querySelector('.reading-progress-bar');
    if (!progressBar) return;

    const content = document.querySelector(config.contentSelector);
    if (!content) return;

    window.addEventListener('scroll', () => {
      const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = window.scrollY;
      const progress = (scrolled / windowHeight) * 100;
      progressBar.style.width = Math.min(progress, 100) + '%';
    });
  }

  /**
   * Setup sticky TOC behavior
   */
  function setupStickyTOC() {
    const toc = document.querySelector('.doc-toc');
    if (!toc) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          toc.style.position = 'sticky';
        }
      });
    });

    // Start observing after content area
    const content = document.querySelector(config.contentSelector);
    if (content) {
      observer.observe(content);
    }
  }

  /**
   * Get article metadata
   */
  function getMetadata() {
    const content = document.querySelector(config.contentSelector);
    const text = content ? (content.innerText || content.textContent) : '';
    const words = text.trim().split(/\s+/).length;
    const readingTime = Math.ceil(words / config.wordsPerMinute);

    return {
      wordCount: words,
      readingTime: readingTime,
      headingCount: document.querySelectorAll(config.headingSelector).length,
      codeBlockCount: document.querySelectorAll(config.codeBlockSelector).length
    };
  }

  /**
   * Set article difficulty level
   */
  function setDifficulty(level) {
    // level: 'beginner', 'intermediate', 'advanced', 'expert'
    const badge = document.querySelector('.difficulty-badge');
    if (badge) {
      badge.className = `difficulty-badge difficulty-${level}`;
      badge.textContent = level.charAt(0).toUpperCase() + level.slice(1);
    }
  }

  /**
   * Add prerequisites section
   */
  function setPrerequisites(items) {
    const prereqSection = document.querySelector('.prerequisites');
    if (!prereqSection) return;

    const ul = prereqSection.querySelector('ul') || document.createElement('ul');
    ul.innerHTML = '';

    items.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      ul.appendChild(li);
    });

    if (!prereqSection.querySelector('ul')) {
      prereqSection.appendChild(ul);
    }
  }

  /**
   * Log documentation statistics
   */
  function logStats() {
    const metadata = getMetadata();
    console.log('\n📖 Documentation Statistics');
    console.log('='.repeat(60));
    console.log(`Word Count: ${metadata.wordCount}`);
    console.log(`Reading Time: ${metadata.readingTime} min`);
    console.log(`Headings: ${metadata.headingCount}`);
    console.log(`Code Blocks: ${metadata.codeBlockCount}`);
    console.log('='.repeat(60) + '\n');
  }

  // Public API
  return {
    init,
    getMetadata,
    setDifficulty,
    setPrerequisites,
    logStats
  };
})();

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    DocumentationUI.init();
  });
} else {
  DocumentationUI.init();
}
