import React from 'react';
import clsx from 'clsx';

type AlertVariant = 'info' | 'success' | 'warning' | 'danger';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  icon?: React.ReactNode;
}

const variantStyles: Record<AlertVariant, { bg: string; border: string; text: string; icon: string }> = {
  info: {
    bg: 'bg-blue-50 dark:bg-blue-950',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-800 dark:text-blue-200',
    icon: 'text-blue-600 dark:text-blue-400',
  },
  success: {
    bg: 'bg-green-50 dark:bg-green-950',
    border: 'border-green-200 dark:border-green-800',
    text: 'text-green-800 dark:text-green-200',
    icon: 'text-green-600 dark:text-green-400',
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-950',
    border: 'border-yellow-200 dark:border-yellow-800',
    text: 'text-yellow-800 dark:text-yellow-200',
    icon: 'text-yellow-600 dark:text-yellow-400',
  },
  danger: {
    bg: 'bg-red-50 dark:bg-red-950',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-800 dark:text-red-200',
    icon: 'text-red-600 dark:text-red-400',
  },
};

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    { className, variant = 'info', title, icon, children, ...props },
    ref
  ) => {
    const styles = variantStyles[variant];

    return (
      <div
        className={clsx(
          'rounded-lg border p-4',
          styles.bg,
          styles.border,
          styles.text,
          className
        )}
        role="alert"
        ref={ref}
        {...props}
      >
        <div className="flex gap-3">
          {icon && <div className={clsx('flex-shrink-0 mt-0.5', styles.icon)}>{icon}</div>}
          <div className="flex-1">
            {title && <h4 className="font-semibold mb-1">{title}</h4>}
            <div className="text-sm">{children}</div>
          </div>
        </div>
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export { Alert, type AlertProps };
