/* ITVedas — dropdown/mega-menu header nav behavior.
   Hover opens/closes on desktop; click always opens (never toggles
   closed) so a mouse user hovering then clicking doesn't immediately
   close what their own hover just opened - mouseenter sets data-open
   before the click handler runs, so a click that reads and flips that
   same flag closes the panel it was meant to keep open. Closing is via
   mouseleave, an outside click, or Escape - never the open button itself. */
(function () {
  // Load the shared event layer. It uses the existing GA4 tag only and is a no-op
  // on pages that do not expose gtag(), so this never creates a second tag.
  if (!document.querySelector('script[src="/js/itvedas-events.js"]')) {
    var analytics = document.createElement('script');
    analytics.src = '/js/itvedas-events.js';
    analytics.async = true;
    document.head.appendChild(analytics);
  }
  function closeAll(except) {
    document.querySelectorAll('.nav-drop[data-open="true"]').forEach(function (d) {
      if (d !== except) {
        d.setAttribute('data-open', 'false');
        var btn = d.querySelector('.nav-drop-btn');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var drops = document.querySelectorAll('.nav-drop');
    drops.forEach(function (drop) {
      var btn = drop.querySelector('.nav-drop-btn');
      if (!btn) return;

      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        closeAll(drop);
        drop.setAttribute('data-open', 'true');
        btn.setAttribute('aria-expanded', 'true');
      });

      drop.addEventListener('mouseenter', function () {
        closeAll(drop);
        drop.setAttribute('data-open', 'true');
        btn.setAttribute('aria-expanded', 'true');
      });
      drop.addEventListener('mouseleave', function () {
        drop.setAttribute('data-open', 'false');
        btn.setAttribute('aria-expanded', 'false');
      });
    });

    document.addEventListener('click', function () { closeAll(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeAll();
    });
  });
})();
