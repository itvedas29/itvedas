// ITVedas software spec database: behaviour shared by /software/ pages.
// No inline handlers (the site's tests forbid onclick attributes).
(function () {
  'use strict';

  // Highlight the tab for the section currently on screen.
  function initTabs() {
    var tabs = document.querySelectorAll('.tabs a[href^="#"]');
    if (!tabs.length || !('IntersectionObserver' in window)) return;
    var byId = {};
    tabs.forEach(function (t) { byId[t.getAttribute('href').slice(1)] = t; });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        tabs.forEach(function (t) { t.removeAttribute('aria-current'); });
        var tab = byId[e.target.id];
        if (tab) tab.setAttribute('aria-current', 'true');
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) observer.observe(el);
    });
  }

  // Server sizing: reads tiers from <script type="application/json" id="sizing-data">.
  function initSizer() {
    var dataEl = document.getElementById('sizing-data');
    var range = document.getElementById('fleet');
    if (!dataEl || !range) return;
    var data;
    try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }
    var tiers = data.tiers;
    var stops = data.stops; // slider positions -> endpoint counts
    var out = {
      count: document.getElementById('fleet-count'),
      tier: document.getElementById('fleet-tier'),
      cpu: document.getElementById('b-cpu'),
      cpuVm: document.getElementById('b-cpu-vm'),
      ram: document.getElementById('b-ram'),
      disk: document.getElementById('b-disk'),
      sql: document.getElementById('b-sql'),
      sqlNote: document.getElementById('b-sql-note'),
      advice: document.getElementById('fleet-advice')
    };
    var fmt = function (n) { return n.toLocaleString('en-US'); };

    function render() {
      var n = stops[Number(range.value)];
      var over = n > tiers[tiers.length - 1].max;
      var tier = tiers[tiers.length - 1];
      for (var i = 0; i < tiers.length; i++) { if (n <= tiers[i].max) { tier = tiers[i]; break; } }

      out.count.firstChild.nodeValue = over ? fmt(tiers[tiers.length - 1].max) + '+' : fmt(n);
      range.setAttribute('aria-valuetext', (over ? 'More than ' + fmt(tiers[tiers.length - 1].max) : fmt(n)) + ' computers');

      if (over) {
        out.tier.textContent = 'Above the single-server limit';
        out.cpu.textContent = 'Custom design';
        out.cpuVm.textContent = 'ManageEngine plans the setup with you';
        out.ram.textContent = 'Custom';
        out.disk.textContent = 'Custom';
        out.sql.textContent = 'Custom';
        out.sqlNote.textContent = 'Separate SQL Server machine';
        out.advice.innerHTML = '';
        var s = document.createElement('span');
        s.textContent = 'One server tops out at 35,000 computers. Beyond that, ManageEngine designs a multi-server setup (a summary server with probe servers of 25,000 to 30,000 endpoints each).';
        out.advice.appendChild(s);
        return;
      }

      out.tier.textContent = 'Tier: ' + fmt(tier.min) + ' to ' + fmt(tier.max) + ' computers';
      out.cpu.textContent = tier.cpu;
      out.cpuVm.textContent = 'or ' + tier.vcpu + ' on a virtual machine';
      out.ram.textContent = tier.ram;
      out.disk.textContent = tier.disk;
      out.sql.textContent = tier.sqlDisk;
      out.sqlNote.textContent = tier.sqlRam + ' RAM if SQL Server is on its own machine';

      var tips = [];
      var ds = Math.ceil(n / 1000);
      if (n > 1000) tips.push('Plan about ' + fmt(ds) + ' distribution servers (one per 1,000 computers) for remote sites.');
      if (n >= 5000) tips.push('Run the server on Windows Server.');
      if (n > 10000) tips.push('Put SQL Server on a separate machine and use enterprise-grade drives or SSDs.');
      if (!tips.length) tips.push('One server covers this fleet. Add a distribution server for any remote office.');
      out.advice.textContent = tips.join(' ');
    }

    range.addEventListener('input', render);
    render();
  }

  // Hub page: filter the catalogue by text and category.
  function initFinder() {
    var input = document.getElementById('finder');
    var list = document.getElementById('catalogue');
    if (!input || !list) return;
    var chips = document.querySelectorAll('.chips button[data-cat]');
    var empty = document.getElementById('catalogue-empty');
    var active = 'all';

    function apply() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      list.querySelectorAll('li[data-cat]').forEach(function (li) {
        var okCat = active === 'all' || li.getAttribute('data-cat') === active;
        var okText = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
        li.hidden = !(okCat && okText);
        if (!li.hidden) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
    }

    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        active = c.getAttribute('data-cat');
        chips.forEach(function (o) { o.setAttribute('aria-pressed', String(o === c)); });
        apply();
      });
    });
    input.addEventListener('input', apply);
    var form = input.closest('form');
    if (form) form.addEventListener('submit', function (e) { e.preventDefault(); apply(); });
  }

  // Sidebar search on product pages sends people to the hub with their query.
  function initSideSearch() {
    var params = new URLSearchParams(window.location.search);
    var q = params.get('q');
    var input = document.getElementById('finder');
    if (q && input) { input.value = q; input.dispatchEvent(new Event('input')); }
    var cat = params.get('cat');
    if (cat) {
      var chip = document.querySelector('.chips button[data-cat="' + cat.replace(/[^a-z]/g, '') + '"]');
      if (chip) chip.click();
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTabs();
    initSizer();
    initFinder();
    initSideSearch();
  });
})();
