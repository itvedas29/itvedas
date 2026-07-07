import { Article, Category } from '@types/article';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://itvedas.com';
const SITE_NAME = 'ITVedas';
const SITE_DESCRIPTION =
  'Professional vendor-neutral IT Knowledge Base. Learn IT topics from the ground up.';

export interface SchemaOrg {
  '@context': string;
  '@type': string;
  [key: string]: unknown;
}

export function generateArticleSchema(
  article: Article,
  articleUrl: string
): SchemaOrg {
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.seoTitle || article.title,
    description: article.seoDescription || article.description,
    image: article.ogImage ? `${SITE_URL}${article.ogImage}` : undefined,
    datePublished: article.published.toISOString(),
    dateModified: article.lastUpdated.toISOString(),
    author: {
      '@type': 'Organization',
      name: article.author || SITE_NAME,
      url: SITE_URL,
    },
    publisher: {
      '@type': 'Organization',
      name: SITE_NAME,
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_URL}/logo.svg`,
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': articleUrl,
    },
  };
}

export function generateBreadcrumbSchema(
  breadcrumbs: { title: string; url: string }[]
): SchemaOrg {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((crumb, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: crumb.title,
      item: crumb.url,
    })),
  };
}

export function generateFAQSchema(
  faqs: { question: string; answer: string }[]
): SchemaOrg {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
}

export function generateCategorySchema(
  category: Category,
  categoryUrl: string
): SchemaOrg {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: category.title,
    description: category.description,
    url: categoryUrl,
    publisher: {
      '@type': 'Organization',
      name: SITE_NAME,
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_URL}/logo.svg`,
      },
    },
  };
}

export function generateOrganizationSchema(): SchemaOrg {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: SITE_NAME,
    url: SITE_URL,
    logo: `${SITE_URL}/logo.svg`,
    description: SITE_DESCRIPTION,
    sameAs: [
      'https://twitter.com/itvedas',
      'https://www.linkedin.com/company/itvedas',
      'https://github.com/itvedas',
    ],
    contact: {
      '@type': 'ContactPoint',
      contactType: 'Editorial',
      email: 'hello@itvedas.com',
    },
  };
}

export function generateWebsiteSchema(): SchemaOrg {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE_NAME,
    url: SITE_URL,
    description: SITE_DESCRIPTION,
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}
