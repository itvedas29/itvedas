// ITVedas user reviews: summary on spec sheets, list + form on review pages.
// All user text is inserted with textContent, never innerHTML.
(function () {
  'use strict';

  var API = '/api/reviews';

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function stars(n) { return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n); }
  function fmtDate(iso) {
    try { return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); }
    catch (e) { return ''; }
  }
  function q(root, name) { return root.querySelector('[data-rv="' + name + '"]'); }

  function load(product) {
    return fetch(API + '?product=' + encodeURIComponent(product), { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); });
  }

  function paintScore(root, data) {
    var avg = q(root, 'average'), st = q(root, 'stars'), count = q(root, 'count');
    if (data.average == null) {
      avg.textContent = '–';
      st.textContent = '';
      count.textContent = data.total ? data.total + ' spec sheet comments, no ratings yet' : 'No reviews yet';
      return;
    }
    avg.textContent = data.average.toFixed(1);
    st.textContent = stars(Math.round(data.average));
    count.textContent = 'from ' + data.rated + (data.rated === 1 ? ' rating' : ' ratings');
  }

  function reviewItem(r) {
    var li = el('li', 'rv-item');
    li.setAttribute('data-topic', r.topic);
    var head = el('div', 'rv-meta');
    head.appendChild(el('b', null, r.name));
    if (r.role) head.appendChild(el('span', null, r.role));
    head.appendChild(el('time', null, fmtDate(r.createdAt)));
    head.lastChild.setAttribute('datetime', r.createdAt);
    li.appendChild(head);
    if (r.topic === 'software' && r.rating) {
      var s = el('div', 'rv-stars', stars(r.rating));
      s.setAttribute('aria-label', r.rating + ' out of 5 stars');
      s.setAttribute('role', 'img');
      li.appendChild(s);
    } else {
      li.appendChild(el('div', 'rv-tag', 'Spec sheet feedback'));
    }
    r.text.split(/\n{2,}/).forEach(function (para) { li.appendChild(el('p', null, para)); });
    return li;
  }

  // Spec sheet: compact summary with the latest review.
  function initSummary() {
    var root = document.querySelector('[data-reviews-summary]');
    if (!root) return;
    load(root.getAttribute('data-reviews-summary')).then(function (data) {
      paintScore(root, data);
      var latest = q(root, 'latest');
      var first = data.reviews.filter(function (r) { return r.topic === 'software'; })[0];
      if (first) {
        var list = el('ol', 'rv-list');
        list.appendChild(reviewItem(first));
        latest.appendChild(list);
      } else {
        latest.appendChild(el('p', 'empty', 'Run Endpoint Central? Tell other admins how it went.'));
      }
    }).catch(function () {
      q(root, 'count').textContent = 'Reviews could not be loaded. Refresh the page to try again.';
    });
    root.querySelectorAll('[data-topic-link]').forEach(function (a) {
      a.addEventListener('click', function () {
        try { sessionStorage.setItem('rv-topic', a.getAttribute('data-topic-link')); } catch (e) { /* ignore */ }
      });
    });
  }

  // Review page: rating bars, filterable list, and the form.
  function initPage() {
    var root = document.querySelector('[data-reviews-page]');
    if (!root) return;
    var product = root.getAttribute('data-reviews-page');
    var list = q(root, 'list'), empty = q(root, 'empty');
    var filter = 'all';
    var all = [];

    function render() {
      list.textContent = '';
      var shown = all.filter(function (r) { return filter === 'all' || r.topic === filter; });
      shown.forEach(function (r) { list.appendChild(reviewItem(r)); });
      empty.hidden = shown.length !== 0;
      empty.textContent = all.length ? 'Nothing in this view yet.' : 'No reviews yet. Yours could be the first.';
    }

    load(product).then(function (data) {
      all = data.reviews;
      paintScore(root, data);
      var bars = q(root, 'bars');
      data.counts.forEach(function (c) {
        var row = el('div', 'rv-bar');
        row.appendChild(el('span', null, c.stars + ' ★'));
        var track = el('div', 'rv-track');
        track.setAttribute('role', 'img');
        track.setAttribute('aria-label', c.count + ' reviews with ' + c.stars + ' stars');
        var fill = el('div', 'rv-fill');
        fill.style.width = (data.rated ? Math.round((c.count / data.rated) * 100) : 0) + '%';
        track.appendChild(fill);
        row.appendChild(track);
        row.appendChild(el('span', 'count', String(c.count)));
        bars.appendChild(row);
      });
      render();
    }).catch(function () {
      q(root, 'count').textContent = 'Reviews could not be loaded. Refresh the page to try again.';
      render();
    });

    root.querySelectorAll('[data-filter]').forEach(function (b) {
      b.addEventListener('click', function () {
        filter = b.getAttribute('data-filter');
        root.querySelectorAll('[data-filter]').forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
        render();
      });
    });

    initForm(root, product);
  }

  function initForm(root, product) {
    var form = q(root, 'form');
    if (!form) return;
    var status = q(root, 'status');
    var ratingField = q(root, 'rating-field');
    var textLabel = q(root, 'text-label');
    var text = form.elements.text;
    var counter = document.getElementById('rv-count');

    function syncTopic() {
      var topic = form.elements.topic.value;
      if (status.classList.contains('is-error')) { status.textContent = ''; status.className = 'rv-status'; }
      ratingField.hidden = topic !== 'software';
      textLabel.textContent = topic === 'software' ? 'Your review' : 'What should we fix or add?';
      text.placeholder = topic === 'software'
        ? 'What do you use it for, what works well, and what gets in the way?'
        : 'Which row is wrong or missing, and where did you see the correct figure?';
    }
    try {
      var pre = sessionStorage.getItem('rv-topic');
      if (pre === 'specs') { form.elements.topic.value = 'specs'; sessionStorage.removeItem('rv-topic'); }
    } catch (e) { /* ignore */ }
    form.querySelectorAll('input[name="topic"]').forEach(function (r) { r.addEventListener('change', syncTopic); });
    syncTopic();

    text.addEventListener('input', function () {
      var n = text.value.trim().length;
      counter.textContent = n < 20 ? (20 - n) + ' more characters needed.' : n.toLocaleString('en-US') + ' of 1,500 characters.';
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var topic = form.elements.topic.value;
      var rating = form.querySelector('input[name="rating"]:checked');
      var payload = {
        product: product,
        topic: topic,
        rating: topic === 'software' && rating ? Number(rating.value) : null,
        name: form.elements.name.value,
        role: form.elements.role.value,
        text: text.value,
        website: form.elements.website.value
      };
      if (topic === 'software' && !payload.rating) { return say('Choose a rating from 1 to 5 stars.', true); }
      if (payload.name.trim().length < 2) { form.elements.name.focus(); return say('Enter a name of at least 2 characters.', true); }
      if (payload.text.trim().length < 20) { text.focus(); return say('Write at least 20 characters so others can learn from it.', true); }

      var btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.textContent = 'Sending…';
      fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error(res.d.error || 'Your review was not sent. Try again in a moment.');
          form.reset();
          syncTopic();
          counter.textContent = 'At least 20 characters. 1,500 maximum.';
          say('Review sent. It will appear here once our team has checked it.', false);
        })
        .catch(function (err) { say(err.message || 'Your review was not sent. Check your connection and try again.', true); })
        .then(function () { btn.disabled = false; btn.textContent = 'Send review'; });
    });

    function say(msg, isError) {
      status.textContent = msg;
      status.className = 'rv-status ' + (isError ? 'is-error' : 'is-ok');
    }
  }

  document.addEventListener('DOMContentLoaded', function () { initSummary(); initPage(); });
})();
