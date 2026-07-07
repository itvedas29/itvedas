'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import clsx from 'clsx';
import Fuse from 'fuse.js';

interface SearchResult {
  slug: string;
  title: string;
  description: string;
  excerpt: string;
  category: string;
  tags: string[];
  keywords: string[];
  readingTime: number;
}

interface SearchIndex {
  version: number;
  timestamp: string;
  articles: SearchResult[];
}

export function SearchBar(): JSX.Element {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [fuse, setFuse] = useState<Fuse<SearchResult> | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load search index
  useEffect(() => {
    fetch('/search-index.json')
      .then((res) => res.json())
      .then((data: SearchIndex) => {
        const fuseInstance = new Fuse(data.articles, {
          keys: ['title', 'description', 'category', 'tags', 'keywords'],
          threshold: 0.3,
          minMatchCharLength: 2,
        });
        setFuse(fuseInstance);
      })
      .catch((err) => console.error('Failed to load search index:', err));
  }, []);

  // Handle search
  useEffect(() => {
    if (!fuse || query.length < 1) {
      setResults([]);
      return;
    }

    const searchResults = fuse.search(query).map((result) => result.item);
    setResults(searchResults.slice(0, 8)); // Limit to 8 results
  }, [query, fuse]);

  // Handle click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      }
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div ref={searchRef} className="relative w-full max-w-xl">
      {/* Search input */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          ref={inputRef}
          type="text"
          placeholder="Search articles... (⌘K)"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          className={clsx(
            'w-full pl-10 pr-4 py-2 rounded-lg border transition-colors',
            'bg-white dark:bg-neutral-900',
            'border-neutral-200 dark:border-neutral-800',
            'text-neutral-900 dark:text-neutral-100',
            'placeholder-neutral-400 dark:placeholder-neutral-500',
            'focus:outline-none focus:border-brand-500 dark:focus:border-brand-500'
          )}
        />
      </div>

      {/* Search results dropdown */}
      {isOpen && (query.length > 0 || results.length > 0) && (
        <div
          className={clsx(
            'absolute top-full left-0 right-0 mt-2 bg-white dark:bg-neutral-900',
            'border border-neutral-200 dark:border-neutral-800 rounded-lg shadow-lg',
            'max-h-96 overflow-y-auto z-50'
          )}
        >
          {results.length > 0 ? (
            <div className="divide-y divide-neutral-200 dark:divide-neutral-800">
              {results.map((result) => (
                <Link
                  key={result.slug}
                  href={`/knowledge/${result.slug}`}
                  onClick={() => {
                    setQuery('');
                    setIsOpen(false);
                  }}
                  className={clsx(
                    'block p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800',
                    'transition-colors border-0'
                  )}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h4 className="font-semibold text-neutral-900 dark:text-neutral-100">
                      {result.title}
                    </h4>
                    <span className="text-xs text-neutral-500 dark:text-neutral-400 whitespace-nowrap">
                      {result.readingTime} min
                    </span>
                  </div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
                    {result.excerpt}
                  </p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded">
                      {result.category}
                    </span>
                    {result.tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-2 py-1 bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </Link>
              ))}
            </div>
          ) : query.length > 0 ? (
            <div className="p-8 text-center text-neutral-500 dark:text-neutral-400">
              <p>No articles found for "{query}"</p>
              <p className="text-sm mt-2">Try different keywords or browse by category</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
