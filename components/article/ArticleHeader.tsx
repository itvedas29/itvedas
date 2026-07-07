import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { Article } from '@types/article';

interface ArticleHeaderProps {
  article: Article;
  readingTime?: number;
}

export function ArticleHeader({ article, readingTime }: ArticleHeaderProps): JSX.Element {
  const publishDate = new Date(article.published);
  const lastUpdatedDate = new Date(article.lastUpdated);

  return (
    <header className="mb-8 pb-8 border-b border-neutral-200 dark:border-neutral-800">
      <div className="mb-4">
        <Badge variant="primary" size="sm">
          {article.category}
        </Badge>
      </div>

      <h1 className="mb-4 text-5xl font-display font-bold leading-tight tracking-tight">
        {article.title}
      </h1>

      <p className="mb-6 text-xl text-neutral-600 dark:text-neutral-400">
        {article.description}
      </p>

      <div className="flex flex-wrap gap-6 text-sm text-neutral-600 dark:text-neutral-400">
        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{readingTime || 10} min read</span>
        </div>

        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <time dateTime={publishDate.toISOString()}>
            {publishDate.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            })}
          </time>
        </div>

        {lastUpdatedDate.getTime() !== publishDate.getTime() && (
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>
              Updated{' '}
              <time dateTime={lastUpdatedDate.toISOString()}>
                {lastUpdatedDate.toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </time>
            </span>
          </div>
        )}
      </div>

      {article.tags && article.tags.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {article.tags.map((tag) => (
            <Badge key={tag} variant="secondary" size="sm">
              {tag}
            </Badge>
          ))}
        </div>
      )}
    </header>
  );
}
