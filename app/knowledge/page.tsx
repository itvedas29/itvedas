import { Metadata } from 'next';
import { SearchBar } from '@/components/search/SearchBar';
import { getArticles } from '@/lib/content/loader';
import Link from 'next/link';
import { Badge } from '@/components/ui';

export const metadata: Metadata = {
  title: 'Knowledge Base',
  description: 'Browse the ITVedas knowledge base of comprehensive IT guides and tutorials.',
  openGraph: {
    title: 'ITVedas Knowledge Base',
    description: 'Browse comprehensive IT guides covering networking, cloud, security, and administration.',
    type: 'website',
  },
};

// Group articles by category
function groupArticlesByCategory(articles: any[]) {
  const grouped: Record<string, any[]> = {};
  articles.forEach((article) => {
    if (!grouped[article.category]) {
      grouped[article.category] = [];
    }
    grouped[article.category].push(article);
  });
  return grouped;
}

export default function KnowledgeBasePage() {
  const articles = getArticles().slice(0, 50); // Limit to 50 for now
  const grouped = groupArticlesByCategory(articles);
  const categories = Object.keys(grouped).sort();

  return (
    <div className="min-h-screen bg-white dark:bg-neutral-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-brand-600 to-brand-700 dark:from-brand-900 dark:to-brand-800 text-white py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold mb-4">Knowledge Base</h1>
          <p className="text-lg text-brand-100 mb-8">
            Comprehensive IT guides covering networking, cloud, security, DevOps, and more.
          </p>
          <div className="max-w-2xl">
            <SearchBar />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {categories.map((category) => (
          <div key={category} className="mb-16">
            <div className="mb-8">
              <h2 className="text-3xl font-bold mb-2">{category}</h2>
              <div className="h-1 w-12 bg-brand-600 dark:bg-brand-400"></div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {grouped[category].map((article) => (
                <Link
                  key={article.slug}
                  href={`/knowledge/${article.slug}`}
                  className="group p-6 border border-neutral-200 dark:border-neutral-800 rounded-lg hover:border-brand-500 dark:hover:border-brand-500 hover:shadow-lg transition-all"
                >
                  <div className="mb-3">
                    <Badge variant="primary" size="sm">
                      {article.category}
                    </Badge>
                  </div>
                  <h3 className="text-xl font-bold mb-2 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                    {article.title}
                  </h3>
                  <p className="text-neutral-600 dark:text-neutral-400 text-sm mb-4 line-clamp-2">
                    {article.description}
                  </p>
                  <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400">
                    <span>{article.readingTime || 10} min read</span>
                    <span>
                      {new Date(article.published).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
