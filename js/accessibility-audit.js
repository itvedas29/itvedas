/**
 * Accessibility Audit & Compliance
 * WCAG 2.1 AA compliance checking and auto-fixes
 * Screen reader optimization, keyboard navigation, color contrast
 */

const AccessibilityAudit = (() => {
  const issues = [];
  const fixes = [];

  /**
   * Run complete accessibility audit
   */
  async function audit() {
    console.log('🔍 Starting accessibility audit...');

    await checkColorContrast();
    checkHeadingStructure();
    checkFormLabels();
    checkImageAltText();
    checkKeyboardNavigation();
    checkAriaLabels();
    checkFocusVisibility();
    checkLanguageAttribute();
    checkLinkContext();

    reportResults();
    return { issues, fixes };
  }

  /**
   * Check color contrast ratios (WCAG AA: 4.5:1 for normal text, 3:1 for large)
   */
  async function checkColorContrast() {
    const elements = document.querySelectorAll('p, span, a, label, h1, h2, h3, h4, h5, h6');

    elements.forEach(el => {
      const style = window.getComputedStyle(el);
      const color = style.color;
      const bgColor = style.backgroundColor;

      if (color && bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {
        const ratio = getContrastRatio(color, bgColor);

        if (ratio < 4.5) {
          issues.push({
            type: 'color-contrast',
            element: el,
            ratio,
            message: `Low contrast ratio (${ratio.toFixed(2)}:1, need 4.5:1): ${el.textContent?.substring(0, 50)}`
          });
        }
      }
    });
  }

  /**
   * Calculate contrast ratio between two colors
   */
  function getContrastRatio(fg, bg) {
    // Simple contrast calculation (approximation)
    const fgRGB = rgbToValues(fg);
    const bgRGB = rgbToValues(bg);

    const fgLum = calculateLuminance(fgRGB);
    const bgLum = calculateLuminance(bgRGB);

    const lighter = Math.max(fgLum, bgLum);
    const darker = Math.min(fgLum, bgLum);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Parse RGB string to values
   */
  function rgbToValues(rgbStr) {
    const match = rgbStr.match(/\d+/g);
    return match ? match.slice(0, 3).map(Number) : [0, 0, 0];
  }

  /**
   * Calculate relative luminance
   */
  function calculateLuminance([r, g, b]) {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  /**
   * Check heading structure (H1 first, no skipped levels)
   */
  function checkHeadingStructure() {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let lastLevel = 0;

    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName[1]);

      if (index === 0 && level !== 1) {
        issues.push({
          type: 'heading-structure',
          element: heading,
          message: `First heading should be H1, found ${heading.tagName}`
        });
      }

      if (level - lastLevel > 1) {
        issues.push({
          type: 'heading-structure',
          element: heading,
          message: `Heading level skipped from H${lastLevel} to H${level}`
        });
      }

      lastLevel = level;
    });
  }

  /**
   * Check form labels
   */
  function checkFormLabels() {
    const formInputs = document.querySelectorAll('input, textarea, select');

    formInputs.forEach(input => {
      const id = input.id;
      const ariaLabel = input.getAttribute('aria-label');

      if (!id && !ariaLabel) {
        issues.push({
          type: 'form-label',
          element: input,
          message: `Form input missing id or aria-label: ${input.type}`
        });
      }

      if (id) {
        const label = document.querySelector(`label[for="${id}"]`);
        if (!label && !ariaLabel) {
          issues.push({
            type: 'form-label',
            element: input,
            message: `No associated label found for input id="${id}"`
          });
        }
      }
    });
  }

  /**
   * Check image alt text
   */
  function checkImageAltText() {
    const images = document.querySelectorAll('img');

    images.forEach(img => {
      const alt = img.alt;
      const src = img.src;

      if (!alt && !src?.includes('/icon')) {
        issues.push({
          type: 'alt-text',
          element: img,
          message: `Image missing alt text: ${src?.substring(-30)}`
        });
      }

      if (alt && alt.toLowerCase().includes('image')) {
        issues.push({
          type: 'alt-text',
          element: img,
          message: `Alt text too generic: "${alt}"`
        });
      }
    });
  }

  /**
   * Check keyboard navigation
   */
  function checkKeyboardNavigation() {
    const interactiveElements = document.querySelectorAll('a, button, [role="button"], input, select, textarea');
    let tabbableCount = 0;

    interactiveElements.forEach(el => {
      const tabIndex = el.tabIndex;
      if (tabIndex >= 0 || !el.hasAttribute('tabindex')) {
        tabbableCount++;
      }
    });

    if (tabbableCount === 0) {
      issues.push({
        type: 'keyboard-nav',
        message: 'No keyboard-tabbable elements found on page'
      });
    }
  }

  /**
   * Check ARIA labels
   */
  function checkAriaLabels() {
    const iconButtons = document.querySelectorAll('button[aria-label], [role="button"][aria-label]');
    const buttonsWithoutLabels = document.querySelectorAll('button:not([aria-label]):not([title]):not(:has(span)), [role="button"]:not([aria-label]):not([title])');

    buttonsWithoutLabels.forEach(btn => {
      if (!btn.textContent?.trim()) {
        issues.push({
          type: 'aria-label',
          element: btn,
          message: `Icon button missing aria-label: ${btn.className}`
        });
      }
    });
  }

  /**
   * Check focus visibility
   */
  function checkFocusVisibility() {
    const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [role="button"]');
    let missingFocus = 0;

    interactiveElements.forEach(el => {
      const style = window.getComputedStyle(el, ':focus');
      const outline = style.outline || window.getComputedStyle(el).outline;

      if (!outline || outline === 'none') {
        missingFocus++;
      }
    });

    if (missingFocus > 0) {
      fixes.push({
        type: 'focus-visibility',
        message: `Add :focus-visible styles to ${missingFocus} interactive elements`
      });
    }
  }

  /**
   * Check language attribute
   */
  function checkLanguageAttribute() {
    const html = document.documentElement;
    if (!html.lang) {
      issues.push({
        type: 'language',
        message: 'Missing lang attribute on HTML element'
      });
    }
  }

  /**
   * Check link context (links must have descriptive text)
   */
  function checkLinkContext() {
    const links = document.querySelectorAll('a');

    links.forEach(link => {
      const text = link.textContent?.trim();
      const title = link.title;
      const ariaLabel = link.getAttribute('aria-label');

      if (!text && !title && !ariaLabel) {
        issues.push({
          type: 'link-context',
          element: link,
          message: `Link missing descriptive text or aria-label`
        });
      }

      if (text === 'click here' || text === 'read more' || text === 'learn more') {
        issues.push({
          type: 'link-context',
          element: link,
          message: `Link text not descriptive: "${text}"`
        });
      }
    });
  }

  /**
   * Report audit results
   */
  function reportResults() {
    console.log(`\n📊 Accessibility Audit Results`);
    console.log(`${'='.repeat(60)}`);
    console.log(`Issues found: ${issues.length}`);
    console.log(`Recommendations: ${fixes.length}`);

    if (issues.length > 0) {
      console.log(`\n⚠️  Issues:`);
      const issuesByType = {};
      issues.forEach(issue => {
        issuesByType[issue.type] = (issuesByType[issue.type] || 0) + 1;
        console.log(`  - [${issue.type}] ${issue.message}`);
      });
    }

    if (fixes.length > 0) {
      console.log(`\n✨ Recommendations:`);
      fixes.forEach(fix => {
        console.log(`  - [${fix.type}] ${fix.message}`);
      });
    }

    console.log(`\n${'='.repeat(60)}`);
  }

  /**
   * Auto-apply critical fixes
   */
  function autoFix() {
    console.log('🔧 Applying auto-fixes...');

    // Add focus styles to elements without them
    const style = document.createElement('style');
    style.textContent = `
      :focus-visible {
        outline: 2px solid #FF6B35;
        outline-offset: 2px;
        border-radius: 4px;
      }
    `;
    document.head.appendChild(style);

    // Ensure all links have title attribute if no text
    document.querySelectorAll('a:not([title]):not([aria-label])').forEach(link => {
      if (!link.textContent?.trim()) {
        link.title = 'Link';
      }
    });

    // Fix image alt text if missing
    document.querySelectorAll('img:not([alt])').forEach(img => {
      img.alt = 'Article image';
    });

    console.log('✅ Auto-fixes applied');
  }

  /**
   * Get accessibility score (0-100)
   */
  function getScore() {
    const criticalIssues = issues.filter(i =>
      i.type === 'color-contrast' || i.type === 'alt-text' || i.type === 'form-label'
    ).length;

    const score = Math.max(0, 100 - (criticalIssues * 5) - (issues.length * 2));
    return Math.round(score);
  }

  // Public API
  return {
    audit,
    autoFix,
    getScore,
    getIssues: () => issues,
    getFixes: () => fixes
  };
})();

// Auto-audit on page load (production can disable this)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // Only run in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      AccessibilityAudit.audit();
    }
  });
}
