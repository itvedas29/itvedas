// Multi-step requirement wizard. Validation here is a UX affordance only —
// /api/requirements re-validates everything server-side.
(function () {
  var form = document.getElementById('reqForm');
  if (!form) return;

  var steps = Array.prototype.slice.call(form.querySelectorAll('.step'));
  var backBtn = document.getElementById('backBtn');
  var nextBtn = document.getElementById('nextBtn');
  var submitBtn = document.getElementById('submitBtn');
  var progressSegs = document.querySelectorAll('.progress-bar span');
  var stepNumEl = document.getElementById('stepNum');
  var stepNameEl = document.getElementById('stepName');
  var submitError = document.getElementById('submitError');
  var current = 0;

  var MAX_FILES = 3;
  var MAX_BYTES = 5 * 1024 * 1024;
  var ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp',
                       'application/pdf', 'text/plain', 'text/csv'];

  var BUDGET_LABELS = {
    'under-50': 'Under $50', '50-100': '$50 – $100', '100-250': '$100 – $250',
    '250-500': '$250 – $500', '500-1000': '$500 – $1,000',
    '1000-plus': '$1,000+', 'not-sure': 'Not sure yet'
  };

  function show(index) {
    steps.forEach(function (s, i) { s.classList.toggle('active', i === index); });
    current = index;
    backBtn.style.visibility = index === 0 ? 'hidden' : 'visible';
    var last = index === steps.length - 1;
    nextBtn.style.display = last ? 'none' : 'inline-flex';
    submitBtn.style.display = last ? 'inline-flex' : 'none';
    progressSegs.forEach(function (seg, i) { seg.classList.toggle('done', i <= index); });
    stepNumEl.textContent = String(index + 1);
    stepNameEl.textContent = steps[index].dataset.name;
    if (last) renderReview();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    var heading = steps[index].querySelector('h2');
    if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }); }
  }

  function setError(fieldId, on) {
    var field = document.getElementById('field-' + fieldId);
    if (field) field.classList.toggle('has-error', on);
    var standalone = document.getElementById('err-' + fieldId);
    if (standalone && !field) standalone.style.display = on ? 'block' : 'none';
  }

  function validateStep(index) {
    var stepEl = steps[index];
    var stepNo = parseInt(stepEl.dataset.step, 10);

    if (stepNo === 1) {
      var anyChecked = form.querySelectorAll('input[name="categories"]:checked').length > 0;
      setError('categories', !anyChecked);
      return anyChecked;
    }
    if (stepNo === 2) {
      var desc = form.description.value.trim();
      var ok = desc.length >= 20;
      setError('description', !ok);
      return ok;
    }
    if (stepNo === 6) {
      var nameOk = form.name.value.trim().length > 0;
      var emailVal = form.email.value.trim();
      var emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(emailVal) && emailVal.length <= 254;
      setError('name', !nameOk);
      setError('email', !emailOk);
      return nameOk && emailOk;
    }
    if (stepNo === 7) {
      return validateFiles();
    }
    return true;
  }

  function validateFiles() {
    var input = document.getElementById('attachments');
    var errEl = document.getElementById('err-attachments');
    var files = input.files ? Array.prototype.slice.call(input.files) : [];
    var message = '';

    if (files.length > MAX_FILES) {
      message = 'Please attach no more than ' + MAX_FILES + ' files.';
    } else {
      for (var i = 0; i < files.length; i++) {
        if (files[i].size > MAX_BYTES) { message = '"' + files[i].name + '" is larger than 5 MB.'; break; }
        if (ALLOWED_TYPES.indexOf(files[i].type) === -1) {
          message = '"' + files[i].name + '" is not an accepted file type.'; break;
        }
      }
    }
    errEl.textContent = message;
    errEl.style.display = message ? 'block' : 'none';
    return !message;
  }

  function renderFileList() {
    var input = document.getElementById('attachments');
    var list = document.getElementById('fileList');
    list.innerHTML = '';
    var files = input.files ? Array.prototype.slice.call(input.files) : [];
    files.forEach(function (f) {
      var li = document.createElement('li');
      var nameSpan = document.createElement('span');
      nameSpan.textContent = f.name;               // textContent, never innerHTML —
      var sizeSpan = document.createElement('span'); // filenames are user-controlled
      sizeSpan.textContent = (f.size / 1024).toFixed(0) + ' KB';
      li.appendChild(nameSpan);
      li.appendChild(sizeSpan);
      list.appendChild(li);
    });
    validateFiles();
  }

  function renderReview() {
    var box = document.getElementById('reviewBox');
    box.innerHTML = '';

    var cats = Array.prototype.slice.call(form.querySelectorAll('input[name="categories"]:checked'))
      .map(function (c) { return c.nextElementSibling.textContent; });
    var budget = form.querySelector('input[name="budget"]:checked');
    var urgency = form.querySelector('input[name="urgency"]:checked');

    var rows = [
      ['Categories', cats.join(', ') || '—'],
      ['Requirement', form.description.value.trim() || '—'],
      ['Budget', budget ? (BUDGET_LABELS[budget.value] || budget.value) : 'Not specified'],
      ['Urgency', urgency ? urgency.nextElementSibling.textContent : 'Normal'],
      ['Name', form.name.value.trim() || '—'],
      ['Email', form.email.value.trim() || '—'],
      ['Company', form.company.value.trim() || '—']
    ];

    rows.forEach(function (row) {
      var dt = document.createElement('dt');
      dt.textContent = row[0];
      var dd = document.createElement('dd');
      dd.textContent = row[1];   // user input — set as text, never parsed as HTML
      box.appendChild(dt);
      box.appendChild(dd);
    });
  }

  nextBtn.addEventListener('click', function () {
    if (!validateStep(current)) return;
    if (current < steps.length - 1) show(current + 1);
  });

  backBtn.addEventListener('click', function () {
    if (current > 0) show(current - 1);
  });

  document.getElementById('description').addEventListener('input', function () {
    document.getElementById('descCount').textContent = String(this.value.length);
  });

  document.getElementById('attachments').addEventListener('change', renderFileList);

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    // Re-run every step's validation, not just the last — a user can reach
    // step 7 and then go back and clear a required field.
    for (var i = 0; i < steps.length; i++) {
      if (!validateStep(i)) { show(i); return; }
    }

    submitError.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting…';

    var data = new FormData(form);
    data.append('source', document.referrer || window.location.search || 'direct');

    fetch('/api/requirements', { method: 'POST', body: data })
      .then(function (res) {
        return res.json().then(function (body) { return { ok: res.ok, body: body }; });
      })
      .then(function (result) {
        if (!result.ok || !result.body.ok) {
          throw new Error(result.body && result.body.error ? result.body.error : 'Submission failed.');
        }
        document.getElementById('refDisplay').textContent = result.body.reference;
        document.getElementById('formArea').style.display = 'none';
        document.getElementById('successArea').style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
      })
      .catch(function (err) {
        submitError.textContent = err.message || 'Something went wrong. Please try again.';
        submitError.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Requirement';
      });
  });

  // Deep link from a service page: /request-it-help?category=microsoft-365
  var preselect = new URLSearchParams(window.location.search).get('category');
  if (preselect) {
    var box = form.querySelector('input[name="categories"][value="' + CSS.escape(preselect) + '"]');
    if (box) box.checked = true;
  }

  show(0);
})();
