// Moderation screen for /api/reviews-admin. The token is kept in sessionStorage
// for this tab only and sent as a Bearer header.
(function () {
  'use strict';
  var form = document.getElementById('admin-form');
  var tokenEl = document.getElementById('token');
  var productEl = document.getElementById('product');
  var statusEl = document.getElementById('status');
  var list = document.getElementById('admin-list');
  var msg = document.getElementById('admin-msg');

  try { tokenEl.value = sessionStorage.getItem('rv-admin-token') || ''; } catch (e) { /* ignore */ }

  function say(t, bad) { msg.textContent = t; msg.className = 'rv-status ' + (bad ? 'is-error' : 'is-ok'); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function call(method, url, body) {
    return fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tokenEl.value },
      body: body ? JSON.stringify(body) : undefined
    }).then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || 'Request failed'); return d; }); });
  }

  function load() {
    try { sessionStorage.setItem('rv-admin-token', tokenEl.value); } catch (e) { /* ignore */ }
    list.textContent = '';
    say('Loading…');
    call('GET', '/api/reviews-admin?status=' + statusEl.value + '&product=' + encodeURIComponent(productEl.value))
      .then(function (d) {
        say(d.reviews.length ? d.reviews.length + ' reviews' : (d.status === 'pending' ? 'Nothing waiting for approval.' : 'No published reviews yet.'));
        d.reviews.forEach(function (r) { list.appendChild(item(r, d.status)); });
      })
      .catch(function (e) { say(e.message, true); });
  }

  function item(r, status) {
    var li = el('li', 'rv-item');
    var meta = el('div', 'rv-meta');
    meta.appendChild(el('b', null, r.name));
    if (r.role) meta.appendChild(el('span', null, r.role));
    meta.appendChild(el('time', null, new Date(r.createdAt).toLocaleString()));
    li.appendChild(meta);
    li.appendChild(el('div', r.topic === 'software' ? 'rv-stars' : 'rv-tag', r.topic === 'software' ? ('★★★★★'.slice(0, r.rating) + '☆☆☆☆☆'.slice(0, 5 - r.rating)) : 'Spec sheet feedback'));
    r.text.split(/\n{2,}/).forEach(function (p) { li.appendChild(el('p', null, p)); });
    var actions = el('div', 'admin-actions');
    if (status === 'pending') actions.appendChild(button('Approve', 'approve', r, li));
    actions.appendChild(button('Delete', 'delete', r, li));
    li.appendChild(actions);
    return li;
  }

  function button(label, action, r, li) {
    var b = el('button', action === 'delete' ? 'btn btn-ghost' : 'btn', label);
    b.type = 'button';
    b.addEventListener('click', function () {
      if (action === 'delete' && !window.confirm('Delete this review permanently?')) return;
      b.disabled = true;
      call('POST', '/api/reviews-admin', { action: action, product: productEl.value, id: r.id })
        .then(function () { li.remove(); say(action === 'approve' ? 'Published.' : 'Deleted.'); })
        .catch(function (e) { b.disabled = false; say(e.message, true); });
    });
    return b;
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); load(); });
  statusEl.addEventListener('change', function () { if (tokenEl.value) load(); });
})();
