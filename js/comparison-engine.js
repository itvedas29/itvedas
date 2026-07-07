/**
 * ITVedas Comparison Engine
 * Dynamic comparison page creation and interactivity
 */

class ComparisonEngine {
  constructor(config = {}) {
    this.config = config;
    this.init();
  }

  init() {
    this.renderComparisonTable();
    this.setupTabToggle();
    this.setupSortability();
    this.generateSchema();
  }

  renderComparisonTable() {
    const { items = [], features = [], tableId = 'comparison-table' } = this.config;
    const table = document.getElementById(tableId);
    if (!table) return;

    const html = `
      <table class="comparison-table">
        <thead>
          <tr>
            <th class="feature-column">Feature</th>
            ${items.map((item, i) => `
              <th class="item-column" data-item-index="${i}">
                <div class="item-header">
                  ${item.icon ? `<span class="item-icon">${item.icon}</span>` : ''}
                  <strong>${item.name}</strong>
                  ${item.logo ? `<img src="${item.logo}" alt="${item.name}" class="item-logo">` : ''}
                </div>
                ${item.tagline ? `<p class="item-tagline">${item.tagline}</p>` : ''}
              </th>
            `).join('')}
          </tr>
        </thead>
        <tbody>
          ${features.map((feature, i) => `
            <tr class="${i % 2 === 0 ? 'even' : 'odd'}">
              <td class="feature-column">
                <strong>${feature.name}</strong>
                ${feature.description ? `<p class="feature-description">${feature.description}</p>` : ''}
              </td>
              ${items.map((item, j) => {
                const value = this.getFeatureValue(feature, item);
                return `
                  <td class="comparison-cell" data-item-index="${j}">
                    ${this.renderCellValue(value, feature.type)}
                  </td>
                `;
              }).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    table.innerHTML = html;
  }

  getFeatureValue(feature, item) {
    if (feature.type === 'boolean') {
      return item[feature.key] ? '✓' : '✗';
    } else if (feature.type === 'rating') {
      return item[feature.key] || 'N/A';
    } else if (feature.type === 'price') {
      return item[feature.key] || 'Custom';
    } else {
      return item[feature.key] || 'N/A';
    }
  }

  renderCellValue(value, type) {
    if (type === 'boolean') {
      if (value === '✓') {
        return '<span class="badge badge-success">✓ Yes</span>';
      } else if (value === '✗') {
        return '<span class="badge badge-warning">✗ No</span>';
      }
      return value;
    } else if (type === 'rating') {
      return this.renderRating(value);
    } else if (type === 'price') {
      return `<span class="price-value">${value}</span>`;
    }
    return value;
  }

  renderRating(value) {
    if (!value || isNaN(value)) return 'N/A';

    const rating = parseFloat(value);
    const stars = '⭐'.repeat(Math.round(rating));
    return `<span class="rating">${stars} (${rating}/5)</span>`;
  }

  setupTabToggle() {
    const tabs = document.querySelectorAll('[data-comparison-tab]');
    tabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        const tabName = tab.dataset.comparisonTab;
        this.switchTab(tabName);
      });
    });
  }

  switchTab(tabName) {
    const tabs = document.querySelectorAll('[data-comparison-tab]');
    const panels = document.querySelectorAll('[data-comparison-panel]');

    tabs.forEach(t => {
      t.classList.toggle('active', t.dataset.comparisonTab === tabName);
    });

    panels.forEach(p => {
      p.classList.toggle('active', p.dataset.comparisonPanel === tabName);
    });
  }

  setupSortability() {
    const headers = document.querySelectorAll('.comparison-table thead th.item-column');
    headers.forEach((header, index) => {
      header.style.cursor = 'pointer';
      header.title = 'Click to highlight';

      header.addEventListener('click', () => {
        this.highlightColumn(index);
      });
    });
  }

  highlightColumn(index) {
    const cells = document.querySelectorAll('.comparison-table tbody td');
    const isHighlighted = document.querySelector(
      `.comparison-table tbody td[data-item-index="${index}"]`
    )?.classList.contains('highlighted');

    document.querySelectorAll('[data-item-index]').forEach(el => {
      el.classList.remove('highlighted');
    });

    if (!isHighlighted) {
      document.querySelectorAll(`[data-item-index="${index}"]`).forEach(el => {
        el.classList.add('highlighted');
      });
    }
  }

  generateSchema() {
    const { title, description, items } = this.config;

    const schema = {
      '@context': 'https://schema.org',
      '@type': 'ComparisonChart',
      name: title,
      description: description,
      publisher: {
        '@type': 'Organization',
        name: 'ITVedas',
        url: 'https://itvedas.com'
      },
      itemReviewed: items.map(item => ({
        '@type': 'SoftwareApplication',
        name: item.name,
        applicationCategory: 'Utility',
        url: item.url || null
      }))
    };

    const schemaScript = document.createElement('script');
    schemaScript.type = 'application/ld+json';
    schemaScript.textContent = JSON.stringify(schema);
    document.head.appendChild(schemaScript);
  }

  static createComparisonPage(config) {
    return new ComparisonEngine(config);
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('[data-comparison-engine]')) {
      const configStr = document.querySelector('[data-comparison-engine]').dataset.config;
      const config = JSON.parse(configStr || '{}');
      new ComparisonEngine(config);
    }
  });
} else {
  if (document.querySelector('[data-comparison-engine]')) {
    const configStr = document.querySelector('[data-comparison-engine]').dataset.config;
    const config = JSON.parse(configStr || '{}');
    new ComparisonEngine(config);
  }
}

window.ComparisonEngine = ComparisonEngine;
