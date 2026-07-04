/**
 * Meta Tag Generator - Dynamically manages meta tags for SEO
 * Handles canonical URLs, OpenGraph, Twitter Cards, JSON-LD schemas
 */

const MetaTagGenerator = (() => {
  const CONFIG = {
    siteUrl: 'https://itvedas.com',
    siteName: 'ITVedas',
    defaultImage: 'https://itvedas.com/assets/og-default.png',
    defaultDescription: 'The complete IT knowledge hub — networking, cloud, security, DevOps, databases, Linux, hardware, compliance.',
    twitterHandle: '@ITVedas'
  };

  /**
   * Update canonical URL based on current page URL
   */
  const updateCanonicalUrl = (customUrl = null) => {
    const url = customUrl || window.location.origin + window.location.pathname + window.location.search;
    let canonical = document.querySelector('link[rel="canonical"]');

    if (!canonical) {
      canonical = document.createElement('link');
      canonical.rel = 'canonical';
      document.head.appendChild(canonical);
    }

    canonical.href = url;
  };

  /**
   * Update or create meta tag
   */
  const updateMetaTag = (name, content, isProperty = false) => {
    const attr = isProperty ? 'property' : 'name';
    let tag = document.querySelector(`meta[${attr}="${name}"]`);

    if (!tag) {
      tag = document.createElement('meta');
      tag.setAttribute(attr, name);
      document.head.appendChild(tag);
    }

    tag.content = content;
  };

  /**
   * Update page title
   */
  const updateTitle = (title) => {
    document.title = title;
    updateMetaTag('og:title', title, true);
    updateMetaTag('twitter:title', title);
  };

  /**
   * Update description
   */
  const updateDescription = (description) => {
    updateMetaTag('description', description);
    updateMetaTag('og:description', description, true);
    updateMetaTag('twitter:description', description);
  };

  /**
   * Update OpenGraph image
   */
  const updateImage = (imageUrl = CONFIG.defaultImage) => {
    updateMetaTag('og:image', imageUrl, true);
    updateMetaTag('og:image:width', '1200', true);
    updateMetaTag('og:image:height', '630', true);
    updateMetaTag('twitter:image', imageUrl);
  };

  /**
   * Set CVE page metadata
   */
  const setCVEMetadata = (cveId, cveData) => {
    const title = `${cveId} - CVE Vulnerability Details | ITVedas`;
    const description = `${cveId}: ${cveData.title || 'Vulnerability'} | CVSS: ${cveData.cvssScore || 'N/A'} | Severity: ${cveData.severity || 'Unknown'}. Detailed technical analysis, exploitation guide, and remediation procedures.`;
    const url = `${CONFIG.siteUrl}/cve/${cveId}/`;

    updateTitle(title);
    updateDescription(description);
    updateImage(); // Use default image for CVEs
    updateCanonicalUrl(url);
    updateMetaTag('keywords', `${cveId}, CVE, vulnerability, ${cveData.severity || 'security'}, CVSS, remediation`, false);
  };

  /**
   * Set CVE listing page metadata
   */
  const setCVEListingMetadata = (filterType = null, filterValue = null) => {
    let title = 'CVE Database - Search & Filter Vulnerabilities | ITVedas';
    let description = 'Browse and filter 640+ CVEs by severity, year, vendor, and CVSS score. Complete vulnerability database with technical analysis, detection guides, and remediation procedures.';
    let url = `${CONFIG.siteUrl}/cve/`;

    if (filterType && filterValue) {
      if (filterType === 'severity') {
        title = `${filterValue} Severity CVEs - Vulnerability Database | ITVedas`;
        description = `Browse all ${filterValue} severity vulnerabilities. ${CONFIG.defaultDescription}`;
        url += `severity/${filterValue.toLowerCase()}/`;
      } else if (filterType === 'year') {
        title = `${filterValue} CVEs - Vulnerability Database | ITVedas`;
        description = `CVE vulnerabilities from ${filterValue}. Complete database with technical details and remediation.`;
        url += `${filterValue}/`;
      } else if (filterType === 'vendor') {
        title = `${filterValue} CVEs - Vulnerability Database | ITVedas`;
        description = `Security vulnerabilities affecting ${filterValue} products. Technical analysis and mitigation strategies.`;
        url += `vendors/${filterValue.toLowerCase()}/`;
      } else if (filterType === 'search') {
        title = `Search: ${filterValue} - CVE Database | ITVedas`;
        description = `Search results for "${filterValue}" in CVE database. ${CONFIG.defaultDescription}`;
        url += `?search=${encodeURIComponent(filterValue)}`;
      }
    }

    updateTitle(title);
    updateDescription(description);
    updateImage();
    updateCanonicalUrl(url);
    updateMetaTag('keywords', 'CVE database, vulnerability search, CVSS, severity, vendor, remediation, patches', false);
  };

  /**
   * Set article page metadata
   */
  const setArticleMetadata = (article) => {
    const title = article.title || 'Article | ITVedas';
    const description = (article.description || article.summary || CONFIG.defaultDescription).substring(0, 160);
    const url = article.url || window.location.href;

    updateTitle(title);
    updateDescription(description);
    updateImage(article.image || CONFIG.defaultImage);
    updateCanonicalUrl(url);
    updateMetaTag('keywords', article.keywords || 'IT, technology, learning', false);

    if (article.datePublished) {
      updateMetaTag('datePublished', article.datePublished);
    }
    if (article.dateModified) {
      updateMetaTag('dateModified', article.dateModified);
    }
  };

  /**
   * Add or update JSON-LD schema
   */
  const setJsonLdSchema = (schema) => {
    let script = document.querySelector('script[type="application/ld+json"]#main-schema');

    if (!script) {
      script = document.createElement('script');
      script.type = 'application/ld+json';
      script.id = 'main-schema';
      document.head.appendChild(script);
    }

    script.textContent = JSON.stringify(schema);
  };

  /**
   * Generate CVE Article schema for detail pages
   */
  const generateCVEArticleSchema = (cveId, cveData) => {
    return {
      '@context': 'https://schema.org',
      '@type': 'Article',
      '@id': `${CONFIG.siteUrl}/cve/${cveId}/`,
      headline: `${cveId} Vulnerability - Technical Analysis & Remediation`,
      description: cveData.title || `Vulnerability details for ${cveId}`,
      image: CONFIG.defaultImage,
      datePublished: cveData.datePublished || new Date().toISOString(),
      dateModified: cveData.dateModified || new Date().toISOString(),
      author: {
        '@type': 'Organization',
        name: 'ITVedas',
        url: CONFIG.siteUrl
      },
      publisher: {
        '@type': 'Organization',
        name: 'ITVedas',
        logo: {
          '@type': 'ImageObject',
          url: `${CONFIG.siteUrl}/assets/logo-mark.svg`
        }
      },
      mainEntity: {
        '@type': 'SecurityVulnerability',
        identifier: cveId,
        name: cveData.title || `Vulnerability ${cveId}`,
        about: {
          '@type': 'Thing',
          name: cveData.affectedProducts?.join(', ') || 'Multiple products'
        },
        cvssScore: cveData.cvssScore || null,
        severity: cveData.severity || 'Unknown',
        discussionUrl: cveData.references?.[0] || '',
        infoUrl: `https://nvd.nist.gov/vuln/detail/${cveId}`
      }
    };
  };

  /**
   * Generate CVE Collection schema for listing pages
   */
  const generateCVECollectionSchema = (cveCount = 640) => {
    return {
      '@context': 'https://schema.org',
      '@type': 'CollectionPage',
      name: 'CVE Database - Search & Filter Vulnerabilities',
      description: 'Comprehensive database of CVE vulnerabilities with search, filtering, and detailed technical information.',
      url: `${CONFIG.siteUrl}/cve/`,
      mainEntity: {
        '@type': 'DataCatalog',
        name: 'CVE Vulnerability Database',
        description: 'Complete collection of CVE vulnerabilities',
        url: `${CONFIG.siteUrl}/cve/`,
        distribution: {
          '@type': 'DataDownload',
          encodingFormat: 'application/json',
          contentUrl: `${CONFIG.siteUrl}/cve-database-full.json`
        },
        keywords: 'CVE, vulnerability, security, CVSS, remediation',
        creator: {
          '@type': 'Organization',
          name: 'ITVedas',
          url: CONFIG.siteUrl
        }
      }
    };
  };

  /**
   * Generate breadcrumb schema
   */
  const generateBreadcrumbSchema = (items) => {
    const itemListElement = items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url
    }));

    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement
    };
  };

  /**
   * Public API
   */
  return {
    updateCanonicalUrl,
    updateTitle,
    updateDescription,
    updateImage,
    setCVEMetadata,
    setCVEListingMetadata,
    setArticleMetadata,
    setJsonLdSchema,
    generateCVEArticleSchema,
    generateCVECollectionSchema,
    generateBreadcrumbSchema,
    config: CONFIG
  };
})();

// Ensure module is accessible
if (typeof window !== 'undefined') {
  window.MetaTagGenerator = MetaTagGenerator;
}
