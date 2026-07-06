/* ITVedas nav search — injects a search button + results panel into the
   fixed nav on every page except the homepage (which has its own hero search).
   Self-contained: no dependencies, styles injected, index lazy-loaded on open. */
(function () {
  var path = location.pathname;
  if (path === '/' || path === '/index.html') return;
  var nav = document.querySelector('nav');
  if (!nav || document.getElementById('nsWrap')) return;

  /* ---------- styles ---------- */
  var css = [
    '#nsWrap{display:flex;align-items:center;}',
    '#nsBtn{display:flex;align-items:center;gap:0.45rem;background:none;border:1px solid rgba(255,255,255,0.12);border-radius:100px;color:#9C9CBE;font-size:0.8rem;font-family:inherit;padding:0.4rem 0.9rem;cursor:pointer;transition:color .2s,border-color .2s;white-space:nowrap;}',
    '#nsBtn:hover{color:#F0F0F8;border-color:rgba(255,255,255,0.3);}',
    '#nsBtn svg{width:14px;height:14px;stroke:currentColor;flex-shrink:0;}',
    '#nsBtn kbd{font-size:0.65rem;border:1px solid rgba(255,255,255,0.15);border-radius:4px;padding:0 0.3rem;color:inherit;font-family:inherit;}',
    '#nsPanel{position:fixed;left:50%;transform:translateX(-50%);width:min(92vw,560px);z-index:300;display:none;}',
    '#nsPanel.show{display:block;}',
    '#nsPanel input{width:100%;padding:0.9rem 1.1rem 0.9rem 2.8rem;border-radius:14px;background:#13131C;border:1px solid rgba(255,255,255,0.15);color:#F0F0F8;font-size:0.95rem;font-family:inherit;box-shadow:0 16px 48px rgba(0,0,0,0.55);}',
    '#nsPanel input:focus{outline:none;border-color:rgba(255,107,53,0.5);box-shadow:0 0 0 4px rgba(255,107,53,0.12),0 16px 48px rgba(0,0,0,0.55);}',
    '#nsPanel .ns-icon{position:absolute;left:1rem;top:0.95rem;width:16px;height:16px;stroke:#9C9CBE;pointer-events:none;}',
    '#nsResults{margin-top:0.5rem;background:#13131C;border:1px solid rgba(255,255,255,0.12);border-radius:14px;overflow:hidden;max-height:min(55vh,420px);overflow-y:auto;box-shadow:0 16px 48px rgba(0,0,0,0.55);display:none;}',
    '#nsResults.show{display:block;}',
    '.ns-item{display:flex;gap:0.75rem;align-items:flex-start;padding:0.7rem 1rem;text-decoration:none;color:#F0F0F8;border-bottom:1px solid rgba(255,255,255,0.06);transition:background .15s;}',
    '.ns-item:last-child{border-bottom:none;}',
    '.ns-item:hover,.ns-item.active{background:rgba(255,255,255,0.05);}',
    '.ns-item .ns-t{font-size:0.88rem;font-weight:600;line-height:1.35;display:block;}',
    '.ns-item .ns-c{font-size:0.72rem;color:#9C9CBE;display:block;margin-top:0.1rem;}',
    '.ns-empty{padding:1rem;color:#9C9CBE;font-size:0.85rem;text-align:center;}',
    '@media(max-width:640px){#nsBtn span,#nsBtn kbd{display:none;}#nsBtn{padding:0.4rem 0.55rem;border-radius:8px;}}'
  ].join('\n');
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  /* ---------- markup ---------- */
  var svg = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>';
  var wrap = document.createElement('div');
  wrap.id = 'nsWrap';
  wrap.innerHTML = '<button id="nsBtn" type="button" aria-label="Search the site">' + svg + '<span>Search</span><kbd>/</kbd></button>';
  nav.appendChild(wrap);

  var panel = document.createElement('div');
  panel.id = 'nsPanel';
  panel.innerHTML = svg.replace('<svg ', '<svg class="ns-icon" ') +
    '<input type="text" id="nsInput" placeholder="Search 500+ guides… try \'subnetting\' or \'api\'" aria-label="Search guides" autocomplete="off">' +
    '<div id="nsResults"></div>';
  document.body.appendChild(panel);

  /* ---------- index ---------- */
  var ICONS = {Networking:'🌐',Cloud:'☁️',Security:'🔐',DevOps:'⚙️',Databases:'🗄️',Linux:'🐧',Hardware:'🖥️',Compliance:'📋',PowerShell:'🔷',Azure:'☁️',IIS:'🌐','SQL Server':'🗄️',CVE:'🛡️',News:'📰',APIs:'🔌','Microsoft 365':'📧','AI/ML':'🤖',Windows:'🪟',Servers:'🖥️'};
  var INDEX = [
    {title:'Networking — How Networks Talk',topic:'Networking',url:'/articles/networking/',icon:'🌐',kw:'networking tcp ip dns subnetting routing vpn firewall'},
    {title:'Cloud — AWS, Azure & GCP',topic:'Cloud',url:'/articles/cloud/',icon:'☁️',kw:'cloud aws azure gcp serverless s3 ec2 lambda'},
    {title:'Security — Threats & Hardening',topic:'Security',url:'/articles/security/',icon:'🔐',kw:'security cybersecurity hacking malware ransomware encryption'},
    {title:'DevOps — Docker, Kubernetes, CI/CD',topic:'DevOps',url:'/articles/devops/',icon:'⚙️',kw:'devops docker kubernetes jenkins terraform cicd pipeline'},
    {title:'Databases — SQL & NoSQL',topic:'Databases',url:'/articles/databases/',icon:'🗄️',kw:'database sql nosql mysql postgresql mongodb index'},
    {title:'Linux — Own the Terminal',topic:'Linux',url:'/articles/linux/',icon:'🐧',kw:'linux bash terminal ssh systemd cron permissions ubuntu'},
    {title:'Hardware — Silicon to System',topic:'Hardware',url:'/articles/hardware/',icon:'🖥️',kw:'hardware cpu ram ssd hdd gpu nvme raid memory storage laptop'},
    {title:'Compliance — Rules That Protect',topic:'Compliance',url:'/articles/compliance/',icon:'📋',kw:'compliance gdpr hipaa soc 2 pci dss iso 27001'},
    {title:'APIs — How Software Talks',topic:'APIs',url:'/articles/api/',icon:'🔌',kw:'api rest http methods get post put delete json status codes oauth webhooks endpoint'},
    {title:'PowerShell Guides',topic:'PowerShell',url:'/articles/powershell/',icon:'🔷',kw:'powershell scripting cmdlets automation active directory'},
    {title:'Azure Guides',topic:'Azure',url:'/articles/azure/',icon:'☁️',kw:'azure vm entra vnet nsg expressroute'},
    {title:'IIS Server Guides',topic:'IIS',url:'/articles/iis/',icon:'🌐',kw:'iis web server app pool ssl windows'},
    {title:'SQL Server Guides',topic:'SQL Server',url:'/articles/sql-server/',icon:'🗄️',kw:'sql server always on licensing installation'},
    {title:'CVE Database',topic:'Security',url:'/cve/',icon:'🛡️',kw:'cve vulnerability exploit cvss patch'},
    {title:'IT News',topic:'News',url:'/news.html',icon:'📰',kw:'news technology industry updates'},
    {title:'Security News',topic:'News',url:'/security-news.html',icon:'🛡️',kw:'security news breach ransomware alert'},
    {title:'Career Paths',topic:'Career',url:'/career-paths.html',icon:'🎯',kw:'career path job salary role certification'},
    {title:'IT Quiz',topic:'Quiz',url:'/quiz.html',icon:'🧠',kw:'quiz test knowledge score assessment'},
    {title:'Problems & Solutions',topic:'Fixes',url:'/problems-solutions.html',icon:'🔧',kw:'problem solution fix error troubleshoot wifi slow printer'}
  ];
  var loaded = false;
  function loadIndex() {
    if (loaded) return;
    loaded = true;
    fetch('/search-index.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
      if (Array.isArray(data)) {
        var extra = data.map(function (a) {
          return {
            title: a.title, topic: a.topic || 'Guide', url: a.url || ('/articles/' + a.file),
            icon: (ICONS[a.topic] || '📄'), kw: (a.keyword || '') + ' ' + (a.title || '') + ' ' + (a.description || '')
          };
        });
        INDEX = extra.concat(INDEX);
      }
    }).catch(function () {});
  }

  /* ---------- behaviour ---------- */
  var btn = document.getElementById('nsBtn');
  var input = document.getElementById('nsInput');
  var results = document.getElementById('nsResults');
  var activeIdx = -1;

  function openPanel() {
    var r = nav.getBoundingClientRect();
    panel.style.top = (r.bottom + 10) + 'px';
    panel.classList.add('show');
    loadIndex();
    input.focus();
  }
  function closePanel() {
    panel.classList.remove('show');
    results.classList.remove('show');
    input.value = '';
    activeIdx = -1;
  }
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  function run() {
    var q = input.value.trim().toLowerCase();
    activeIdx = -1;
    if (!q) { results.classList.remove('show'); results.innerHTML = ''; return; }
    var seen = {}, hits = [];
    for (var i = 0; i < INDEX.length && hits.length < 8; i++) {
      var it = INDEX[i];
      if (seen[it.url]) continue;
      if (it.title.toLowerCase().indexOf(q) > -1 || it.topic.toLowerCase().indexOf(q) > -1 || (it.kw && it.kw.toLowerCase().indexOf(q) > -1)) {
        seen[it.url] = 1; hits.push(it);
      }
    }
    if (!hits.length) {
      results.innerHTML = '<div class="ns-empty">No results for "' + esc(q) + '" — try another word</div>';
    } else {
      results.innerHTML = hits.map(function (h) {
        return '<a class="ns-item" href="' + h.url + '"><span>' + h.icon + '</span><span><span class="ns-t">' + esc(h.title) + '</span><span class="ns-c">' + esc(h.topic) + '</span></span></a>';
      }).join('');
    }
    results.classList.add('show');
  }

  btn.addEventListener('click', function () {
    panel.classList.contains('show') ? closePanel() : openPanel();
  });
  input.addEventListener('input', run);
  input.addEventListener('keydown', function (e) {
    var items = results.querySelectorAll('.ns-item');
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!items.length) return;
      activeIdx = e.key === 'ArrowDown' ? (activeIdx + 1) % items.length : (activeIdx - 1 + items.length) % items.length;
      for (var i = 0; i < items.length; i++) items[i].classList.toggle('active', i === activeIdx);
      items[activeIdx].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter' && activeIdx > -1 && items[activeIdx]) {
      location.href = items[activeIdx].getAttribute('href');
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== input &&
        !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
      e.preventDefault(); openPanel();
    }
    if (e.key === 'Escape') closePanel();
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#nsPanel') && !e.target.closest('#nsWrap')) closePanel();
  });
})();
