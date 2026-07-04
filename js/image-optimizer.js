/**
 * Image Optimizer
 * Handles lazy loading, responsive images, and WebP optimization
 */

const ImageOptimizer = (() => {
  const observedImages = new Set();
  let intersectionObserver = null;

  /**
   * Initialize Intersection Observer for lazy loading
   */
  function initObserver() {
    if (intersectionObserver) return;

    intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            loadImage(entry.target);
          }
        });
      },
      {
        root: null,
        rootMargin: '50px',
        threshold: 0.01
      }
    );
  }

  /**
   * Load image from lazy-load data attributes
   */
  function loadImage(img) {
    if (!img.dataset.src) return;

    img.src = img.dataset.src;
    if (img.dataset.srcset) {
      img.srcset = img.dataset.srcset;
    }

    img.classList.add('loaded');
    observedImages.add(img);

    if (intersectionObserver) {
      intersectionObserver.unobserve(img);
    }
  }

  /**
   * Convert regular images to lazy-loaded versions
   */
  function optimizeImage(img) {
    if (observedImages.has(img)) return;

    // Skip if already has lazy-load attributes
    if (img.dataset.src) return;

    // Skip very small images (icons, etc.)
    if (img.width && img.width < 50 && img.height && img.height < 50) {
      return;
    }

    // Add loading attribute
    img.loading = 'lazy';

    // If image is already in viewport, load immediately
    if (img.getBoundingClientRect().top < window.innerHeight + 50) {
      loadImage(img);
    } else {
      // For non-critical images, use intersection observer
      if (intersectionObserver) {
        intersectionObserver.observe(img);
      }
    }

    observedImages.add(img);
  }

  /**
   * Generate responsive image srcset
   * @param {string} src - Original image source
   * @returns {string} srcset string for responsive images
   */
  function generateSrcset(src) {
    // Skip if not a relative or local path
    if (!src || src.startsWith('http')) return '';

    // For local images, generate sizes
    const baseName = src.split('.')[0];
    const ext = src.split('.').pop();

    // Generate common responsive sizes
    return `${baseName}-sm.${ext} 480w, ${baseName}-md.${ext} 768w, ${src} 1200w`;
  }

  /**
   * Apply sizes attribute for responsive loading
   * @param {HTMLImageElement} img - Image element
   */
  function applySizes(img) {
    // Common responsive breakpoints
    const width = img.width || img.getBoundingClientRect().width;

    let sizes = '';
    if (width >= 800) {
      sizes = '(min-width: 1200px) 800px, (min-width: 768px) 600px, 100vw';
    } else if (width >= 600) {
      sizes = '(min-width: 768px) 600px, 100vw';
    } else {
      sizes = '100vw';
    }

    if (sizes && !img.sizes) {
      img.sizes = sizes;
    }
  }

  /**
   * Add dimension preservation to prevent layout shift
   */
  function preserveAspectRatio(img) {
    // Get dimensions
    const width = img.width || img.dataset.width;
    const height = img.height || img.dataset.height;

    if (width && height) {
      const aspectRatio = (height / width * 100).toFixed(2);
      const container = document.createElement('div');
      container.className = 'image-container';
      container.style.paddingBottom = `${aspectRatio}%`;
      container.style.position = 'relative';
      container.style.overflow = 'hidden';

      img.style.position = 'absolute';
      img.style.top = '0';
      img.style.left = '0';
      img.style.width = '100%';
      img.style.height = '100%';
      img.style.objectFit = 'cover';

      img.parentNode.insertBefore(container, img);
      container.appendChild(img);
    }
  }

  /**
   * Optimize all images on page
   */
  function optimizeAll() {
    initObserver();

    const images = document.querySelectorAll('img');
    images.forEach(img => {
      // Skip if already optimized
      if (observedImages.has(img)) return;

      // Apply lazy loading
      optimizeImage(img);

      // Apply responsive sizes
      applySizes(img);

      // Preserve aspect ratio
      if (img.width && img.height) {
        preserveAspectRatio(img);
      }

      // Ensure alt text
      if (!img.alt) {
        img.alt = 'Article image';
      }
    });
  }

  /**
   * Watch for dynamically added images (for SPA support)
   */
  function watchDOMChanges() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) { // Element node
            if (node.tagName === 'IMG') {
              optimizeImage(node);
            }
            // Check for images in added HTML
            const newImages = node.querySelectorAll?.('img');
            if (newImages) {
              newImages.forEach(img => optimizeImage(img));
            }
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    return observer;
  }

  /**
   * Get image statistics
   */
  function getStats() {
    const images = document.querySelectorAll('img');
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');

    return {
      totalImages: images.length,
      lazyLoadedImages: lazyImages.length,
      imagesWithoutAlt: imagesWithoutAlt.length,
      lazyLoadPercentage: (lazyImages.length / images.length * 100).toFixed(1) + '%'
    };
  }

  // Public API
  return {
    optimizeAll,
    optimizeImage,
    generateSrcset,
    applySizes,
    preserveAspectRatio,
    watchDOMChanges,
    getStats,
    loadImage
  };
})();

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ImageOptimizer.optimizeAll();
    ImageOptimizer.watchDOMChanges();
  });
} else {
  ImageOptimizer.optimizeAll();
  ImageOptimizer.watchDOMChanges();
}

// Also optimize on window load (for images loaded after DOM ready)
window.addEventListener('load', () => {
  ImageOptimizer.optimizeAll();
});
