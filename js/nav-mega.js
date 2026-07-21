/* ITVedas — dropdown/mega-menu header nav behavior.
   Click or hover to open, Escape or outside-click to close, one open
   at a time. Mirrors the toggle pattern already used for the homepage's
   Resources dropdown so behavior stays consistent site-wide. */
(function () {
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
        var isOpen = drop.getAttribute('data-open') === 'true';
        closeAll(isOpen ? null : drop);
        drop.setAttribute('data-open', isOpen ? 'false' : 'true');
        btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
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
