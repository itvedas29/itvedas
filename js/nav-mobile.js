/* ============================================================================
   ITVedas — Modern Responsive Mobile Navigation
   Self-contained, accessible (WCAG AA), supports tap-outside dismiss and Escape.
   ============================================================================ */
(function () {
  var nav = document.querySelector('nav');
  if (!nav) return;
  var links = nav.querySelector('.nav-links');
  if (!links || document.getElementById('navHamb')) return;

  /* ---------- Modern Light-Theme Mobile Styles ---------- */
  var css = document.createElement('style');
  css.textContent = [
    '.nav-hamburger {',
    '  display: none;',
    '  background: none;',
    '  border: none;',
    '  color: var(--brand-navy, #0B2750);',
    '  cursor: pointer;',
    '  padding: 0.5rem;',
    '  line-height: 0;',
    '  border-radius: var(--radius-sm, 6px);',
    '  min-height: 44px;',
    '  min-width: 44px;',
    '  align-items: center;',
    '  justify-content: center;',
    '  transition: background var(--transition-fast, 150ms ease);',
    '}',
    '.nav-hamburger:focus-visible {',
    '  outline: 2px solid var(--accent, #FF7A00);',
    '}',
    '.nav-hamburger svg {',
    '  width: 24px;',
    '  height: 24px;',
    '  stroke: currentColor;',
    '  display: block;',
    '}',
    '@media(max-width: 820px) {',
    '  nav { position: fixed; top: 0; left: 0; right: 0; z-index: 1000; }',
    '  .nav-hamburger { display: inline-flex; }',
    '  nav .nav-links {',
    '    position: fixed;',
    '    top: var(--header-height, 64px);',
    '    left: 0;',
    '    right: 0;',
    '    background: #FFFFFF;',
    '    border-bottom: 1.5px solid var(--border, rgba(15, 23, 42, 0.12));',
    '    box-shadow: 0 16px 36px rgba(11, 39, 80, 0.14);',
    '    padding: 1rem 1.25rem 1.75rem;',
    '    flex-direction: column;',
    '    align-items: flex-start;',
    '    gap: 0.25rem;',
    '    display: none;',
    '    max-height: calc(100vh - var(--header-height, 64px));',
    '    overflow-y: auto;',
    '    -webkit-overflow-scrolling: touch;',
    '  }',
    '  nav .nav-links.open { display: flex; animation: slideDown 200ms cubic-bezier(0.4, 0, 0.2, 1); }',
    '  nav .nav-links > a, nav .nav-links li > a {',
    '    display: flex !important;',
    '    width: 100%;',
    '    padding: 0.75rem 0.5rem;',
    '    color: var(--text-primary, #0F172A) !important;',
    '    font-size: 1rem;',
    '    font-weight: 500;',
    '    border-radius: var(--radius-sm, 6px);',
    '    min-height: 44px;',
    '    align-items: center;',
    '    border-bottom: 1px solid var(--border-subtle, rgba(15, 23, 42, 0.06));',
    '  }',
    '  nav .nav-links > a:last-child { border-bottom: none; }',
    '  nav .nav-links .nav-drop { width: 100%; }',
    '  nav .nav-links .nav-drop-btn {',
    '    width: 100%;',
    '    justify-content: space-between;',
    '    padding: 0.75rem 0.5rem;',
    '    font-size: 1rem;',
    '    color: var(--text-primary, #0F172A);',
    '    border-bottom: 1px solid var(--border-subtle, rgba(15, 23, 42, 0.06));',
    '    min-height: 44px;',
    '  }',
    '  nav .nav-links .nav-drop-panel {',
    '    position: static;',
    '    transform: none !important;',
    '    width: 100% !important;',
    '    box-shadow: none;',
    '    border: none;',
    '    background: var(--bg3, #F8FAFD);',
    '    padding: 0.5rem 0.75rem;',
    '    margin: 0.25rem 0;',
    '    border-radius: var(--radius-md, 8px);',
    '  }',
    '  nav .nav-links .nav-drop-panel::before { display: none; }',
    '  nav .nav-links .nav-mega-grid { grid-template-columns: 1fr; gap: 0.75rem; }',
    '  .nav-backdrop {',
    '    position: fixed;',
    '    inset: 0;',
    '    top: var(--header-height, 64px);',
    '    background: rgba(15, 23, 42, 0.4);',
    '    backdrop-filter: blur(4px);',
    '    z-index: 999;',
    '    display: none;',
    '  }',
    '  .nav-backdrop.open { display: block; }',
    '}',
    '@keyframes slideDown {',
    '  from { opacity: 0; transform: translateY(-8px); }',
    '  to { opacity: 1; transform: translateY(0); }',
    '}'
  ].join('\n');
  document.head.appendChild(css);

  /* ---------- Backdrop Overlay ---------- */
  var backdrop = document.createElement('div');
  backdrop.className = 'nav-backdrop';
  document.body.appendChild(backdrop);

  /* ---------- Hamburger Button ---------- */
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'nav-hamburger';
  btn.id = 'navHamb';
  btn.setAttribute('aria-label', 'Toggle Navigation Menu');
  btn.setAttribute('aria-expanded', 'false');
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>';
  nav.appendChild(btn);

  function setOpen(open) {
    links.classList.toggle('open', open);
    backdrop.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  }

  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    setOpen(!links.classList.contains('open'));
  });

  backdrop.addEventListener('click', function () {
    setOpen(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });

  links.addEventListener('click', function (e) {
    if (e.target.closest('a')) setOpen(false);
  });
})();
