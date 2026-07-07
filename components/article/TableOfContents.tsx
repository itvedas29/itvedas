import React from 'react';
import { TableOfContents as TOCType } from '@types/article';
import clsx from 'clsx';

interface TableOfContentsProps {
  toc: TOCType;
  className?: string;
}

interface TOCItem {
  id: string;
  title: string;
  level: number;
  children?: TOCItem[];
}

function renderTOCItems(items: TOCItem[], baseLevel = 2): JSX.Element[] {
  return items.map((item) => (
    <React.Fragment key={item.id}>
      <li
        className={clsx(
          'mb-2 transition-colors hover:text-brand-600 dark:hover:text-brand-400',
          {
            'ml-0': item.level === baseLevel,
            'ml-4': item.level === baseLevel + 1,
            'ml-8': item.level === baseLevel + 2,
            'ml-12': item.level === baseLevel + 3,
          }
        )}
      >
        <a
          href={`#${item.id}`}
          className="text-neutral-700 dark:text-neutral-300 hover:text-brand-600 dark:hover:text-brand-400"
        >
          {item.title}
        </a>
      </li>
      {item.children && item.children.length > 0 && renderTOCItems(item.children, baseLevel)}
    </React.Fragment>
  ));
}

export function TableOfContents({ toc, className }: TableOfContentsProps): JSX.Element {
  return (
    <nav
      className={clsx(
        'bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-6',
        className
      )}
      aria-label="Table of contents"
    >
      <h2 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-neutral-100">
        On this page
      </h2>
      <ul className="text-sm space-y-1">
        {renderTOCItems(toc.items)}
      </ul>
    </nav>
  );
}
