// Scroll reveal, stagger, and the sticky CTA bar.
//
// Deliberately no animation library: this is ~40 lines of IntersectionObserver
// against a CSS transition, which keeps the CSP at script-src 'self' and adds
// no network request before content can animate.
(function () {
  var root = document.documentElement;

  // Content is visible by default in CSS; we only opt into the hidden
  // starting state once we know JS is running and the user hasn't asked for
  // reduced motion. A crawler, or a visitor whose JS failed, sees everything.
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var supported = 'IntersectionObserver' in window;

  if (supported && !reduced) {
    root.classList.add('js-reveal');

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target); // reveal once, never re-hide
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

    document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
      if (el.classList.contains('reveal-stagger')) {
        // Cap the per-item delay so long grids don't crawl: with 10+ cards a
        // 60ms step would leave the last one arriving nearly a second late.
        var children = el.children;
        var step = children.length > 8 ? 0.03 : 0.06;
        for (var i = 0; i < children.length; i++) {
          children[i].style.transitionDelay = (i * step).toFixed(2) + 's';
        }
      }
      observer.observe(el);
    });
  }

  // --- sticky CTA ---------------------------------------------------------
  var bar = document.querySelector('.sticky-cta');
  var sentinel = document.querySelector('[data-cta-sentinel]');
  if (bar && sentinel && supported) {
    new IntersectionObserver(function (entries) {
      // Show the bar only once the hero CTA has scrolled out of view above.
      var e = entries[0];
      var scrolledPast = !e.isIntersecting && e.boundingClientRect.top < 0;
      bar.classList.toggle('is-visible', scrolledPast);
    }, { threshold: 0 }).observe(sentinel);
  }
})();
