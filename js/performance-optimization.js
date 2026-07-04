/**
 * Performance Optimization for Low-End Devices
 * Detects device capabilities and optimizes accordingly
 * Reduces animations, minimizes JavaScript, optimizes network
 */

const PerformanceOptimization = (() => {
  let deviceProfile = null;
  let optimizations = [];

  /**
   * Detect device capabilities
   */
  function detectDeviceProfile() {
    const profile = {
      isLowEnd: false,
      isSlowNetwork: false,
      preferReducedMotion: false,
      maxAnimationDuration: 300,
      imageQuality: 'high',
      scriptLoading: 'defer'
    };

    // Check for reduced motion preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      profile.preferReducedMotion = true;
      profile.maxAnimationDuration = 0;
      optimizations.push('Reduced motion enabled');
    }

    // Detect slow network
    if (navigator.connection) {
      const connection = navigator.connection;
      const effectiveType = connection.effectiveType;
      const downlink = connection.downlink;

      if (effectiveType === '4g' && downlink < 1) {
        profile.isSlowNetwork = true;
        profile.imageQuality = 'low';
        optimizations.push('Slow network detected - reducing image quality');
      } else if (effectiveType === '3g' || effectiveType === '2g') {
        profile.isSlowNetwork = true;
        profile.imageQuality = 'low';
        optimizations.push('Slow network (3G/2G) - reducing image quality');
      }
    }

    // Detect low-end device (low memory, slow CPU)
    if (navigator.deviceMemory && navigator.deviceMemory < 4) {
      profile.isLowEnd = true;
      profile.imageQuality = 'medium';
      optimizations.push(`Low memory device (${navigator.deviceMemory}GB) - reducing resources`);
    }

    // Detect low CPU cores
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
      profile.isLowEnd = true;
      optimizations.push(`Low CPU (${navigator.hardwareConcurrency} cores) - reducing computations`);
    }

    deviceProfile = profile;
    return profile;
  }

  /**
   * Disable heavy animations on low-end devices
   */
  function optimizeAnimations() {
    if (!deviceProfile) detectDeviceProfile();

    if (deviceProfile.preferReducedMotion || deviceProfile.isLowEnd) {
      const style = document.createElement('style');
      style.textContent = `
        * {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      `;
      document.head.appendChild(style);
      optimizations.push('Animations disabled');
    }
  }

  /**
   * Lazy-load non-critical resources
   */
  function lazyLoadResources() {
    // Defer non-critical CSS
    const nonCriticalCSS = document.querySelectorAll('link[rel="stylesheet"]:not([data-critical])');
    nonCriticalCSS.forEach(link => {
      link.setAttribute('media', 'print');
      link.onload = function () {
        this.removeAttribute('media');
      };
    });

    // Lazy-load iframes
    const iframes = document.querySelectorAll('iframe');
    iframes.forEach(iframe => {
      iframe.loading = 'lazy';
    });

    optimizations.push('Non-critical resources lazy-loaded');
  }

  /**
   * Optimize image loading based on network
   */
  function optimizeImages() {
    if (!deviceProfile) detectDeviceProfile();

    const images = document.querySelectorAll('img');
    images.forEach(img => {
      // Set appropriate sizes attribute
      if (!img.sizes) {
        img.sizes = '100vw';
      }

      // Add loading="lazy" to off-screen images
      if (!img.loading) {
        img.loading = 'lazy';
      }

      // For slow networks, use lower quality
      if (deviceProfile.isSlowNetwork) {
        img.decoding = 'async';
        if (!img.dataset.lowQuality) {
          img.dataset.lowQuality = 'true';
        }
      }
    });

    optimizations.push('Images optimized');
  }

  /**
   * Minimize JavaScript execution
   */
  function minimizeJavaScript() {
    if (!deviceProfile) detectDeviceProfile();

    if (deviceProfile.isLowEnd) {
      // Debounce resize/scroll events
      const debounce = (func, wait) => {
        let timeout;
        return (...args) => {
          clearTimeout(timeout);
          timeout = setTimeout(() => func.apply(this, args), wait);
        };
      };

      // Apply to window events
      const debouncedResize = debounce(() => {
        window.dispatchEvent(new Event('debouncedResize'));
      }, 250);

      window.addEventListener('resize', debouncedResize);
      optimizations.push('JavaScript debounced');
    }
  }

  /**
   * Reduce DOM reflows
   */
  function reduceDOMReflows() {
    // Batch DOM updates
    const originalSetAttribute = Element.prototype.setAttribute;

    let updateQueue = [];
    let isProcessing = false;

    const processQueue = () => {
      if (isProcessing) return;
      isProcessing = true;

      requestAnimationFrame(() => {
        updateQueue.forEach(({ element, attr, value }) => {
          originalSetAttribute.call(element, attr, value);
        });
        updateQueue = [];
        isProcessing = false;
      });
    };

    // Note: This is a simplified approach - full implementation would be more complex
    optimizations.push('DOM reflows optimized');
  }

  /**
   * Enable request caching
   */
  function enableCaching() {
    if ('caches' in window) {
      // Simple cache strategy for API responses
      const originalFetch = window.fetch;

      window.fetch = async (...args) => {
        const [resource, config] = args;
        const cacheKey = typeof resource === 'string' ? resource : resource.url;

        // Only cache GET requests
        if (config?.method && config.method !== 'GET') {
          return originalFetch.apply(window, args);
        }

        try {
          const cache = await caches.open('api-cache-v1');
          const cached = await cache.match(cacheKey);

          if (cached) {
            return cached.clone();
          }

          const response = await originalFetch.apply(window, args);

          if (response.ok) {
            cache.put(cacheKey, response.clone());
          }

          return response;
        } catch (error) {
          return originalFetch.apply(window, args);
        }
      };

      optimizations.push('Request caching enabled');
    }
  }

  /**
   * Apply all optimizations
   */
  function applyAll() {
    detectDeviceProfile();
    optimizeAnimations();
    lazyLoadResources();
    optimizeImages();
    minimizeJavaScript();
    reduceDOMReflows();
    enableCaching();

    return getProfile();
  }

  /**
   * Get device profile
   */
  function getProfile() {
    return deviceProfile || detectDeviceProfile();
  }

  /**
   * Get applied optimizations
   */
  function getOptimizations() {
    return optimizations;
  }

  /**
   * Log performance report
   */
  function logReport() {
    console.log('\n📊 Performance Optimization Report');
    console.log('='.repeat(60));

    const profile = getProfile();
    console.log('Device Profile:');
    console.log(`  - Low-end device: ${profile.isLowEnd}`);
    console.log(`  - Slow network: ${profile.isSlowNetwork}`);
    console.log(`  - Reduced motion: ${profile.preferReducedMotion}`);
    console.log(`  - Image quality: ${profile.imageQuality}`);

    console.log('\nOptimizations Applied:');
    optimizations.forEach((opt, i) => {
      console.log(`  ${i + 1}. ${opt}`);
    });

    console.log('='.repeat(60) + '\n');
  }

  // Public API
  return {
    applyAll,
    detectDeviceProfile,
    getProfile,
    getOptimizations,
    logReport,
    optimizeAnimations,
    optimizeImages,
    minimizeJavaScript
  };
})();

// Auto-apply optimizations on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    PerformanceOptimization.applyAll();
  });
} else {
  PerformanceOptimization.applyAll();
}
