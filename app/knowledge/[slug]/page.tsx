import { notFound } from 'next/navigation';
import { MDXRemote } from 'next-mdx-remote/rsc';
import { Metadata } from 'next';
import { getArticleBySlug, getAllArticleSlugs, getRelatedArticles } from '@/lib/content/loader';
import { generateArticleSchema, generateBreadcrumbSchema } from '@/lib/seo/schema';
import { ArticleHeader } from '@/components/article/ArticleHeader';
import { Breadcrumb } from '@/components/article/Breadcrumb';
import { TableOfContents } from '@/components/article/TableOfContents';
import {
  BestPractice,
  CommonMistake,
  EnterpriseInsight,
  TipBox,
  ImportantNote,
} from '@/components/content/ContentBoxes';
import { Button, Badge, Card, Alert, CodeBlock } from '@/components/ui';

const components = {
  BestPractice,
  CommonMistake,
  EnterpriseInsight,
  TipBox,
  ImportantNote,
  Button,
  Badge,
  Card,
  Alert,
  CodeBlock,
  h2: (props: any) => <h2 className="mt-8 mb-4 pt-8 border-t border-neutral-200 dark:border-neutral-800" {...props} />,
  h3: (props: any) => <h3 className="mt-6 mb-3" {...props} />,
  p: (props: any) => <p className="mb-4" {...props} />,
  ul: (props: any) => <ul className="mb-4 ml-6 space-y-2" {...props} />,
  ol: (props: any) => <ol className="mb-4 ml-6 space-y-2 list-decimal" {...props} />,
  li: (props: any) => <li className="mb-2" {...props} />,
  table: (props: any) => (
    <div className="overflow-x-auto my-4">
      <table className="w-full border-collapse" {...props} />
    </div>
  ),
  th: (props: any) => (
    <th className="border border-neutral-200 dark:border-neutral-700 px-4 py-2 text-left bg-neutral-100 dark:bg-neutral-800" {...props} />
  ),
  td: (props: any) => (
    <td className="border border-neutral-200 dark:border-neutral-700 px-4 py-2" {...props} />
  ),
};

interface ArticlePageProps {
  params: {
    slug: string;
  };
}

export async function generateStaticParams() {
  const slugs = getAllArticleSlugs();
  return slugs.map((slug) => ({
    slug,
  }));
}

export async function generateMetadata(
  { params }: ArticlePageProps
): Promise<Metadata> {
  const article = getArticleBySlug(params.slug);

  if (!article) {
    return {
      title: 'Article Not Found',
      description: 'The article you are looking for does not exist.',
    };
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://itvedas.com';
  const articleUrl = `${siteUrl}/knowledge/${article.slug}`;

  return {
    title: article.seoTitle || article.title,
    description: article.seoDescription || article.description,
    keywords: article.keywords,
    authors: article.author ? [{ name: article.author }] : undefined,
    openGraph: {
      title: article.seoTitle || article.title,
      description: article.seoDescription || article.description,
      type: 'article',
      url: articleUrl,
      images: article.ogImage ? [{ url: `${siteUrl}${article.ogImage}` }] : undefined,
      publishedTime: article.published.toISOString(),
      modifiedTime: article.lastUpdated.toISOString(),
      authors: article.author ? [article.author] : undefined,
    },
    twitter: {
      card: 'summary_large_image',
      title: article.seoTitle || article.title,
      description: article.seoDescription || article.description,
      images: article.ogImage ? [`${siteUrl}${article.ogImage}`] : undefined,
    },
    alternates: {
      canonical: articleUrl,
    },
  };
}

export default function ArticlePage({ params }: ArticlePageProps) {
  const article = getArticleBySlug(params.slug);

  if (!article) {
    notFound();
  }

  const relatedArticles = getRelatedArticles(article, 5);
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://itvedas.com';
  const articleUrl = `${siteUrl}/knowledge/${article.slug}`;

  const breadcrumbs = [
    { title: 'Home', url: '/' },
    { title: 'Knowledge Base', url: '/knowledge' },
    { title: article.category, url: `/categories/${article.category.toLowerCase().replace(/\s+/g, '-')}` },
    { title: article.title, url: articleUrl, current: true },
  ];

  const articleSchema = generateArticleSchema(article, articleUrl);
  const breadcrumbSchema = generateBreadcrumbSchema(
    breadcrumbs.map((crumb) => ({
      title: crumb.title,
      url: crumb.url.startsWith('http') ? crumb.url : `${siteUrl}${crumb.url}`,
    }))
  );

  return (
    <article className="min-h-screen bg-white dark:bg-neutral-950">
      {/* Schema markup */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Breadcrumb */}
        <Breadcrumb items={breadcrumbs} />

        {/* Article Header */}
        <ArticleHeader article={article} readingTime={article.readingTime} />

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Article content */}
          <div className="lg:col-span-3">
            <div className="prose dark:prose-invert max-w-none">
              <MDXRemote source={article.content} components={components} />
            </div>
          </div>

          {/* Sidebar - Table of Contents */}
          <div className="lg:col-span-1">
            <div className="sticky top-20">
              {/* TOC would go here */}
              <div className="space-y-6">
                <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-6">
                  <h3 className="font-bold mb-4">Share this article</h3>
                  <div className="flex gap-2">
                    <a href={`https://twitter.com/intent/tweet?url=${articleUrl}`} target="_blank" rel="noopener noreferrer" className="flex-1 px-3 py-2 bg-blue-500 text-white rounded text-center text-sm hover:bg-blue-600">
                      Twitter
                    </a>
                    <a href={`https://www.linkedin.com/sharing/share-offsite/?url=${articleUrl}`} target="_blank" rel="noopener noreferrer" className="flex-1 px-3 py-2 bg-blue-700 text-white rounded text-center text-sm hover:bg-blue-800">
                      LinkedIn
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Related Articles */}
        {relatedArticles.length > 0 && (
          <div className="mt-16 pt-16 border-t border-neutral-200 dark:border-neutral-800">
            <h2 className="text-3xl font-bold mb-8">Related Articles</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {relatedArticles.map((relArticle) => (
                <a
                  key={relArticle.slug}
                  href={`/knowledge/${relArticle.slug}`}
                  className="group p-6 border border-neutral-200 dark:border-neutral-800 rounded-lg hover:border-brand-500 dark:hover:border-brand-500 transition-colors"
                >
                  <div className="mb-2">
                    <Badge variant="secondary" size="sm">
                      {relArticle.category}
                    </Badge>
                  </div>
                  <h3 className="font-bold group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors mb-2">
                    {relArticle.title}
                  </h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {relArticle.description}
                  </p>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </article>
  );
}
