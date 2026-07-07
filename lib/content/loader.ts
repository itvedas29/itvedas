import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { ArticleFrontmatter, Article, Category } from '@types/article';

const CONTENT_DIR = path.join(process.cwd(), 'content');
const ARTICLES_DIR = path.join(CONTENT_DIR, 'articles');
const CATEGORIES_DIR = path.join(CONTENT_DIR, 'categories');

export function getAllArticleSlugs(): string[] {
  if (!fs.existsSync(ARTICLES_DIR)) {
    return [];
  }

  return fs.readdirSync(ARTICLES_DIR)
    .filter((file) => file.endsWith('.mdx'))
    .map((file) => file.replace(/\.mdx$/, ''));
}

export function getAllCategories(): string[] {
  if (!fs.existsSync(CATEGORIES_DIR)) {
    return [];
  }

  return fs.readdirSync(CATEGORIES_DIR)
    .filter((file) => file.endsWith('.json'))
    .map((file) => file.replace(/\.json$/, ''));
}

export function getArticleBySlug(slug: string): Article | null {
  const filePath = path.join(ARTICLES_DIR, `${slug}.mdx`);

  if (!fs.existsSync(filePath)) {
    return null;
  }

  const source = fs.readFileSync(filePath, 'utf-8');
  const { data, content } = matter(source);

  const frontmatter = data as ArticleFrontmatter;

  return {
    ...frontmatter,
    content,
    contentHtml: '', // Will be processed by MDX
    wordCount: content.split(/\s+/).length,
    sections: [],
    published: new Date(frontmatter.published),
    lastUpdated: new Date(frontmatter.lastUpdated),
  };
}

export function getArticles(
  category?: string,
  limit?: number,
  offset = 0
): Article[] {
  const slugs = getAllArticleSlugs();
  const articles = slugs
    .map((slug) => getArticleBySlug(slug))
    .filter((article): article is Article => article !== null)
    .filter((article) => !article.draft);

  if (category) {
    articles.filter((article) => article.category === category);
  }

  return articles
    .sort(
      (a, b) =>
        new Date(b.published).getTime() - new Date(a.published).getTime()
    )
    .slice(offset, limit ? offset + limit : undefined);
}

export function getCategoryBySlug(slug: string): Category | null {
  const filePath = path.join(CATEGORIES_DIR, `${slug}.json`);

  if (!fs.existsSync(filePath)) {
    return null;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(content);
}

export function getRelatedArticles(
  article: Article,
  limit = 5
): Article[] {
  const allArticles = getArticles();

  const related = allArticles
    .filter((a) => a.slug !== article.slug)
    .filter(
      (a) =>
        a.category === article.category ||
        a.tags.some((tag) => article.tags.includes(tag)) ||
        a.keywords.some((kw) => article.keywords.includes(kw))
    )
    .slice(0, limit);

  return related;
}

export function calculateReadingTime(content: string): number {
  const wordsPerMinute = 200;
  const wordCount = content.split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}
