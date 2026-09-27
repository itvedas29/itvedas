/* ITVedas site navigation behaviour (menus, mobile menu, search, current section).
   Markup: partials/site-nav.html. No inline handlers. */
(function () {
  'use strict';

  // GA4 event layer (was loaded by the old nav-mega.js). No-op when gtag is absent.
  if (!document.querySelector('script[src="/js/itvedas-events.js"]')) {
    var ev = document.createElement('script');
    ev.src = '/js/itvedas-events.js';
    ev.async = true;
    document.head.appendChild(ev);
  }

  var SECTIONS = {
    learn: ['/articles/', '/chapters'],
    news: ['/news', '/security-news'],
    software: ['/software/', '/ai-tools'],
    tools: ['/tools/', '/cve-listing', '/cve/', '/cve-detail'],
    careers: ['/career-paths', '/career-navigator', '/quiz'],
    help: ['/problems-solutions', '/faq', '/about', '/services', '/contact', '/author']
  };

  var QUICK = [
    ['Networking', '/articles/networking/', 'How devices connect and share data', 'wifi internet router ip dns vpn'],
    ['Hardware', '/articles/hardware/', 'What is inside a computer', 'cpu ram ssd laptop pc memory'],
    ['Linux', '/articles/linux/', 'The system most servers run on', 'terminal ubuntu bash command'],
    ['Cloud', '/articles/cloud/', 'Renting computers and storage online', 'aws azure google storage'],
    ['Security', '/articles/security/', 'Protecting people and systems', 'password hacking virus malware phishing firewall'],
    ['Compliance', '/articles/compliance/', 'Rules for handling data', 'gdpr hipaa iso privacy'],
    ['APIs', '/articles/api/', 'How apps talk to each other', 'rest json integration'],
    ['DevOps', '/articles/devops/', 'How software is built and released', 'docker kubernetes pipeline'],
    ['Databases', '/articles/databases/', 'Where apps keep their information', 'sql data mysql'],
    ['AI models', '/articles/ai-models/', 'How AI tools work', 'chatgpt ai machine learning llm'],
    ['Software specs', '/software/', 'Requirements, prices and reviews', 'endpoint central manageengine software'],
    ['Free IT tools', '/tools/', 'Calculators and lookups', 'password generator dns whois ip subnet'],
    ['Security flaw lookup', '/cve-listing', 'Search known vulnerabilities', 'cve vulnerability exploit patch'],
    ['Problems and fixes', '/problems-solutions', 'Fixes for common issues', 'slow printer error fix help'],
    ['Career paths', '/career-paths', 'What each IT job involves', 'job career salary certification'],
    ['Latest IT news', '/news', 'What happened this week', 'news update']
  ];

  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }

  ready(function () {
    var header = document.querySelector('.site-header');
    if (!header) return;
    var path = location.pathname.replace(/\.html$/, '').replace(/\/index$/, '/');

    // Skip link target: first <main>, else the element right after the header.
    if (!document.getElementById('main-content')) {
      var target = document.querySelector('main') || header.nextElementSibling;
      if (target) { if (!target.id) target.id = 'main-content'; else header.querySelector('.sn-skip').setAttribute('href', '#' + target.id); }
    }

    // Mark the current section and page.
    Object.keys(SECTIONS).forEach(function (key) {
      if (SECTIONS[key].some(function (p) { return path === p.replace(/\/$/, '') || path.indexOf(p) === 0; })) {
        var li = header.querySelector('.sn-top[data-section="' + key + '"]');
        if (li) li.classList.add('is-current');
      }
    });
    header.querySelectorAll('.sn-item, .sn-start').forEach(function (a) {
      var h = a.getAttribute('href').replace(/\.html$/, '');
      if (h === path || h.replace(/\/$/, '') === path.replace(/\/$/, '')) a.setAttribute('aria-current', 'page');
    });

    var buttons = header.querySelectorAll('.sn-btn');
    var desktop = window.matchMedia('(min-width: 1081px)');

    function closeAll(except) {
      buttons.forEach(function (b) { if (b !== except) b.setAttribute('aria-expanded', 'false'); });
    }

    buttons.forEach(function (btn) {
      var li = btn.parentElement;
      var timer, hoverOpenedAt = 0;
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var open = btn.getAttribute('aria-expanded') === 'true';
        // A mouse click right after hover opened the menu should keep it open, not close it.
        if (open && Date.now() - hoverOpenedAt < 600) return;
        closeAll(btn);
        btn.setAttribute('aria-expanded', String(!open));
        closeSearch();
      });
      // Hover opens on desktop; leaving closes after a short delay so diagonal mouse moves don't snap it shut.
      li.addEventListener('mouseenter', function () {
        if (!desktop.matches) return;
        clearTimeout(timer); closeAll(btn);
        if (btn.getAttribute('aria-expanded') !== 'true') { hoverOpenedAt = Date.now(); btn.setAttribute('aria-expanded', 'true'); }
      });
      li.addEventListener('mouseleave', function () {
        if (!desktop.matches) return;
        timer = setTimeout(function () { btn.setAttribute('aria-expanded', 'false'); }, 180);
      });
    });

    // Mobile menu
    var burger = header.querySelector('.sn-burger');
    burger.addEventListener('click', function () {
      var open = !header.classList.contains('is-open');
      header.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', String(open));
      burger.lastChild.nodeValue = open ? 'Close' : 'Menu';
      document.documentElement.style.overflow = open ? 'hidden' : '';
      if (!open) closeAll();
    });
    desktop.addEventListener && desktop.addEventListener('change', function () {
      header.classList.remove('is-open'); burger.setAttribute('aria-expanded', 'false');
      document.documentElement.style.overflow = ''; closeAll();
    });

    document.addEventListener('click', function (e) {
      if (!header.contains(e.target)) { closeAll(); closeSearch(); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        var openBtn = header.querySelector('.sn-btn[aria-expanded="true"]');
        closeAll(); closeSearch();
        if (header.classList.contains('is-open')) burger.click();
        if (openBtn) openBtn.focus();
      }
      if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test((document.activeElement || {}).tagName || '') && !(document.activeElement || {}).isContentEditable) {
        e.preventDefault(); openSearch();
      }
    });

    // Search
    var searchBtn = header.querySelector('.sn-search-btn');
    var panel = header.querySelector('.sn-search');
    var input = panel.querySelector('input');
    var results = panel.querySelector('.sn-results');
    var index = QUICK.map(function (q) { return { title: q[0], url: q[1], desc: q[2], kw: (q[0] + ' ' + q[2] + ' ' + q[3]).toLowerCase() }; });
    var loaded = false;
    var active = -1;

    function loadIndex() {
      if (loaded) return; loaded = true;
      fetch('/search-index.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
        var pages = d && Array.isArray(d.pages) ? d.pages : (Array.isArray(d) ? d : []);
        pages.forEach(function (p) {
          var title = p.title || p.h1; if (!title || !p.url) return;
          var kw = [title, p.h1, p.description, p.topic, Array.isArray(p.keywords) ? p.keywords.join(' ') : p.keyword].join(' ').toLowerCase();
          index.push({ title: title, url: p.url, desc: p.topic || p.description || '', kw: kw });
        });
        if (input.value) render();
      }).catch(function () { /* quick links still work */ });
    }
    function openSearch() {
      closeAll();
      if (header.classList.contains('is-open')) burger.click();
      panel.hidden = false; searchBtn.setAttribute('aria-expanded', 'true');
      loadIndex(); input.focus();
    }
    function closeSearch() {
      if (panel.hidden) return;
      panel.hidden = true; searchBtn.setAttribute('aria-expanded', 'false');
      input.value = ''; results.textContent = ''; active = -1;
    }
    function render() {
      var q = input.value.trim().toLowerCase();
      results.textContent = ''; active = -1;
      if (!q) return;
      var words = q.split(/\s+/);
      var seen = {};
      var hits = index.filter(function (it) {
        if (seen[it.url]) return false;
        var ok = words.every(function (w) { return it.kw.indexOf(w) !== -1; });
        if (ok) seen[it.url] = true;
        return ok;
      }).slice(0, 8);
      if (!hits.length) {
        var li = document.createElement('li'); li.className = 'sn-empty';
        li.textContent = 'Nothing found for \u201c' + input.value.trim() + '\u201d. Try a simpler word, like \u201cwifi\u201d or \u201cpassword\u201d.';
        results.appendChild(li); return;
      }
      hits.forEach(function (it) {
        var li = document.createElement('li');
        var a = document.createElement('a'); a.href = it.url;
        var t = document.createElement('span'); t.className = 'sn-t'; t.textContent = it.title;
        var d = document.createElement('span'); d.className = 'sn-d'; d.textContent = it.desc;
        a.appendChild(t); if (it.desc) a.appendChild(d); li.appendChild(a); results.appendChild(li);
      });
    }
    searchBtn.addEventListener('click', function (e) { e.stopPropagation(); if (panel.hidden) openSearch(); else closeSearch(); });
    panel.querySelector('.sn-search-close').addEventListener('click', closeSearch);
    input.addEventListener('input', render);
    panel.querySelector('form').addEventListener('submit', function (e) {
      e.preventDefault();
      var links = results.querySelectorAll('a');
      if (links.length) location.href = links[Math.max(active, 0)].href;
    });
    input.addEventListener('keydown', function (e) {
      var links = results.querySelectorAll('a');
      if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && links.length) {
        e.preventDefault();
        active = e.key === 'ArrowDown' ? (active + 1) % links.length : (active - 1 + links.length) % links.length;
        links.forEach(function (l, i) { l.classList.toggle('is-active', i === active); });
        links[active].scrollIntoView({ block: 'nearest' });
      }
    });
  });
})();
