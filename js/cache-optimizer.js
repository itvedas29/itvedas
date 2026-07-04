/**
 * Cache Optimization Strategy
 * Multi-layer caching: IndexedDB, LocalStorage, Service Worker
 */

const CacheOptimizer = (() => {
  const CACHE_VERSION = 'itvedas-v1';
  const CACHE_STRATEGIES = {
    CACHE_FIRST: 'cache-first',
    NETWORK_FIRST: 'network-first',
    STALE_WHILE_REVALIDATE: 'stale-while-revalidate'
  };

  let isCacheReady = false;
  let cacheStats = {
    indexedDBSize: 0,
    localStorageSize: 0,
    cacheStorageSize: 0
  };

  /**
   * Initialize all cache layers
   */
  async function init() {
    initIndexedDB();
    initLocalStorage();
    if ('serviceWorker' in navigator) {
      await initServiceWorker();
    }
    isCacheReady = true;
  }

  /**
   * Initialize IndexedDB for large data
   */
  function initIndexedDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ITVedas', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Store for search index
        if (!db.objectStoreNames.contains('search-index')) {
          const store = db.createObjectStore('search-index', { keyPath: 'file' });
          store.createIndex('topic', 'topic', { unique: false });
        }

        // Store for page cache
        if (!db.objectStoreNames.contains('pages')) {
          db.createObjectStore('pages', { keyPath: 'url' });
        }

        // Store for API responses
        if (!db.objectStoreNames.contains('api-cache')) {
          const store = db.createObjectStore('api-cache', { keyPath: 'url' });
          store.createIndex('expires', 'expires', { unique: false });
        }
      };
    });
  }

  /**
   * Initialize LocalStorage for small, frequently-accessed data
   */
  function initLocalStorage() {
    try {
      const test = '__test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);

      // Store preferences
      const prefs = localStorage.getItem('user-prefs');
      if (!prefs) {
        localStorage.setItem('user-prefs', JSON.stringify({
          theme: 'dark',
          language: 'en',
          reducedMotion: false,
          cacheEnabled: true
        }));
      }

      return true;
    } catch (e) {
      console.warn('LocalStorage not available');
      return false;
    }
  }

  /**
   * Initialize Service Worker for offline support
   */
  async function initServiceWorker() {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });
      console.log('Service Worker registered:', registration);
      return registration;
    } catch (error) {
      console.warn('Service Worker registration failed:', error);
    }
  }

  /**
   * Store data in IndexedDB
   */
  async function setIndexedDB(store, key, value) {
    const db = await getDatabase();
    const transaction = db.transaction([store], 'readwrite');
    const objectStore = transaction.objectStore(store);

    return new Promise((resolve, reject) => {
      const request = objectStore.put({ ...value, [key]: key });
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Get data from IndexedDB
   */
  async function getIndexedDB(store, key) {
    const db = await getDatabase();
    const transaction = db.transaction([store], 'readonly');
    const objectStore = transaction.objectStore(store);

    return new Promise((resolve, reject) => {
      const request = objectStore.get(key);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Get IndexedDB database reference
   */
  async function getDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ITVedas', 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  /**
   * Cache API response with strategy
   */
  async function cacheResponse(url, response, strategy = CACHE_STRATEGIES.CACHE_FIRST, ttl = 3600000) {
    if (!response.ok) return response;

    const cacheKey = new URL(url, window.location.origin).href;

    // Store in IndexedDB with expiration
    await setIndexedDB('api-cache', cacheKey, {
      url: cacheKey,
      data: await response.clone().json(),
      expires: Date.now() + ttl,
      strategy,
      timestamp: Date.now()
    });

    return response;
  }

  /**
   * Get cached response
   */
  async function getCachedResponse(url) {
    const cacheKey = new URL(url, window.location.origin).href;
    const cached = await getIndexedDB('api-cache', cacheKey);

    if (cached && cached.expires > Date.now()) {
      return cached;
    }

    return null;
  }

  /**
   * Prefetch resources
   */
  async function prefetch(urls) {
    if (!('cache' in window)) return;

    const cache = await caches.open(CACHE_VERSION);

    const requests = urls.map(url => {
      return fetch(url).then(response => {
        if (response.ok) {
          cache.put(url, response.clone());
        }
      }).catch(e => console.warn(`Prefetch failed for ${url}:`, e));
    });

    await Promise.allSettled(requests);
  }

  /**
   * Warm up cache with critical resources
   */
  async function warmupCache() {
    const criticalResources = [
      '/search-index.json',
      '/css/shared.css',
      '/js/breadcrumb-generator.js',
      '/js/image-optimizer.js',
      '/js/mobile-nav.js'
    ];

    await prefetch(criticalResources);
  }

  /**
   * Clear expired cache entries
   */
  async function clearExpired() {
    try {
      const db = await getDatabase();
      const transaction = db.transaction(['api-cache'], 'readwrite');
      const objectStore = transaction.objectStore('api-cache');
      const index = objectStore.index('expires');
      const range = IDBKeyRange.upperBound(Date.now());

      return new Promise((resolve, reject) => {
        const request = index.openCursor(range);

        request.onerror = () => reject(request.error);
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor) {
            objectStore.delete(cursor.primaryKey);
            cursor.continue();
          } else {
            resolve();
          }
        };
      });
    } catch (error) {
      console.warn('Clear expired cache failed:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async function getStats() {
    try {
      // Estimate storage usage
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        cacheStats.storageUsage = estimate.usage;
        cacheStats.storageQuota = estimate.quota;
      }

      // Get cache storage size
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        let totalSize = 0;

        for (const cacheName of cacheNames) {
          const cache = await caches.open(cacheName);
          const keys = await cache.keys();
          totalSize += keys.length;
        }

        cacheStats.cacheStorageSize = totalSize;
      }

      return cacheStats;
    } catch (error) {
      console.warn('Get cache stats failed:', error);
      return cacheStats;
    }
  }

  /**
   * Clear all caches
   */
  async function clearAllCaches() {
    try {
      // Clear IndexedDB
      const db = await getDatabase();
      db.close();
      indexedDB.deleteDatabase('ITVedas');

      // Clear LocalStorage
      localStorage.clear();

      // Clear Service Worker cache
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
      }

      cacheStats = {
        indexedDBSize: 0,
        localStorageSize: 0,
        cacheStorageSize: 0
      };

      return true;
    } catch (error) {
      console.error('Clear all caches failed:', error);
      return false;
    }
  }

  /**
   * Log cache statistics
   */
  async function logStats() {
    const stats = await getStats();

    console.log('\n💾 Cache Statistics');
    console.log('='.repeat(60));
    console.log(`IndexedDB: ${stats.indexedDBSize || 'N/A'}`);
    console.log(`LocalStorage: ${stats.localStorageSize || 'N/A'}`);
    console.log(`Cache Storage: ${stats.cacheStorageSize || 'N/A'}`);
    if (stats.storageUsage && stats.storageQuota) {
      const usage = (stats.storageUsage / stats.storageQuota * 100).toFixed(1);
      console.log(`Storage Usage: ${usage}% (${formatBytes(stats.storageUsage)} / ${formatBytes(stats.storageQuota)})`);
    }
    console.log('='.repeat(60) + '\n');
  }

  /**
   * Format bytes for display
   */
  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  // Public API
  return {
    init,
    setIndexedDB,
    getIndexedDB,
    cacheResponse,
    getCachedResponse,
    prefetch,
    warmupCache,
    clearExpired,
    getStats,
    clearAllCaches,
    logStats,
    CACHE_STRATEGIES
  };
})();

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    CacheOptimizer.init().then(() => {
      CacheOptimizer.warmupCache();
    });
  });
} else {
  CacheOptimizer.init().then(() => {
    CacheOptimizer.warmupCache();
  });
}
