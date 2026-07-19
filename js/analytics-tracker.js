/**
 * Analytics Tracker
 * Tracks page views, events, performance metrics, and user engagement
 * Uses secure random session ID generation
 */

const AnalyticsTracker = (() => {
  const config = {
    enabled: true,
    trackPageViews: true,
    trackEvents: true,
    trackPerformance: true,
    trackClickTracking: true,
    batchInterval: 5000
  };

  // Generate cryptographically secure session ID
  let sessionId = generateSecureSessionId();
  let eventQueue = [];
  let performanceMetrics = {};
  let isSending = false;

  function generateSecureSessionId() {
    // Use crypto.getRandomValues if available (modern browsers)
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      const arr = new Uint8Array(16);
      crypto.getRandomValues(arr);
      const hex = Array.from(arr, byte => byte.toString(16).padStart(2, '0')).join('');
      return `session_${Date.now()}_${hex.substring(0, 16)}`;
    }
    // Fallback for older browsers - still better than Math.random alone
    const timestamp = Date.now().toString(36);
    const randomPart = Math.random().toString(36).substring(2, 15) +
                       Math.random().toString(36).substring(2, 15);
    return `session_${timestamp}_${randomPart}`;
  }

  function trackPageView() {
    queueEvent({
      type: 'pageview',
      url: window.location.pathname,
      title: document.title,
      referrer: document.referrer,
      timestamp: Date.now(),
      sessionId: sessionId
    });
  }

  function trackEvent(eventName, eventData = {}) {
    queueEvent({
      type: 'event',
      name: eventName,
      data: eventData,
      url: window.location.pathname,
      timestamp: Date.now(),
      sessionId: sessionId
    });
  }

  function queueEvent(event) {
    eventQueue.push(event);
    if (eventQueue.length >= 10) {
      sendBatch();
    }
  }

  async function sendBatch() {
    if (isSending || eventQueue.length === 0) return;

    isSending = true;
    const batch = [...eventQueue];
    eventQueue = [];

    try {
      const payload = {
        sessionId: sessionId,
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
        events: batch
      };

      if (window.location.hostname === 'localhost') {
        console.log('📊 Analytics batch:', payload);
      }
    } catch (error) {
      console.warn('Analytics send failed:', error);
      eventQueue.push(...batch);
    } finally {
      isSending = false;
    }
  }

  function setupClickTracking() {
    document.addEventListener('click', (event) => {
      const target = event.target.closest('a, button, [role="button"]');
      if (target) {
        trackEvent('click', {
          text: target.textContent?.substring(0, 100),
          href: target.href,
          className: target.className,
          type: target.tagName.toLowerCase()
        });
      }
    }, true);
  }

  function setupPerformanceTracking() {
    if (!config.trackPerformance) return;

    if ('PerformanceObserver' in window) {
      try {
        // Track Largest Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          performanceMetrics.lcp = lastEntry.renderTime || lastEntry.loadTime;
          trackEvent('performance', {
            metric: 'LCP',
            value: performanceMetrics.lcp,
            unit: 'ms'
          });
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // Track Cumulative Layout Shift
        new PerformanceObserver((list) => {
          let cls = 0;
          list.getEntries().forEach((entry) => {
            if (!entry.hadRecentInput) {
              cls += entry.value;
            }
          });
          performanceMetrics.cls = cls;
          trackEvent('performance', {
            metric: 'CLS',
            value: performanceMetrics.cls.toFixed(3),
            unit: 'score'
          });
        }).observe({ entryTypes: ['layout-shift'] });

        // Track First Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          if (entries.length > 0) {
            performanceMetrics.fcp = entries[0].startTime;
            trackEvent('performance', {
              metric: 'FCP',
              value: performanceMetrics.fcp,
              unit: 'ms'
            });
          }
        }).observe({ entryTypes: ['paint'] });
      } catch (error) {
        console.warn('Performance monitoring failed:', error);
      }
    }

    // Track Navigation Timing
    if (window.performance && window.performance.timing) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const timing = window.performance.timing;
          performanceMetrics.navigationTiming = {
            dns: timing.domainLookupEnd - timing.domainLookupStart,
            tcp: timing.connectEnd - timing.connectStart,
            ttfb: timing.responseStart - timing.navigationStart,
            download: timing.responseEnd - timing.responseStart,
            domParse: timing.domInteractive - timing.domLoading,
            domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
            pageLoad: timing.loadEventEnd - timing.navigationStart
          };
          trackEvent('performance', {
            metric: 'NavigationTiming',
            value: performanceMetrics.navigationTiming
          });
        }, 0);
      });
    }
  }

  // Public API
  return {
    init(options = {}) {
      Object.assign(config, options);

      if (!config.enabled) return;

      trackPageView();

      if (config.trackClickTracking) {
        setupClickTracking();
      }

      setupPerformanceTracking();

      // Send batches periodically
      setInterval(() => {
        if (eventQueue.length > 0) {
          sendBatch();
        }
      }, config.batchInterval);
    },

    trackPageView,
    trackEvent,

    trackScrollDepth() {
      let maxDepth = 0;
      window.addEventListener('scroll', () => {
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrolled = window.scrollY;
        const depth = docHeight > 0 ? Math.round((scrolled / docHeight) * 100) : 0;

        if (depth > maxDepth) {
          maxDepth = depth;
          if (maxDepth % 25 === 0) {
            trackEvent('scroll', {
              depth: maxDepth,
              unit: 'percent'
            });
          }
        }
      });
    },

    trackTimeOnPage() {
      const startTime = Date.now();
      window.addEventListener('beforeunload', () => {
        trackEvent('engagement', {
          timeOnPage: Math.round((Date.now() - startTime) / 1000),
          unit: 'seconds'
        });
      });
    },

    getSessionAnalytics() {
      return {
        sessionId,
        eventCount: eventQueue.length,
        performanceMetrics,
        config
      };
    },

    logSummary() {
      console.log('\n📊 Analytics Summary');
      console.log('='.repeat(60));
      console.log(`Session ID: ${sessionId}`);
      console.log(`Queued Events: ${eventQueue.length}`);

      if (Object.keys(performanceMetrics).length > 0) {
        console.log('Performance Metrics:');
        Object.entries(performanceMetrics).forEach(([key, value]) => {
          if (typeof value === 'object') {
            console.log(`  ${key}:`, value);
          } else {
            console.log(`  ${key}: ${value.toFixed ? value.toFixed(2) : value}`);
          }
        });
      }

      console.log('='.repeat(60) + '\n');
    },

    processEventBatch: sendBatch,
    config
  };
})();

// Initialize analytics when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    AnalyticsTracker.init({
      enabled: true,
      trackPageViews: true,
      trackEvents: true,
      trackPerformance: true
    });
    AnalyticsTracker.trackScrollDepth();
    AnalyticsTracker.trackTimeOnPage();
  });
} else {
  AnalyticsTracker.init({
    enabled: true,
    trackPageViews: true,
    trackEvents: true,
    trackPerformance: true
  });
  AnalyticsTracker.trackScrollDepth();
  AnalyticsTracker.trackTimeOnPage();
}
