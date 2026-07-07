export interface ArticleFrontmatter {
  // Basic
  title: string;
  description: string;
  slug: string;

  // Content
  category: string;
  subcategory?: string;
  tags: string[];
  keywords: string[];

  // Metadata
  author?: string;
  authorEmail?: string;
  published: Date;
  lastUpdated: Date;
  readingTime?: number;

  // SEO
  seoTitle?: string;
  seoDescription?: string;
  canonical?: string;
  ogImage?: string;
  ogType?: string;

  // Relations
  relatedArticles?: string[];
  previousArticle?: string;
  nextArticle?: string;

  // Status
  draft?: boolean;
  featured?: boolean;
  version?: string;
}

export interface Article extends ArticleFrontmatter {
  content: string;
  contentHtml: string;
  wordCount: number;
  sections: ArticleSection[];
}

export interface ArticleSection {
  id: string;
  title: string;
  level: number;
  content: string;
}

export interface Category {
  slug: string;
  title: string;
  description: string;
  icon?: string;
  color?: string;
  subcategories: SubCategory[];
  articleCount: number;
  relatedCategories?: string[];
  featured?: boolean;
}

export interface SubCategory {
  slug: string;
  title: string;
  description?: string;
  articleCount: number;
}

export interface TableOfContents {
  items: TOCItem[];
}

export interface TOCItem {
  id: string;
  title: string;
  level: number;
  children?: TOCItem[];
}

export interface SearchResult {
  slug: string;
  title: string;
  description: string;
  category: string;
  excerpt: string;
  readingTime: number;
  published: Date;
  relevance: number;
}

export interface SitemapEntry {
  url: string;
  lastModified: Date;
  changeFrequency: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  priority: number;
}
