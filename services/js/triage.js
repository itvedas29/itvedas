// Symptom triage widget.
//
// A visitor who doesn't know the name of their problem picks the symptom that
// matches, and gets the likely service, an indicative starting price, and a
// deep link into the requirement form with the category pre-selected.
//
// The mapping is intentionally conservative: it suggests where to start, and
// says so. It never claims to diagnose the actual fault.
(function () {
  var widget = document.getElementById('triage');
  if (!widget) return;

  var SYMPTOMS = [
    {
      id: 'email-missing',
      symptom: "Staff aren't receiving emails",
      service: 'Microsoft 365 or Google Workspace support',
      slug: 'microsoft-365',
      category: 'microsoft-365',
      from: 'from $40',
      why: "Missing mail is usually mail flow, filtering or an authentication (SPF/DKIM/DMARC) problem rather than a broken mailbox. We'd start by checking delivery and your email authentication records.",
      tool: { label: 'Check your DNS records first', href: 'https://itvedas.com/tools/dns-lookup.html' }
    },
    {
      id: 'someone-left',
      symptom: 'An employee left and we need their access removed',
      service: 'Active Directory & identity support',
      slug: 'active-directory',
      category: 'active-directory',
      from: 'from $40',
      why: "Offboarding usually spans more than one system — email, files, devices and any shared logins. We'd work through each and give you a repeatable checklist for next time.",
      tool: null
    },
    {
      id: 'updates',
      symptom: "Laptops aren't getting updates",
      service: 'Patch management',
      slug: 'patch-management',
      category: 'patch-management',
      from: 'from $49',
      why: "Usually either no central patch policy exists, or updates are failing quietly on individual machines. An assessment tells you which, and how many devices are affected.",
      tool: null
    },
    {
      id: 'too-many-devices',
      symptom: 'We have too many devices to manage by hand',
      service: 'Endpoint management',
      slug: 'endpoint-management',
      category: 'endpoint-management',
      from: 'from $49',
      why: "Past roughly 10-15 devices, spreadsheets stop working. We'd assess your fleet and recommend a management platform sized to your budget rather than the biggest one.",
      tool: null
    },
    {
      id: 'security-worry',
      symptom: "We're not sure our setup is secure",
      service: 'Security health check',
      slug: 'cybersecurity',
      category: 'cybersecurity',
      from: 'from $75',
      why: "For most small businesses the two biggest gaps are MFA that isn't enforced everywhere and missing email authentication. A health check tells you where you actually stand.",
      tool: { label: 'Check your security headers', href: 'https://itvedas.com/tools/http-header-analyzer.html' }
    },
    {
      id: 'moving-platform',
      symptom: "We're moving to a new email or device platform",
      service: 'IT migration',
      slug: 'it-migration',
      category: 'it-migration',
      from: 'from $75',
      why: "Migrations go wrong at cutover. We'd plan the move, the verification steps and a rollback path before touching anything live.",
      tool: null
    }
  ];

  var optionsEl = widget.querySelector('.triage-options');
  var resultEl = widget.querySelector('.triage-result');

  function el(tag, opts) {
    var n = document.createElement(tag);
    opts = opts || {};
    if (opts.text !== undefined) n.textContent = opts.text;
    if (opts.className) n.className = opts.className;
    if (opts.attrs) Object.keys(opts.attrs).forEach(function (k) { n.setAttribute(k, opts.attrs[k]); });
    (opts.children || []).forEach(function (c) { n.appendChild(c); });
    return n;
  }

  SYMPTOMS.forEach(function (s) {
    var btn = el('button', {
      className: 'triage-option',
      attrs: { type: 'button', 'aria-controls': 'triageResult' },
      children: [
        el('span', { className: 'q', text: '?', attrs: { 'aria-hidden': 'true' } }),
        el('span', { text: s.symptom })
      ]
    });
    btn.addEventListener('click', function () { render(s); });
    optionsEl.appendChild(btn);
  });

  function render(s) {
    resultEl.innerHTML = '';
    resultEl.hidden = false;

    resultEl.appendChild(el('p', {
      className: 'eyebrow',
      text: 'Most likely a starting point of'
    }));
    resultEl.appendChild(el('h3', { text: s.service }));
    resultEl.appendChild(el('p', {
      text: s.why,
      attrs: { style: 'color:var(--muted);font-size:0.94rem;' }
    }));

    var meta = el('div', { className: 'meta', children: [
      el('span', { className: 'pill', text: 'Indicative ' + s.from }),
      el('span', { className: 'pill', text: 'Scoped before any work starts' })
    ]});
    resultEl.appendChild(meta);

    var actions = el('div', { className: 'triage-actions', children: [
      el('a', {
        className: 'btn btn-primary',
        text: 'Post This Requirement',
        attrs: { href: '/request-it-help?category=' + encodeURIComponent(s.category) }
      }),
      el('a', {
        className: 'btn btn-secondary',
        text: 'Read about this service',
        attrs: { href: '/services/' + s.slug }
      })
    ]});
    if (s.tool) {
      actions.appendChild(el('a', {
        className: 'btn btn-ghost',
        text: s.tool.label,
        attrs: { href: s.tool.href }
      }));
    }
    resultEl.appendChild(actions);

    resultEl.appendChild(el('p', {
      text: "This is a starting point, not a diagnosis — tell us what's actually happening and we'll confirm during review.",
      attrs: { style: 'color:var(--muted);font-size:0.82rem;margin-top:1rem;' }
    }));

    // Move focus to the result so keyboard and screen-reader users land on the
    // content that just appeared rather than staying on the button.
    resultEl.setAttribute('tabindex', '-1');
    resultEl.focus({ preventScroll: true });
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
})();
