import React from 'react';
import clsx from 'clsx';

interface CodeBlockProps extends React.HTMLAttributes<HTMLPreElement> {
  language?: string;
  filename?: string;
  showLineNumbers?: boolean;
  highlight?: number[];
}

const CodeBlock = React.forwardRef<HTMLPreElement, CodeBlockProps>(
  (
    {
      className,
      children,
      language,
      filename,
      showLineNumbers = false,
      highlight = [],
      ...props
    },
    ref
  ) => {
    const lines = String(children).split('\n');

    return (
      <div className="my-4 rounded-lg border border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900 overflow-hidden">
        {filename && (
          <div className="px-4 py-2 bg-neutral-200 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-800 text-xs font-mono text-neutral-700 dark:text-neutral-300">
            {filename}
          </div>
        )}
        <pre
          ref={ref}
          className={clsx(
            'p-4 overflow-x-auto',
            className
          )}
          {...props}
        >
          <code className={`language-${language || 'text'}`}>
            {lines.map((line, idx) => (
              <div
                key={idx}
                className={clsx(
                  'font-mono text-sm leading-relaxed',
                  highlight.includes(idx + 1) &&
                    'bg-yellow-200 dark:bg-yellow-900 px-2 -mx-2'
                )}
              >
                {showLineNumbers && (
                  <span className="text-neutral-500 dark:text-neutral-400 mr-4 select-none">
                    {String(idx + 1).padStart(3, ' ')}
                  </span>
                )}
                {line}
              </div>
            ))}
          </code>
        </pre>
      </div>
    );
  }
);

CodeBlock.displayName = 'CodeBlock';

export { CodeBlock, type CodeBlockProps };
