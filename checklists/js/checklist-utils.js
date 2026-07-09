// Checklist Utilities

class ChecklistManager {
  constructor(checklistId) {
    this.checklistId = checklistId;
    this.storageKey = `checklist-${checklistId}`;
  }

  // Get all checked items
  getCheckedItems() {
    const data = localStorage.getItem(this.storageKey);
    return data ? JSON.parse(data) : [];
  }

  // Add checked item
  checkItem(itemIndex) {
    const checked = this.getCheckedItems();
    if (!checked.includes(itemIndex)) {
      checked.push(itemIndex);
      localStorage.setItem(this.storageKey, JSON.stringify(checked));
    }
    this.updateProgress();
  }

  // Remove checked item
  uncheckItem(itemIndex) {
    let checked = this.getCheckedItems();
    checked = checked.filter(i => i !== itemIndex);
    localStorage.setItem(this.storageKey, JSON.stringify(checked));
    this.updateProgress();
  }

  // Get progress percentage
  getProgress() {
    const checked = this.getCheckedItems();
    const total = document.querySelectorAll('.checklist-item input[type="checkbox"]').length;
    return total > 0 ? Math.round((checked.length / total) * 100) : 0;
  }

  // Update progress display
  updateProgress() {
    const progress = this.getProgress();
    const progressEl = document.getElementById('checklistProgress');
    if (progressEl) {
      progressEl.textContent = progress + '%';
      progressEl.parentElement.style.width = progress + '%';
    }
  }

  // Clear all checks
  clearAll() {
    if (confirm('Clear all checks? This cannot be undone.')) {
      localStorage.removeItem(this.storageKey);
      document.querySelectorAll('.checklist-item input[type="checkbox"]').forEach(cb => cb.checked = false);
      this.updateProgress();
    }
  }

  // Export as CSV
  exportCSV(filename) {
    const items = [];
    document.querySelectorAll('.checklist-item').forEach((item, index) => {
      const checkbox = item.querySelector('input[type="checkbox"]');
      const text = item.querySelector('.item-text')?.textContent || '';
      const priority = item.querySelector('.item-priority')?.textContent || '';
      const owner = item.querySelector('.item-owner')?.textContent || '';
      const checked = checkbox.checked ? 'Yes' : 'No';
      items.push([checked, text, priority, owner, '']);
    });

    let csv = 'Completed,Item,Priority,Responsible Owner,Notes\n';
    items.forEach(row => {
      csv += row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    this.downloadFile(blob, filename || 'checklist.csv');
  }

  // Export as Excel-like CSV
  exportExcel(filename) {
    this.exportCSV(filename || 'checklist.xlsx');
  }

  // Download helper
  downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  // Generate PDF export
  exportPDF(filename) {
    const element = document.querySelector('article');
    const opt = {
      margin: 10,
      filename: filename || 'checklist.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };

    // Simple fallback: print to PDF
    window.print();
  }
}

// Initialize checklist on page load
document.addEventListener('DOMContentLoaded', () => {
  const checklistId = document.body.dataset.checklistId;
  if (!checklistId) return;

  const manager = new ChecklistManager(checklistId);

  // Restore checked state
  const checked = manager.getCheckedItems();
  document.querySelectorAll('.checklist-item input[type="checkbox"]').forEach((cb, index) => {
    if (checked.includes(index)) {
      cb.checked = true;
      cb.closest('.checklist-item').classList.add('item-checked');
    }
  });

  // Attach event listeners
  document.querySelectorAll('.checklist-item input[type="checkbox"]').forEach((cb, index) => {
    cb.addEventListener('change', () => {
      if (cb.checked) {
        manager.checkItem(index);
        cb.closest('.checklist-item').classList.add('item-checked');
      } else {
        manager.uncheckItem(index);
        cb.closest('.checklist-item').classList.remove('item-checked');
      }
    });
  });

  // Download button handlers
  document.querySelectorAll('[data-export]').forEach(btn => {
    btn.addEventListener('click', () => {
      const format = btn.dataset.export;
      const title = document.querySelector('h1')?.textContent || 'checklist';
      const filename = `${title.toLowerCase().replace(/\s+/g, '-')}.${format === 'pdf' ? 'pdf' : 'csv'}`;

      if (format === 'pdf') manager.exportPDF(filename);
      else if (format === 'excel') manager.exportExcel(filename);
      else if (format === 'csv') manager.exportCSV(filename);
    });
  });

  // Clear all button
  document.getElementById('clearAll')?.addEventListener('click', () => manager.clearAll());

  // Update progress on init
  manager.updateProgress();
});

// FAQ accordion functionality
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.faq-item').forEach(item => {
    item.querySelector('.faq-question').addEventListener('click', () => {
      item.classList.toggle('active');
    });
  });
});

// Print functionality
function printChecklist() {
  window.print();
}

// Share functionality
function shareChecklist(platform) {
  const url = window.location.href;
  const title = document.querySelector('h1')?.textContent || 'IT Operations Checklist';

  const shareUrls = {
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
    email: `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(url)}`
  };

  if (shareUrls[platform]) {
    window.open(shareUrls[platform], '_blank', 'width=600,height=400');
  }
}

// Table of contents smooth scrolling
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (href === '#') return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
        // Highlight for a moment
        target.style.backgroundColor = 'rgba(255, 107, 53, 0.1)';
        setTimeout(() => {
          target.style.backgroundColor = '';
        }, 2000);
      }
    });
  });
});
