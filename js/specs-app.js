/**
 * ITVedas — Enterprise Software Spec Database Application Logic
 * High-Density GSMArena-style Technical Explorer
 */

// Software catalog dataset for client-side search, filtering, and diffing
const SOFTWARE_CATALOG = [
  {
    id: "manageengine-endpoint-central",
    name: "ManageEngine Endpoint Central",
    vendor: "Zoho Corporation",
    category: "Unified Endpoint Management (UEM)",
    category_id: "uem",
    deployment: ["Cloud SaaS", "On-Premise", "Air-Gapped"],
    auth: ["Active Directory", "Microsoft Entra ID", "SAML 2.0", "OpenLDAP"],
    free_tier: true,
    free_tier_nodes: 25,
    max_nodes: 25000,
    min_ram: "8 GB",
    score: 9.4,
    tags: ["UEM", "Patch Management", "Software Deployment", "WebRTC Remote", "Bare-Metal OS Imaging"]
  },
  {
    id: "microsoft-intune",
    name: "Microsoft Intune",
    vendor: "Microsoft Corporation",
    category: "Unified Endpoint Management (UEM)",
    category_id: "uem",
    deployment: ["Cloud SaaS"],
    auth: ["Microsoft Entra ID", "SAML 2.0"],
    free_tier: false,
    free_tier_nodes: 0,
    max_nodes: 500000,
    min_ram: "N/A (Cloud)",
    score: 9.1,
    tags: ["Cloud UEM", "MDM", "Conditional Access", "Autopilot", "Microsoft 365"]
  },
  {
    id: "ninjaone",
    name: "NinjaOne",
    vendor: "NinjaOne LLC",
    category: "Remote Monitoring & Management (RMM)",
    category_id: "rmm",
    deployment: ["Cloud SaaS"],
    auth: ["Active Directory", "Microsoft Entra ID", "SAML 2.0"],
    free_tier: false,
    free_tier_nodes: 0,
    max_nodes: 50000,
    min_ram: "N/A (Cloud)",
    score: 9.2,
    tags: ["RMM", "UEM", "SNMP Monitoring", "Patching", "MSP Multi-Tenant"]
  },
  {
    id: "ivanti-neurons",
    name: "Ivanti Neurons for UEM",
    vendor: "Ivanti, Inc.",
    category: "Unified Endpoint Management (UEM)",
    category_id: "uem",
    deployment: ["Cloud SaaS", "On-Premise", "Air-Gapped"],
    auth: ["Active Directory", "Microsoft Entra ID", "OpenLDAP", "SAML 2.0"],
    free_tier: false,
    free_tier_nodes: 0,
    max_nodes: 100000,
    min_ram: "16 GB",
    score: 8.8,
    tags: ["UEM", "Self-Healing AI", "Rugged Android/Zebra", "EPM", "Enterprise"]
  },
  {
    id: "manageengine-servicedesk-plus",
    name: "ManageEngine ServiceDesk Plus",
    vendor: "Zoho Corporation",
    category: "IT Service Management (ITSM)",
    category_id: "itsm",
    deployment: ["Cloud SaaS", "On-Premise"],
    auth: ["Active Directory", "Microsoft Entra ID", "SAML 2.0"],
    free_tier: true,
    free_tier_nodes: 5,
    max_nodes: 50000,
    min_ram: "8 GB",
    score: 9.3,
    tags: ["ITSM", "CMDB", "Incident Management", "Asset Lifecycle", "Service Catalog"]
  },
  {
    id: "servicenow-itsm",
    name: "ServiceNow IT Service Management",
    vendor: "ServiceNow, Inc.",
    category: "IT Service Management (ITSM)",
    category_id: "itsm",
    deployment: ["Cloud SaaS"],
    auth: ["Microsoft Entra ID", "SAML 2.0", "Active Directory"],
    free_tier: false,
    free_tier_nodes: 0,
    max_nodes: 500000,
    min_ram: "N/A (Cloud)",
    score: 9.5,
    tags: ["ITSM", "Enterprise CMDB", "AI Workflows", "Change Management", "Fortune 500"]
  }
];

// State
let compareQueue = ['manageengine-endpoint-central'];
let searchActiveIndex = -1;

document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  initParametricFilters();
  initKeyShortcuts();
  renderCompareDrawer();
});

// ============================================================================
// 1. GLOBAL AUTOCOMPLETE SEARCH
// ============================================================================
function initSearch() {
  const searchInput = document.getElementById('globalSearchInput');
  const dropdown = document.getElementById('searchResultsDropdown');
  const resultsList = document.getElementById('searchResultsList');

  if (!searchInput || !dropdown || !resultsList) return;

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim().toLowerCase();
    searchActiveIndex = -1;

    if (!query) {
      dropdown.classList.add('hidden');
      return;
    }

    const matches = SOFTWARE_CATALOG.filter(item => {
      return item.name.toLowerCase().includes(query) ||
             item.vendor.toLowerCase().includes(query) ||
             item.category.toLowerCase().includes(query) ||
             item.tags.some(t => t.toLowerCase().includes(query));
    });

    if (matches.length === 0) {
      resultsList.innerHTML = `
        <div class="p-4 text-center text-xs text-slate-400">
          No direct matches found for "<span class="text-brand-orange font-mono">${escapeHtml(query)}</span>".<br>
          <button onclick="openModal('suggestModal')" class="mt-2 text-cyan-400 hover:underline font-semibold">Suggest this software for addition →</button>
        </div>
      `;
      dropdown.classList.remove('hidden');
      return;
    }

    resultsList.innerHTML = matches.map((item, idx) => `
      <div 
        class="search-result-item p-3 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition-colors ${idx === 0 ? 'bg-slate-800/40' : ''}"
        data-index="${idx}"
        onclick="selectSoftware('${item.id}')"
      >
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-slate-800 border border-slate-700 flex items-center justify-center font-display font-bold text-xs text-slate-200">
            ${item.name.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div class="font-display font-semibold text-xs text-slate-100 flex items-center gap-2">
              <span>${item.name}</span>
              ${item.free_tier ? '<span class="px-1.5 py-0.2 rounded text-[9px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">Free Tier</span>' : ''}
            </div>
            <div class="text-[11px] text-slate-400 font-mono">
              ${item.vendor} • <span class="text-cyan-400">${item.category}</span>
            </div>
          </div>
        </div>
        <div class="text-right font-mono text-[11px] text-slate-400">
          <div class="text-emerald-400 font-bold">★ ${item.score}</div>
          <div class="text-[10px] text-slate-500">${item.deployment.join(' / ')}</div>
        </div>
      </div>
    `).join('');

    dropdown.classList.remove('hidden');
  });

  // Handle keyboard navigation inside search input
  searchInput.addEventListener('keydown', (e) => {
    const items = resultsList.querySelectorAll('.search-result-item');
    if (items.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      searchActiveIndex = (searchActiveIndex + 1) % items.length;
      updateSearchSelection(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      searchActiveIndex = (searchActiveIndex - 1 + items.length) % items.length;
      updateSearchSelection(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (searchActiveIndex >= 0 && searchActiveIndex < items.length) {
        items[searchActiveIndex].click();
      } else if (items.length > 0) {
        items[0].click();
      }
    } else if (e.key === 'Escape') {
      dropdown.classList.add('hidden');
    }
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.add('hidden');
    }
  });
}

function updateSearchSelection(items) {
  items.forEach((item, idx) => {
    if (idx === searchActiveIndex) {
      item.classList.add('bg-slate-800', 'border-l-2', 'border-brand-orange');
      item.scrollIntoView({ block: 'nearest' });
    } else {
      item.classList.remove('bg-slate-800', 'border-l-2', 'border-brand-orange');
    }
  });
}

function selectSoftware(softwareId) {
  const dropdown = document.getElementById('searchResultsDropdown');
  if (dropdown) dropdown.classList.add('hidden');

  if (softwareId === 'manageengine-endpoint-central') {
    switchTab('specsTab');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    showToast('Loaded ManageEngine Endpoint Central specs.', true);
  } else {
    // Show diff modal directly with comparison against Endpoint Central
    openCustomDiff('manageengine-endpoint-central', softwareId);
  }
}

// ============================================================================
// 2. TAB SWITCHING (FULL SPECS / EDITIONS & PRICING / DIRECT COMPETITOR DIFF)
// ============================================================================
function switchTab(tabId) {
  const specsContent = document.getElementById('specsTabContent');
  const pricingContent = document.getElementById('pricingTabContent');
  const diffContent = document.getElementById('diffTabContent');

  const tabSpecsBtn = document.getElementById('tabSpecsBtn');
  const tabPricingBtn = document.getElementById('tabPricingBtn');
  const tabDiffBtn = document.getElementById('tabDiffBtn');
  const accordionToggleWrapper = document.getElementById('accordionToggleWrapper');

  // Reset tabs
  [tabSpecsBtn, tabPricingBtn, tabDiffBtn].forEach(btn => {
    if (btn) {
      btn.classList.remove('border-brand-orange', 'text-brand-orange');
      btn.classList.add('border-transparent', 'text-slate-400');
    }
  });

  // Hide all contents
  if (specsContent) specsContent.classList.add('hidden');
  if (pricingContent) pricingContent.classList.add('hidden');
  if (diffContent) diffContent.classList.add('hidden');
  if (accordionToggleWrapper) accordionToggleWrapper.classList.add('hidden');

  if (tabId === 'specsTab') {
    if (specsContent) specsContent.classList.remove('hidden');
    if (tabSpecsBtn) {
      tabSpecsBtn.classList.add('border-brand-orange', 'text-brand-orange');
      tabSpecsBtn.classList.remove('border-transparent', 'text-slate-400');
    }
    if (accordionToggleWrapper) accordionToggleWrapper.classList.remove('hidden');
  } else if (tabId === 'pricingTab') {
    if (pricingContent) pricingContent.classList.remove('hidden');
    if (tabPricingBtn) {
      tabPricingBtn.classList.add('border-brand-orange', 'text-brand-orange');
      tabPricingBtn.classList.remove('border-transparent', 'text-slate-400');
    }
  } else if (tabId === 'diffTab') {
    if (diffContent) diffContent.classList.remove('hidden');
    if (tabDiffBtn) {
      tabDiffBtn.classList.add('border-brand-orange', 'text-brand-orange');
      tabDiffBtn.classList.remove('border-transparent', 'text-slate-400');
    }
  }
}

// ============================================================================
// 3. ACCORDION EXPAND / COLLAPSE
// ============================================================================
function toggleAccordion(secId) {
  const content = document.getElementById(`content-${secId}`);
  const arrow = document.getElementById(`arrow-${secId}`);

  if (!content || !arrow) return;

  if (content.classList.contains('hidden')) {
    content.classList.remove('hidden');
    arrow.classList.add('rotate-180');
  } else {
    content.classList.add('hidden');
    arrow.classList.remove('rotate-180');
  }
}

let allAccordionsExpanded = true;
function toggleAllAccordions() {
  const sections = ['sec1', 'sec2', 'sec3', 'sec4', 'sec5', 'sec6', 'sec7'];
  const btn = document.getElementById('toggleAllAccordionsBtn');

  allAccordionsExpanded = !allAccordionsExpanded;

  sections.forEach(secId => {
    const content = document.getElementById(`content-${secId}`);
    const arrow = document.getElementById(`arrow-${secId}`);
    if (content && arrow) {
      if (allAccordionsExpanded) {
        content.classList.remove('hidden');
        arrow.classList.add('rotate-180');
      } else {
        content.classList.add('hidden');
        arrow.classList.remove('rotate-180');
      }
    }
  });

  if (btn) {
    btn.querySelector('span').textContent = allAccordionsExpanded ? 'Collapse All Sections' : 'Expand All Sections';
  }
}

// ============================================================================
// 4. PARAMETRIC FACETED FILTER ENGINE
// ============================================================================
function initParametricFilters() {
  const deployBoxes = document.querySelectorAll('input[name="filter_deploy"]');
  const authBoxes = document.querySelectorAll('input[name="filter_auth"]');
  const freeRadios = document.querySelectorAll('input[name="filter_freetier"]');
  const scaleSlider = document.getElementById('nodeScaleSlider');
  const scaleValDisplay = document.getElementById('nodeScaleVal');
  const resetBtn = document.getElementById('resetFiltersBtn');

  const recalculateFilters = () => {
    const selectedDeploys = Array.from(deployBoxes).filter(b => b.checked).map(b => b.value);
    const selectedAuths = Array.from(authBoxes).filter(b => b.checked).map(b => b.value);
    const selectedFreeRadio = document.querySelector('input[name="filter_freetier"]:checked')?.value || 'any';
    const minScale = parseInt(scaleSlider.value, 10);

    if (scaleValDisplay) {
      scaleValDisplay.textContent = `${minScale.toLocaleString()}+ Nodes`;
    }

    const matches = SOFTWARE_CATALOG.filter(item => {
      // Scale check
      if (item.max_nodes < minScale) return false;

      // Free tier check
      if (selectedFreeRadio === 'yes' && !item.free_tier) return false;
      if (selectedFreeRadio === 'no' && item.free_tier) return false;

      // Deploy check: item must support at least one of selected deploys if any are selected
      if (selectedDeploys.length > 0) {
        const hasDeploy = selectedDeploys.some(d => item.deployment.includes(d));
        if (!hasDeploy) return false;
      }

      // Auth check
      if (selectedAuths.length > 0) {
        const hasAuth = selectedAuths.some(a => item.auth.includes(a));
        if (!hasAuth) return false;
      }

      return true;
    });

    const matchCountEl = document.getElementById('filterMatchCount');
    if (matchCountEl) {
      matchCountEl.textContent = `${matches.length} Platform${matches.length === 1 ? '' : 's'}`;
    }
  };

  [...deployBoxes, ...authBoxes, ...freeRadios].forEach(input => {
    input.addEventListener('change', recalculateFilters);
  });

  if (scaleSlider) {
    scaleSlider.addEventListener('input', recalculateFilters);
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      deployBoxes.forEach(b => b.checked = true);
      authBoxes.forEach(b => b.checked = true);
      const anyRadio = document.querySelector('input[name="filter_freetier"][value="any"]');
      if (anyRadio) anyRadio.checked = true;
      if (scaleSlider) scaleSlider.value = 25000;
      recalculateFilters();
      showToast('Filters reset to default.', true);
    });
  }

  recalculateFilters();
}

function filterByCategory(categoryId) {
  showToast(`Filtered category: ${categoryId.toUpperCase()}`, true);
  switchTab('specsTab');
}

// ============================================================================
// 5. SIDE-BY-SIDE COMPARISON QUEUE
// ============================================================================
function toggleCompare(softwareId) {
  const idx = compareQueue.indexOf(softwareId);
  const btn = document.getElementById('addToCompareBtn');
  const btnText = document.getElementById('compareBtnText');

  if (idx > -1) {
    compareQueue.splice(idx, 1);
    if (btnText) btnText.textContent = 'Add to Compare';
    showToast('Removed from comparison queue.', false);
  } else {
    if (compareQueue.length >= 4) {
      showToast('Maximum 4 software platforms can be compared simultaneously.', false);
      return;
    }
    compareQueue.push(softwareId);
    if (btnText) btnText.textContent = 'In Compare Queue (✓)';
    showToast('Added to comparison queue.', true);
  }

  renderCompareDrawer();
}

function renderCompareDrawer() {
  const drawer = document.getElementById('compareDrawer');
  const slots = document.getElementById('compareSlots');

  if (!drawer || !slots) return;

  if (compareQueue.length === 0) {
    drawer.classList.add('translate-y-full');
    return;
  }

  drawer.classList.remove('translate-y-full');

  slots.innerHTML = compareQueue.map(id => {
    const item = SOFTWARE_CATALOG.find(s => s.id === id);
    const name = item ? item.name : id;
    return `
      <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono text-slate-200">
        <span>${name}</span>
        <button onclick="event.stopPropagation(); removeCompareSlot('${id}')" class="text-slate-400 hover:text-red-400 font-bold ml-1">×</button>
      </div>
    `;
  }).join('');
}

function removeCompareSlot(softwareId) {
  const idx = compareQueue.indexOf(softwareId);
  if (idx > -1) {
    compareQueue.splice(idx, 1);
    if (softwareId === 'manageengine-endpoint-central') {
      const btnText = document.getElementById('compareBtnText');
      if (btnText) btnText.textContent = 'Add to Compare';
    }
    renderCompareDrawer();
  }
}

function clearCompareQueue() {
  compareQueue = [];
  const btnText = document.getElementById('compareBtnText');
  if (btnText) btnText.textContent = 'Add to Compare';
  renderCompareDrawer();
  showToast('Comparison queue cleared.', true);
}

function openCustomDiff(id1, id2) {
  if (!compareQueue.includes(id1)) compareQueue.push(id1);
  if (!compareQueue.includes(id2)) compareQueue.push(id2);
  renderCompareDrawer();
  openModal('diffModal');
}

// ============================================================================
// 6. MODAL & KEYBOARD CONTROLS
// ============================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
  }
}

function initKeyShortcuts() {
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const input = document.getElementById('globalSearchInput');
      if (input) {
        input.focus();
        input.select();
      }
    } else if (e.key === 'Escape') {
      ['diffModal', 'reportModal', 'suggestModal'].forEach(closeModal);
    }
  });
}

// ============================================================================
// 7. FORM SUBMISSIONS & TOAST NOTIFICATIONS
// ============================================================================
function handleReportSubmit(e) {
  e.preventDefault();
  closeModal('reportModal');
  showToast('Audit report submitted. An ITVedas engineer will review the citation.', true);
}

function handleSuggestSubmit(e) {
  e.preventDefault();
  closeModal('suggestModal');
  showToast('Software suggestion submitted for architectural indexing.', true);
}

function showToast(msg, isSuccess = true) {
  const toast = document.getElementById('toastNotification');
  const toastMsg = document.getElementById('toastMsg');
  const toastIcon = document.getElementById('toastIcon');

  if (!toast || !toastMsg) return;

  toastMsg.textContent = msg;
  toastIcon.textContent = isSuccess ? '✓' : 'ℹ';
  toastIcon.className = isSuccess ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold';

  toast.classList.remove('translate-y-[-150%]');
  toast.classList.add('translate-y-0');

  setTimeout(() => {
    toast.classList.remove('translate-y-0');
    toast.classList.add('translate-y-[-150%]');
  }, 3500);
}

function escapeHtml(string) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(string));
  return div.innerHTML;
}


// Delegated click handling for elements marked data-action="fnName"
// (replaces inline onclick= attributes so the page can run under a CSP
// without 'unsafe-inline' handlers). Only whitelisted functions run.
(function () {
  const ACTIONS = {
    clearCompareQueue, closeModal, filterByCategory, openCustomDiff,
    openModal, switchTab, toggleAccordion, toggleAllAccordions, toggleCompare,
  };
  document.addEventListener('click', function (e) {
    const el = e.target.closest('[data-action]');
    if (!el) return;
    if (el.hasAttribute('data-self-only') && e.target !== el) return;
    const fn = ACTIONS[el.dataset.action];
    if (!fn) return;
    if (el.hasAttribute('data-prevent')) e.preventDefault();
    let args = [];
    try { args = JSON.parse(el.dataset.args || '[]'); } catch (_) {}
    fn.apply(el, args);
  });
})();
