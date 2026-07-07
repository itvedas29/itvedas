#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://itvedas.com';
const ARTICLES_DIR = path.join(process.cwd(), 'content', 'articles');
const PUBLIC_DIR = path.join(process.cwd(), 'public');

function readArticles() {
  if (!fs.existsSync(ARTICLES_DIR)) {
    return [];
  }

  const files = fs.readdirSync(ARTICLES_DIR).filter((file) => file.endsWith('.mdx'));
  const articles = [];

  files.forEach((file) => {
    const filePath = path.join(ARTICLES_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');

    // Extract frontmatter
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) {
      console.warn(`No frontmatter in ${file}, skipping...`);
      return;
    }

    const frontmatter = frontmatterMatch[1];
    const slugMatch = frontmatter.match(/slug:\s*"?([^"\n]+)"?/);
    const publishedMatch = frontmatter.match(/published:\s*(\d{4}-\d{2}-\d{2})/);
    const lastUpdatedMatch = frontmatter.match(/lastUpdated:\s*(\d{4}-\d{2}-\d{2})/);
    const draftMatch = frontmatter.match(/draft:\s*(true|false)/);

    const isDraft = draftMatch && draftMatch[1] === 'true';
    if (isDraft) {
      return;
    }

    const slug = slugMatch ? slugMatch[1] : file.replace(/\.mdx$/, '');
    const published = publishedMatch ? publishedMatch[1] : new Date().toISOString().split('T')[0];
    const lastUpdated = lastUpdatedMatch
      ? lastUpdatedMatch[1]
      : new Date().toISOString().split('T')[0];

    articles.push({
      url: `${SITE_URL}/knowledge/${slug}`,
      lastModified: lastUpdated,
      changeFrequency: 'weekly',
      priority: 0.8,
    });
  });

  return articles;
}

function generateSitemap(articles) {
  const staticPages = [
    { url: SITE_URL, lastModified: new Date().toISOString().split('T')[0], priority: 1.0 },
    {
      url: `${SITE_URL}/knowledge`,
      lastModified: new Date().toISOString().split('T')[0],
      priority: 0.9,
    },
  ];

  const allPages = [...staticPages, ...articles];

  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

  allPages.forEach((page) => {
    xml += '  <url>\n';
    xml += `    <loc>${escapeXml(page.url)}</loc>\n`;
    xml += `    <lastmod>${page.lastModified}</lastmod>\n`;
    xml += `    <changefreq>${page.changeFrequency}</changefreq>\n`;
    xml += `    <priority>${page.priority}</priority>\n`;
    xml += '  </url>\n';
  });

  xml += '</urlset>\n';

  return xml;
}

function escapeXml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}

function main() {
  try {
    console.log('📝 Generating sitemap.xml...');

    const articles = readArticles();
    console.log(`   Found ${articles.length} published articles`);

    const sitemap = generateSitemap(articles);

    if (!fs.existsSync(PUBLIC_DIR)) {
      fs.mkdirSync(PUBLIC_DIR, { recursive: true });
    }

    const outputPath = path.join(PUBLIC_DIR, 'sitemap.xml');
    fs.writeFileSync(outputPath, sitemap);

    console.log(`✅ Sitemap generated: ${outputPath}`);
    console.log(`   Total URLs: ${articles.length + 2}`);
  } catch (error) {
    console.error('❌ Error generating sitemap:', error);
    process.exit(1);
  }
}

main();
