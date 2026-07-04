/**
 * Analytics Tracker
 * Track user behavior, page performance, and engagement metrics
 */

const AnalyticsTracker = (() => {
  const config = {
    enabled: true,
    trackPageViews: true,
    trackEvents: true,
    trackPerformance: true,
    trackClickTracking: true,
    batchInterval: 5000 // ms
  };

  let sessionId = generateSessionId();
  let eventQueue = [];
  let performanceMetrics = {};
  let isProcessing = false;

  /**
   * Initialize analytics tracking
   */
  function init(options = {}) {
    Object.assign(config, options);

    if (config.enabled) {
      trackPageView();
      setupEventListeners();
      trackPerformanceMetrics();
      setupBatchProcessing();
    }
  }

  /**
   * Generate unique session ID
   */
  function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Track page view
   */
  function trackPageView() {
    const event = {
      type: 'pageview',
      url: window.location.pathname,
      title: document.title,
      referrer: document.referrer,
      timestamp: Date.now(),
      sessionId
    };

    queueEvent(event);
  }

  /**
   * Track custom event
   */
  function trackEvent(eventName, eventData = {}) {
    const event = {
      type: 'event',
      name: eventName,
      data: eventData,
      url: window.location.pathname,
      timestamp: Date.now(),
      sessionId
    };

    queueEvent(event);
  }

  /**
   * Track click events
   */
  function setupEventListeners() {
    if (config.trackClickTracking) {
      document.addEventListener('click', (e) => {
        const target = e.target.closest('a, button, [role="button"]');
        if (target) {
          const clickData = {
            text: target.textContent?.substring(0, 100),
            href: target.href,
            className: target.className,
            type: target.tagName.toLowerCase()
          };

          trackEvent('click', clickData);
        }
      }, true);
    }
  }

  /**
   * Track performance metrics
   */
  function trackPerformanceMetrics() {
    if (!config.trackPerformance) return;

    // Use PerformanceObserver if available
    if ('PerformanceObserver' in window) {
      try {
        // Track LCP (Largest Contentful Paint)
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];

          performanceMetrics.lcp = lastEntry.renderTime || lastEntry.loadTime;

          trackEvent('performance', {
            metric: 'LCP',
            value: performanceMetrics.lcp,
            unit: 'ms'
          });
        });

        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

        // Track CLS (Cumulative Layout Shift)
        const clsObserver = new PerformanceObserver((list) => {
          let clsValue = 0;
          list.getEntries().forEach((entry) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });

          performanceMetrics.cls = clsValue;

          trackEvent('performance', {
            metric: 'CLS',
            value: performanceMetrics.cls.toFixed(3),
            unit: 'score'
          });
        });

        clsObserver.observe({ entryTypes: ['layout-shift'] });

        // Track FCP (First Contentful Paint)
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          if (entries.length > 0) {
            performanceMetrics.fcp = entries[0].startTime;

            trackEvent('performance', {
              metric: 'FCP',
              value: performanceMetrics.fcp,
              unit: 'ms'
            });
          }
        });

        fcpObserver.observe({ entryTypes: ['paint'] });
      } catch (error) {
        console.warn('Performance monitoring failed:', error);
      }
    }

    // Also track traditional timing
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

  /**
   * Track scroll depth
   */
  function trackScrollDepth() {
    let maxScroll = 0;

    window.addEventListener('scroll', () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = window.scrollY;
      const scrollPercent = scrollHeight > 0 ? Math.round((scrolled / scrollHeight) * 100) : 0;

      if (scrollPercent > maxScroll) {
        maxScroll = scrollPercent;

        if (maxScroll % 25 === 0) {
          trackEvent('scroll', {
            depth: maxScroll,
            unit: 'percent'
          });
        }
      }
    });
  }

  /**
   * Track time on page
   */
  function trackTimeOnPage() {
    const startTime = Date.now();

    window.addEventListener('beforeunload', () => {
      const timeOnPage = Math.round((Date.now() - startTime) / 1000);

      trackEvent('engagement', {
        timeOnPage,
        unit: 'seconds'
      });
    });
  }

  /**
   * Queue event for batching
   */
  function queueEvent(event) {
    eventQueue.push(event);

    if (eventQueue.length >= 10) {
      processEventBatch();
    }
  }

  /**
   * Setup batching for efficiency
   */
  function setupBatchProcessing() {
    setInterval(() => {
      if (eventQueue.length > 0) {
        processEventBatch();
      }
    }, config.batchInterval);
  }

  /**
   * Process queued events
   */
  async function processEventBatch() {
    if (isProcessing || eventQueue.length === 0) return;

    isProcessing = true;
    const eventsToSend = [...eventQueue];
    eventQueue = [];

    try {
      const payload = {
        sessionId,
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
        events: eventsToSend
      };

      // Send to analytics endpoint (GA, Mixpanel, etc.)
      // For now, just log to console in development
      if (window.location.hostname === 'localhost') {
        console.log('📊 Analytics batch:', payload);
      } else {
        // In production, send to actual analytics service
        // await fetch('/api/analytics', {
        //   method: 'POST',
        //   body: JSON.stringify(payload),
        //   headers: { 'Content-Type': 'application/json' }
        // });
      }
    } catch (error) {
      console.warn('Analytics send failed:', error);
      // Re-queue events on failure
      eventQueue.push(...eventsToSend);
    } finally {
      isProcessing = false;
    }
  }

  /**
   * Get session analytics
   */
  function getSessionAnalytics() {
    return {
      sessionId,
      eventCount: eventQueue.length,
      performanceMetrics,
      config
    };
  }

  /**
   * Log analytics summary
   */
  function logSummary() {
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
  }

  // Public API
  return {
    init,
    trackPageView,
    trackEvent,
    trackScrollDepth,
    trackTimeOnPage,
    getSessionAnalytics,
    logSummary,
    processEventBatch,
    config
  };
})();

// Auto-initialize analytics
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
