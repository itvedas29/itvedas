/**
 * Mobile Navigation Handler
 * Touch-friendly navigation with hamburger menu and swipe support
 * Ensures 44x44px minimum touch targets
 */

const MobileNav = (() => {
  const TOUCH_TARGET_MIN = 44; // Minimum touch target size in pixels
  const MOBILE_BREAKPOINT = 768;

  let isMenuOpen = false;
  let hamburgerBtn = null;
  let navMenu = null;
  let closeBtn = null;

  /**
   * Initialize mobile navigation
   */
  function init() {
    detectMobileView();
    createHamburgerMenu();
    setupEventListeners();
    ensureTouchTargets();
    setupSwipeGestures();
  }

  /**
   * Detect if viewing on mobile
   */
  function detectMobileView() {
    return window.innerWidth < MOBILE_BREAKPOINT;
  }

  /**
   * Create hamburger menu button
   */
  function createHamburgerMenu() {
    // Check if hamburger already exists
    hamburgerBtn = document.querySelector('.mobile-menu-toggle');
    navMenu = document.querySelector('nav');

    if (!hamburgerBtn && navMenu && detectMobileView()) {
      // Create hamburger button
      hamburgerBtn = document.createElement('button');
      hamburgerBtn.className = 'mobile-menu-toggle';
      hamburgerBtn.setAttribute('aria-label', 'Toggle navigation menu');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
      hamburgerBtn.innerHTML = `
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
      `;

      // Insert into nav or create nav if missing
      if (navMenu) {
        const navRight = navMenu.querySelector('.nav-right') || navMenu;
        navRight.appendChild(hamburgerBtn);
      } else {
        document.body.insertBefore(hamburgerBtn, document.body.firstChild);
      }
    }
  }

  /**
   * Setup event listeners for menu interactions
   */
  function setupEventListeners() {
    if (!hamburgerBtn) return;

    // Toggle menu on hamburger click
    hamburgerBtn.addEventListener('click', toggleMenu);

    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isMenuOpen) {
        closeMenu();
      }
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (isMenuOpen && navMenu && !navMenu.contains(e.target) && !hamburgerBtn.contains(e.target)) {
        closeMenu();
      }
    });

    // Close menu when navigation link clicked
    const navLinks = document.querySelectorAll('nav a, .nav-links a');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (isMenuOpen) closeMenu();
      });
    });

    // Handle window resize
    window.addEventListener('resize', handleResize);
  }

  /**
   * Toggle menu open/closed
   */
  function toggleMenu() {
    if (isMenuOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  /**
   * Open mobile menu
   */
  function openMenu() {
    isMenuOpen = true;
    if (hamburgerBtn) {
      hamburgerBtn.classList.add('active');
      hamburgerBtn.setAttribute('aria-expanded', 'true');
    }
    if (navMenu) {
      navMenu.classList.add('mobile-menu-open');
    }
    document.body.style.overflow = 'hidden';
  }

  /**
   * Close mobile menu
   */
  function closeMenu() {
    isMenuOpen = false;
    if (hamburgerBtn) {
      hamburgerBtn.classList.remove('active');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
    }
    if (navMenu) {
      navMenu.classList.remove('mobile-menu-open');
    }
    document.body.style.overflow = '';
  }

  /**
   * Ensure all interactive elements have 44x44px minimum touch targets
   */
  function ensureTouchTargets() {
    const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [role="button"]');

    interactiveElements.forEach(el => {
      const rect = el.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      if (width < TOUCH_TARGET_MIN || height < TOUCH_TARGET_MIN) {
        // Add padding or wrapper to ensure minimum size
        el.style.minWidth = TOUCH_TARGET_MIN + 'px';
        el.style.minHeight = TOUCH_TARGET_MIN + 'px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
      }
    });
  }

  /**
   * Setup swipe gesture support for navigation
   */
  function setupSwipeGestures() {
    let touchStartX = 0;
    let touchEndX = 0;

    document.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, false);

    document.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipe();
    }, false);

    function handleSwipe() {
      const swipeThreshold = 50; // Minimum swipe distance
      const diff = touchStartX - touchEndX;

      // Swipe right (open menu)
      if (diff < -swipeThreshold && detectMobileView()) {
        openMenu();
      }
      // Swipe left (close menu)
      else if (diff > swipeThreshold && isMenuOpen) {
        closeMenu();
      }
    }
  }

  /**
   * Handle window resize events
   */
  function handleResize() {
    const isMobile = detectMobileView();

    if (!isMobile && isMenuOpen) {
      closeMenu();
    }

    // Ensure touch targets on resize
    ensureTouchTargets();
  }

  /**
   * Get mobile nav stats
   */
  function getStats() {
    return {
      isMobileView: detectMobileView(),
      menuOpen: isMenuOpen,
      breakpoint: MOBILE_BREAKPOINT,
      touchTargetMin: TOUCH_TARGET_MIN
    };
  }

  // Public API
  return {
    init,
    toggleMenu,
    openMenu,
    closeMenu,
    detectMobileView,
    ensureTouchTargets,
    getStats
  };
})();

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', MobileNav.init);
} else {
  MobileNav.init();
}
