/* ITVedas mobile nav — injects a hamburger button that toggles the existing
   .nav-links into a dropdown panel on small screens. Self-contained: no deps,
   styles injected, works with both <ul class="nav-links"> and
   <div class="nav-links"> variants. Coexists with nav-search.js. */
(function () {
  var nav = document.querySelector('nav');
  if (!nav) return;
  var links = nav.querySelector('.nav-links');
  if (!links || document.getElementById('navHamb')) return;

  /* ---------- styles ---------- */
  var css = document.createElement('style');
  css.textContent = [
    '.nav-hamburger{display:none;background:none;border:none;color:var(--text,#F0F0F8);cursor:pointer;padding:0.3rem;line-height:0;margin-left:0.25rem;}',
    '.nav-hamburger svg{width:24px;height:24px;stroke:currentColor;display:block;}',
    '@media(max-width:820px){',
    '  nav{position:relative;}',
    '  nav .nav-links{position:absolute;top:100%;left:0;right:0;flex-direction:column;align-items:flex-start;gap:0;',
    '    background:rgba(10,10,15,0.98);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);',
    '    border-bottom:1px solid var(--border,rgba(255,255,255,0.08));padding:0.5rem 1.25rem 1rem;',
    '    display:none;max-height:calc(100vh - 64px);overflow-y:auto;}',
    '  nav .nav-links.open{display:flex;}',
    '  nav .nav-links>li{width:100%;list-style:none;}',
    '  nav .nav-links>li>a,nav .nav-links>a{display:block;width:100%;padding:0.8rem 0;}',
    /* override the old ".nav-links a:not(.active){display:none}" rule some
       pages ship, which would otherwise hide every link but the active one
       inside the open panel */
    '  nav .nav-links.open a{display:block !important;}',
    '  .nav-hamburger{display:inline-flex;}',
    '}'
  ].join('\n');
  document.head.appendChild(css);

  /* ---------- hamburger button ---------- */
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'nav-hamburger';
  btn.id = 'navHamb';
  btn.setAttribute('aria-label', 'Toggle menu');
  btn.setAttribute('aria-expanded', 'false');
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>';
  nav.appendChild(btn);

  function setOpen(open) {
    links.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    setOpen(!links.classList.contains('open'));
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('nav')) setOpen(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });
  links.addEventListener('click', function (e) {
    if (e.target.closest('a')) setOpen(false);
  });
})();
