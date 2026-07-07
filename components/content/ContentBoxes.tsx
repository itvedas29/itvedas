import React from 'react';
import clsx from 'clsx';

interface ContentBoxProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title?: string;
}

export function BestPractice({
  className,
  title,
  icon,
  children,
  ...props
}: ContentBoxProps): JSX.Element {
  return (
    <div
      className={clsx(
        'my-6 rounded-lg border-l-4 border-green-500 bg-green-50 p-4 dark:border-green-600 dark:bg-green-950',
        className
      )}
      {...props}
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          {icon || (
            <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          {title && <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">{title}</h4>}
          <div className="text-sm text-green-800 dark:text-green-200">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function CommonMistake({
  className,
  title,
  icon,
  children,
  ...props
}: ContentBoxProps): JSX.Element {
  return (
    <div
      className={clsx(
        'my-6 rounded-lg border-l-4 border-red-500 bg-red-50 p-4 dark:border-red-600 dark:bg-red-950',
        className
      )}
      {...props}
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          {icon || (
            <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 2.526a6 6 0 008.367 8.364m1.497 3.999a6 6 0 01-8.368-8.368m0 0L2 4m12 12l-2-2" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          {title && <h4 className="font-semibold text-red-900 dark:text-red-100 mb-2">{title}</h4>}
          <div className="text-sm text-red-800 dark:text-red-200">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function EnterpriseInsight({
  className,
  title,
  icon,
  children,
  ...props
}: ContentBoxProps): JSX.Element {
  return (
    <div
      className={clsx(
        'my-6 rounded-lg border-l-4 border-blue-500 bg-blue-50 p-4 dark:border-blue-600 dark:bg-blue-950',
        className
      )}
      {...props}
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          {icon || (
            <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 000 2H4a1 1 0 00-1 1v10a1 1 0 001 1h12a1 1 0 001-1V6a1 1 0 00-1-1h-2a1 1 0 000-2h2a2 2 0 012 2v10a2 2 0 01-2 2H6a2 2 0 01-2-2V5z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          {title && <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">{title}</h4>}
          <div className="text-sm text-blue-800 dark:text-blue-200">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function TipBox({
  className,
  title,
  icon,
  children,
  ...props
}: ContentBoxProps): JSX.Element {
  return (
    <div
      className={clsx(
        'my-6 rounded-lg border-l-4 border-yellow-500 bg-yellow-50 p-4 dark:border-yellow-600 dark:bg-yellow-950',
        className
      )}
      {...props}
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          {icon || (
            <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          {title && <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">{title}</h4>}
          <div className="text-sm text-yellow-800 dark:text-yellow-200">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function ImportantNote({
  className,
  title,
  icon,
  children,
  ...props
}: ContentBoxProps): JSX.Element {
  return (
    <div
      className={clsx(
        'my-6 rounded-lg border-l-4 border-orange-500 bg-orange-50 p-4 dark:border-orange-600 dark:bg-orange-950',
        className
      )}
      {...props}
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          {icon || (
            <svg className="w-6 h-6 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          {title && <h4 className="font-semibold text-orange-900 dark:text-orange-100 mb-2">{title}</h4>}
          <div className="text-sm text-orange-800 dark:text-orange-200">{children}</div>
        </div>
      </div>
    </div>
  );
}
