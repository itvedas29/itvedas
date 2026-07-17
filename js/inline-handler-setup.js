/**
 * Universal Event Listener Setup for Refactored Inline Handlers
 * Converts onclick= attributes (refactored as data attributes) to proper event listeners
 */

document.addEventListener('DOMContentLoaded', () => {
  // Toggle accordion/expandable elements
  document.querySelectorAll('.problem-toggle').forEach(el => {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      const card = this.closest('.problem-card') || this.parentElement;
      if (card) {
        card.classList.toggle('open');
      }
    });
  });

  // Filter by chapter
  document.querySelectorAll('.filter-chapter').forEach(el => {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      const chapter = this.dataset.filterChapter;

      document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
      this.classList.add('active');

      document.querySelectorAll('.chapter-section').forEach(sec => {
        if (chapter === 'all' || sec.dataset.chapter === chapter) {
          sec.classList.remove('hidden');
        } else {
          sec.classList.add('hidden');
        }
      });

      if (chapter !== 'all') {
        setTimeout(() => {
          const element = document.getElementById(chapter);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 50);
      }
    });
  });

  // Filter by severity
  document.querySelectorAll('.filter-severity').forEach(el => {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      const severity = this.dataset.filterSeverity;

      document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
      this.classList.add('active');

      document.querySelectorAll('.chapter-section').forEach(sec => sec.classList.remove('hidden'));
      document.querySelectorAll('.problem-card').forEach(card => {
        card.classList.toggle('hidden', card.dataset.sev !== severity);
      });
    });
  });

  // Navigation links (e.g., tools index)
  document.querySelectorAll('.nav-link').forEach(el => {
    el.addEventListener('click', function(e) {
      const href = this.dataset.href;
      if (href) {
        window.location.href = href;
      }
    });
  });

  // Generic function handlers (data-onclick with optional data-arg)
  document.querySelectorAll('[data-onclick]').forEach(el => {
    el.addEventListener('click', function(e) {
      const functionName = this.dataset.onclick;
      const arg = this.dataset.arg;

      if (typeof window[functionName] === 'function') {
        if (arg) {
          window[functionName](arg);
        } else {
          window[functionName]();
        }
      }
    });
  });
});
