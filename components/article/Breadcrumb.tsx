import React from 'react';
import Link from 'next/link';
import clsx from 'clsx';

interface BreadcrumbItem {
  title: string;
  url: string;
  current?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumb({ items, className }: BreadcrumbProps): JSX.Element {
  return (
    <nav
      className={clsx(
        'flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400 mb-6',
        className
      )}
      aria-label="Breadcrumb"
    >
      <ol className="flex items-center gap-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {item.current ? (
              <span className="font-medium text-neutral-900 dark:text-neutral-100">
                {item.title}
              </span>
            ) : (
              <>
                <Link
                  href={item.url}
                  className="hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
                >
                  {item.title}
                </Link>
                {index < items.length - 1 && (
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
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                )}
              </>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
