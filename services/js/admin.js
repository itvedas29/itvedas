// Admin dashboard client.
//
// Everything rendered from the API is customer-supplied text, so this file
// builds DOM nodes and assigns textContent rather than interpolating into
// innerHTML — an enquiry containing markup must never become live HTML here.
(function () {
  var loginView = document.getElementById('loginView');
  var dashView = document.getElementById('dashView');
  var listView = document.getElementById('listView');
  var detailView = document.getElementById('detailView');

  var STATUS_LABELS = {
    new: 'New', reviewing: 'Reviewing', contacted: 'Contacted',
    qualified: 'Qualified', quoted: 'Quoted', fiverr_upwork: 'Fiverr/Upwork',
    in_progress: 'In Progress', completed: 'Completed',
    follow_up: 'Follow-up', cancelled: 'Cancelled'
  };
  var STATUS_ORDER = ['new', 'reviewing', 'contacted', 'qualified', 'quoted',
                      'fiverr_upwork', 'in_progress', 'completed', 'follow_up', 'cancelled'];

  var BUDGET_LABELS = {
    'under-50': 'Under $50', '50-100': '$50–$100', '100-250': '$100–$250',
    '250-500': '$250–$500', '500-1000': '$500–$1,000',
    '1000-plus': '$1,000+', 'not-sure': 'Not sure'
  };

  var state = { status: '', q: '' };

  function el(tag, opts) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.text !== undefined) node.textContent = opts.text;
    if (opts.className) node.className = opts.className;
    if (opts.attrs) Object.keys(opts.attrs).forEach(function (k) { node.setAttribute(k, opts.attrs[k]); });
    (opts.children || []).forEach(function (c) { node.appendChild(c); });
    return node;
  }

  function api(path, options) {
    return fetch(path, Object.assign({ credentials: 'same-origin' }, options || {}))
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (body) {
          if (res.status === 401) { showLogin(); throw new Error('Session expired. Please sign in again.'); }
          if (!res.ok || body.ok === false) throw new Error(body.error || 'Request failed.');
          return body;
        });
      });
  }

  function formatDate(iso) {
    if (!iso) return '—';
    var d = new Date(iso.replace(' ', 'T') + (iso.endsWith('Z') ? '' : 'Z'));
    if (isNaN(d)) return iso;
    return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function statusBadge(status) {
    return el('span', { className: 'status status-' + status, text: STATUS_LABELS[status] || status });
  }

  // --- auth ----------------------------------------------------------------

  function showLogin() {
    loginView.classList.remove('hidden');
    loginView.style.display = '';
    dashView.classList.add('hidden');
  }

  function showDash(user) {
    loginView.style.display = 'none';
    dashView.classList.remove('hidden');
    document.getElementById('whoami').textContent = user ? (user.name || user.email) : '';
    loadList();
  }

  document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = document.getElementById('loginBtn');
    var errEl = document.getElementById('loginError');
    errEl.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Signing in…';

    fetch('/api/admin/login', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPassword').value
      })
    })
      .then(function (res) { return res.json().then(function (b) { return { ok: res.ok, body: b }; }); })
      .then(function (r) {
        if (!r.ok || !r.body.ok) throw new Error(r.body.error || 'Sign in failed.');
        document.getElementById('loginPassword').value = '';
        return api('/api/admin/session');
      })
      .then(function (s) { showDash(s.user); })
      .catch(function (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = 'Sign In';
      });
  });

  document.getElementById('logoutBtn').addEventListener('click', function () {
    fetch('/api/admin/logout', { method: 'POST', credentials: 'same-origin' })
      .finally(function () { window.location.reload(); });
  });

  // --- list ----------------------------------------------------------------

  function loadList() {
    listView.classList.remove('hidden');
    detailView.classList.add('hidden');
    var body = document.getElementById('listBody');
    body.innerHTML = '';
    body.appendChild(el('div', { className: 'spinner', text: 'Loading…' }));

    var params = new URLSearchParams();
    if (state.status) params.set('status', state.status);
    if (state.q) params.set('q', state.q);

    api('/api/admin/requirements?' + params.toString())
      .then(function (data) {
        renderStats(data);
        renderTable(data);
      })
      .catch(function (err) {
        body.innerHTML = '';
        body.appendChild(el('div', { className: 'alert alert-error', text: err.message }));
      });
  }

  function renderStats(data) {
    var grid = document.getElementById('statGrid');
    grid.innerHTML = '';

    var all = el('button', {
      className: 'stat' + (state.status === '' ? ' active' : ''),
      children: [
        el('div', { className: 'n', text: String(data.total) }),
        el('div', { className: 'l', text: 'Total enquiries' })
      ]
    });
    all.addEventListener('click', function () { state.status = ''; loadList(); });
    grid.appendChild(all);

    STATUS_ORDER.forEach(function (s) {
      var btn = el('button', {
        className: 'stat' + (state.status === s ? ' active' : ''),
        children: [
          el('div', { className: 'n', text: String(data.counts[s] || 0) }),
          el('div', { className: 'l', text: STATUS_LABELS[s] })
        ]
      });
      btn.addEventListener('click', function () { state.status = s; loadList(); });
      grid.appendChild(btn);
    });
  }

  function renderTable(data) {
    var body = document.getElementById('listBody');
    body.innerHTML = '';
    document.getElementById('listMeta').textContent = data.matching + ' matching';

    if (!data.requirements.length) {
      body.appendChild(el('div', { className: 'empty', text: 'No enquiries match these filters yet.' }));
      return;
    }

    var thead = el('thead', {
      children: [el('tr', {
        children: ['Reference', 'Customer', 'Company', 'Categories', 'Budget', 'Urgency', 'Created', 'Status']
          .map(function (h) { return el('th', { text: h }); })
      })]
    });

    var tbody = el('tbody');
    data.requirements.forEach(function (r) {
      var tr = el('tr', {
        children: [
          el('td', { children: [el('span', { className: 'mono', text: r.reference })] }),
          el('td', {
            children: [
              el('div', { text: r.customer_name || '—' }),
              el('div', { text: r.customer_email || '', attrs: { style: 'color:var(--muted);font-size:0.8rem;' } })
            ]
          }),
          el('td', { text: r.company_name || '—' }),
          el('td', { text: r.categories || '—' }),
          el('td', { text: BUDGET_LABELS[r.budget_range] || '—' }),
          el('td', { text: r.urgency || '—' }),
          el('td', { text: formatDate(r.created_at) }),
          el('td', { children: [statusBadge(r.status)] })
        ]
      });
      tr.addEventListener('click', function () { loadDetail(r.id); });
      tbody.appendChild(tr);
    });

    var wrap = el('div', { className: 'table-scroll', children: [el('table', { children: [thead, tbody] })] });
    body.appendChild(wrap);
  }

  document.getElementById('searchBtn').addEventListener('click', function () {
    state.q = document.getElementById('searchInput').value.trim();
    loadList();
  });
  document.getElementById('searchInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); state.q = this.value.trim(); loadList(); }
  });
  document.getElementById('clearFilterBtn').addEventListener('click', function () {
    state.status = ''; state.q = '';
    document.getElementById('searchInput').value = '';
    loadList();
  });
  document.getElementById('backToList').addEventListener('click', loadList);

  // --- detail --------------------------------------------------------------

  function loadDetail(id) {
    listView.classList.add('hidden');
    detailView.classList.remove('hidden');
    var body = document.getElementById('detailBody');
    body.innerHTML = '';
    body.appendChild(el('div', { className: 'spinner', text: 'Loading…' }));

    api('/api/admin/requirement/' + id)
      .then(function (d) { renderDetail(id, d); })
      .catch(function (err) {
        body.innerHTML = '';
        body.appendChild(el('div', { className: 'alert alert-error', text: err.message }));
      });
  }

  function kvPanel(title, pairs) {
    var dl = el('dl', { className: 'kv' });
    pairs.forEach(function (p) {
      if (p[1] === null || p[1] === undefined || p[1] === '') return;
      dl.appendChild(el('dt', { text: p[0] }));
      dl.appendChild(el('dd', { text: String(p[1]) }));
    });
    if (!dl.children.length) dl.appendChild(el('dd', { text: 'Nothing recorded.' }));
    return el('div', { className: 'panel', children: [el('h3', { text: title }), dl] });
  }

  function renderDetail(id, d) {
    var r = d.requirement;
    var body = document.getElementById('detailBody');
    body.innerHTML = '';

    var header = el('div', {
      attrs: { style: 'display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:1.5rem;' },
      children: [
        el('h1', { attrs: { style: 'font-size:1.4rem;' }, children: [el('span', { className: 'mono', text: r.reference })] }),
        statusBadge(r.status),
        el('span', { attrs: { style: 'color:var(--muted);font-size:0.85rem;' }, text: 'Submitted ' + formatDate(r.created_at) })
      ]
    });
    body.appendChild(header);

    var left = el('div');
    var right = el('div');

    // requirement text
    left.appendChild(el('div', {
      className: 'panel',
      children: [
        el('h3', { text: 'Requirement' }),
        el('div', { className: 'desc-block', text: r.description })
      ]
    }));

    if (r.extra_message) {
      left.appendChild(el('div', {
        className: 'panel',
        children: [el('h3', { text: 'Additional message' }), el('div', { className: 'desc-block', text: r.extra_message })]
      }));
    }

    left.appendChild(kvPanel('Environment', [
      ['Users', r.users_count], ['Devices', r.devices_count],
      ['Windows devices', r.windows_devices], ['Mac devices', r.mac_devices],
      ['Productivity suite', r.productivity_suite],
      ['Endpoint solution', r.endpoint_solution],
      ['Other technology', r.other_technology]
    ]));

    // attachments
    var attachPanel = el('div', { className: 'panel', children: [el('h3', { text: 'Attachments' })] });
    if (!d.attachments.length) {
      attachPanel.appendChild(el('p', { attrs: { style: 'color:var(--muted);font-size:0.88rem;' }, text: 'No attachments.' }));
    } else {
      d.attachments.forEach(function (a) {
        var link = el('a', {
          text: a.filename,
          attrs: { href: '/api/admin/attachment/' + a.id, style: 'color:var(--accent);text-decoration:none;' }
        });
        attachPanel.appendChild(el('div', {
          attrs: { style: 'padding:0.4rem 0;font-size:0.88rem;' },
          children: [link, el('span', { attrs: { style: 'color:var(--muted);margin-left:0.5rem;' }, text: '(' + Math.round((a.size_bytes || 0) / 1024) + ' KB)' })]
        }));
      });
    }
    left.appendChild(attachPanel);

    // notes
    var notesPanel = el('div', { className: 'panel', children: [el('h3', { text: 'Internal notes' })] });
    var noteInput = el('textarea', { attrs: { rows: '3', placeholder: 'Add an internal note…', style: 'min-height:80px;margin-bottom:0.6rem;' } });
    var noteBtn = el('button', { className: 'btn btn-secondary btn-sm', text: 'Add note' });
    noteBtn.addEventListener('click', function () {
      var text = noteInput.value.trim();
      if (!text) return;
      noteBtn.disabled = true;
      api('/api/admin/requirement/' + id, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'add_note', body: text })
      }).then(function () { loadDetail(id); })
        .catch(function (err) { alert(err.message); noteBtn.disabled = false; });
    });
    notesPanel.appendChild(noteInput);
    notesPanel.appendChild(noteBtn);
    d.notes.forEach(function (n) {
      notesPanel.appendChild(el('div', {
        className: 'note',
        attrs: { style: 'margin-top:0.75rem;' },
        children: [
          el('div', { text: n.body, attrs: { style: 'white-space:pre-wrap;' } }),
          el('div', { className: 'meta', text: (n.author || 'admin') + ' · ' + formatDate(n.created_at) })
        ]
      }));
    });
    left.appendChild(notesPanel);

    // --- right column ---

    right.appendChild(kvPanel('Customer', [
      ['Name', r.customer_name], ['Email', r.customer_email],
      ['Phone', r.customer_phone], ['Country', r.customer_country || r.ip_country],
      ['Prefers', r.preferred_contact], ['Company', r.company_name]
    ]));

    right.appendChild(kvPanel('Request', [
      ['Categories', d.categories.join(', ')],
      ['Budget', BUDGET_LABELS[r.budget_range] || r.budget_range],
      ['Urgency', r.urgency],
      ['Source', r.source]
    ]));

    // status control
    var statusSelect = el('select');
    STATUS_ORDER.forEach(function (s) {
      var opt = el('option', { text: STATUS_LABELS[s], attrs: { value: s } });
      if (s === r.status) opt.selected = true;
      statusSelect.appendChild(opt);
    });
    var statusBtn = el('button', { className: 'btn btn-primary btn-sm', text: 'Update' });
    statusBtn.addEventListener('click', function () {
      statusBtn.disabled = true;
      api('/api/admin/requirement/' + id, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'set_status', status: statusSelect.value })
      }).then(function () { loadDetail(id); })
        .catch(function (err) { alert(err.message); statusBtn.disabled = false; });
    });
    right.appendChild(el('div', {
      className: 'panel',
      children: [
        el('h3', { text: 'Status' }),
        el('div', { className: 'inline-form', children: [statusSelect, statusBtn] })
      ]
    }));

    // project (Fiverr/Upwork)
    var p = d.project || {};
    var platformSel = el('select');
    [['', '— none —'], ['fiverr', 'Fiverr'], ['upwork', 'Upwork'], ['other', 'Other']].forEach(function (o) {
      var opt = el('option', { text: o[1], attrs: { value: o[0] } });
      if (o[0] === (p.platform || '')) opt.selected = true;
      platformSel.appendChild(opt);
    });
    var urlInput = el('input', { attrs: { type: 'url', placeholder: 'https://www.upwork.com/…' } });
    urlInput.value = p.project_url || '';
    var refInput = el('input', { attrs: { type: 'text', placeholder: 'Project ID / reference' } });
    refInput.value = p.project_ref || '';
    var priceInput = el('input', { attrs: { type: 'number', min: '0', step: '0.01', placeholder: 'Agreed price (USD)' } });
    priceInput.value = p.agreed_price_usd != null ? p.agreed_price_usd : '';
    var startedInput = el('input', { attrs: { type: 'date' } });
    startedInput.value = p.started_at ? String(p.started_at).slice(0, 10) : '';
    var projNotes = el('textarea', { attrs: { rows: '2', placeholder: 'Project notes', style: 'min-height:70px;' } });
    projNotes.value = p.notes || '';

    var projBtn = el('button', { className: 'btn btn-secondary btn-sm', text: 'Save project details' });
    projBtn.addEventListener('click', function () {
      projBtn.disabled = true;
      api('/api/admin/requirement/' + id, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'set_project',
          platform: platformSel.value,
          project_url: urlInput.value.trim(),
          project_ref: refInput.value.trim(),
          agreed_price_usd: priceInput.value,
          started_at: startedInput.value,
          notes: projNotes.value.trim()
        })
      }).then(function () { loadDetail(id); })
        .catch(function (err) { alert(err.message); projBtn.disabled = false; });
    });

    function labelled(labelText, control) {
      return el('div', { attrs: { style: 'margin-bottom:0.75rem;' }, children: [el('label', { text: labelText }), control] });
    }

    var projectPanel = el('div', {
      className: 'panel',
      children: [
        el('h3', { text: 'Fiverr / Upwork project' }),
        labelled('Platform', platformSel),
        labelled('Project URL', urlInput),
        labelled('Project reference', refInput),
        labelled('Agreed price (USD)', priceInput),
        labelled('Started on', startedInput),
        labelled('Notes', projNotes),
        projBtn
      ]
    });
    if (p.project_url) {
      projectPanel.insertBefore(el('p', {
        attrs: { style: 'margin-bottom:0.75rem;font-size:0.85rem;' },
        children: [el('a', { text: 'Open project ↗', attrs: { href: p.project_url, target: '_blank', rel: 'noopener noreferrer', style: 'color:var(--accent);' } })]
      }), projectPanel.children[1]);
    }
    right.appendChild(projectPanel);

    // quotes
    var quoteAmount = el('input', { attrs: { type: 'number', min: '0', step: '0.01', placeholder: 'Amount (USD)' } });
    var quoteScope = el('textarea', { attrs: { rows: '2', placeholder: 'Scope summary', style: 'min-height:70px;' } });
    var quoteBtn = el('button', { className: 'btn btn-secondary btn-sm', text: 'Record quote' });
    quoteBtn.addEventListener('click', function () {
      quoteBtn.disabled = true;
      api('/api/admin/requirement/' + id, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'add_quote', amount_usd: quoteAmount.value, scope: quoteScope.value.trim() })
      }).then(function () { loadDetail(id); })
        .catch(function (err) { alert(err.message); quoteBtn.disabled = false; });
    });
    var quotePanel = el('div', {
      className: 'panel',
      children: [el('h3', { text: 'Quotes' }), labelled('Amount', quoteAmount), labelled('Scope', quoteScope), quoteBtn]
    });
    d.quotes.forEach(function (q) {
      quotePanel.appendChild(el('div', {
        className: 'note',
        attrs: { style: 'margin-top:0.75rem;' },
        children: [
          el('div', { text: (q.amount_usd != null ? '$' + q.amount_usd : 'No amount') + (q.scope ? ' — ' + q.scope : '') }),
          el('div', { className: 'meta', text: formatDate(q.created_at) })
        ]
      }));
    });
    right.appendChild(quotePanel);

    // history + emails
    var histList = el('ul', { className: 'timeline' });
    d.history.forEach(function (h) {
      histList.appendChild(el('li', {
        text: (h.from_status ? (STATUS_LABELS[h.from_status] || h.from_status) + ' → ' : '') +
              (STATUS_LABELS[h.to_status] || h.to_status) + ' · ' + formatDate(h.created_at)
      }));
    });
    right.appendChild(el('div', { className: 'panel', children: [el('h3', { text: 'Status history' }), histList] }));

    if (d.emails.length) {
      var emailList = el('ul', { className: 'timeline' });
      d.emails.forEach(function (e) {
        emailList.appendChild(el('li', {
          text: e.template + ' → ' + e.recipient + ' · ' + e.status + (e.error ? ' (' + e.error + ')' : '') + ' · ' + formatDate(e.created_at)
        }));
      });
      right.appendChild(el('div', { className: 'panel', children: [el('h3', { text: 'Email log' }), emailList] }));
    }

    body.appendChild(el('div', { className: 'detail-grid', children: [left, right] }));
    window.scrollTo({ top: 0 });
  }

  // --- boot ----------------------------------------------------------------

  fetch('/api/admin/session', { credentials: 'same-origin' })
    .then(function (res) { return res.json().then(function (b) { return { ok: res.ok, body: b }; }); })
    .then(function (r) {
      if (r.ok && r.body.authenticated) showDash(r.body.user);
      else showLogin();
    })
    .catch(showLogin);
})();
