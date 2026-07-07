#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ARTICLES_DIR = path.join(process.cwd(), 'content', 'articles');
const PUBLIC_DIR = path.join(process.cwd(), 'public');

function parseYamlValue(value) {
  value = value.trim();
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (!isNaN(value) && value !== '') return Number(value);
  if (value.startsWith('"') && value.endsWith('"')) return value.slice(1, -1);
  if (value.startsWith('[') && value.endsWith(']')) {
    return value
      .slice(1, -1)
      .split(',')
      .map((v) => {
        let item = v.trim();
        if (item.startsWith('"') && item.endsWith('"')) {
          return item.slice(1, -1);
        }
        return item;
      });
  }
  return value;
}

function extractFrontmatter(content) {
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) {
    return null;
  }

  const frontmatterText = frontmatterMatch[1];
  const frontmatter = {};

  const lines = frontmatterText.split('\n');
  let currentKey = null;
  let currentValue = '';

  for (const line of lines) {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0 && !line.startsWith(' ')) {
      if (currentKey) {
        frontmatter[currentKey] = parseYamlValue(currentValue);
      }
      currentKey = line.substring(0, colonIndex).trim();
      currentValue = line.substring(colonIndex + 1).trim();
    } else if (currentKey && line.startsWith('  ')) {
      currentValue += '\n' + line;
    }
  }

  if (currentKey) {
    frontmatter[currentKey] = parseYamlValue(currentValue);
  }

  return frontmatter;
}

function extractExcerpt(content, maxLength = 200) {
  // Remove frontmatter
  const contentWithoutFrontmatter = content.replace(/^---\n[\s\S]*?\n---/, '').trim();

  // Remove markdown formatting
  let text = contentWithoutFrontmatter
    .replace(/#+\s/g, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/`/g, '')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    .replace(/#{1,6}\s/g, '')
    .trim();

  // Take first paragraph
  const firstParagraph = text.split('\n\n')[0];

  if (firstParagraph.length > maxLength) {
    return firstParagraph.substring(0, maxLength).split(' ').slice(0, -1).join(' ') + '...';
  }

  return firstParagraph;
}

function readArticles() {
  if (!fs.existsSync(ARTICLES_DIR)) {
    return [];
  }

  const files = fs.readdirSync(ARTICLES_DIR).filter((file) => file.endsWith('.mdx'));
  const articles = [];

  files.forEach((file) => {
    const filePath = path.join(ARTICLES_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');

    const frontmatter = extractFrontmatter(content);
    if (!frontmatter || frontmatter.draft === true) {
      return;
    }

    const excerpt = extractExcerpt(content);
    const wordCount = content.split(/\s+/).length;
    const readingTime = Math.ceil(wordCount / 200);

    articles.push({
      slug: frontmatter.slug || file.replace(/\.mdx$/, ''),
      title: frontmatter.title || 'Untitled',
      description: frontmatter.description || '',
      excerpt,
      category: frontmatter.category || 'Uncategorized',
      tags: Array.isArray(frontmatter.tags) ? frontmatter.tags : [],
      keywords: Array.isArray(frontmatter.keywords) ? frontmatter.keywords : [],
      published: frontmatter.published || new Date().toISOString(),
      readingTime,
    });
  });

  return articles;
}

function generateSearchIndex(articles) {
  return {
    version: 1,
    timestamp: new Date().toISOString(),
    articles: articles.map((article) => ({
      ...article,
      searchText: [article.title, article.description, article.category, ...(article.tags || []), ...(article.keywords || [])].join(' ').toLowerCase(),
    })),
  };
}

function main() {
  try {
    console.log('🔍 Generating search index...');

    const articles = readArticles();
    console.log(`   Found ${articles.length} published articles`);

    const searchIndex = generateSearchIndex(articles);

    if (!fs.existsSync(PUBLIC_DIR)) {
      fs.mkdirSync(PUBLIC_DIR, { recursive: true });
    }

    const outputPath = path.join(PUBLIC_DIR, 'search-index.json');
    fs.writeFileSync(outputPath, JSON.stringify(searchIndex, null, 2));

    console.log(`✅ Search index generated: ${outputPath}`);
    console.log(`   Total articles indexed: ${articles.length}`);
    console.log(`   Index file size: ${(fs.statSync(outputPath).size / 1024).toFixed(2)} KB`);
  } catch (error) {
    console.error('❌ Error generating search index:', error);
    process.exit(1);
  }
}

main();
