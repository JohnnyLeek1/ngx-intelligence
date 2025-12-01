import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

const variantStyles = {
  success: 'border-green-500 bg-green-50 dark:bg-green-950/50 text-green-900 dark:text-green-50',
  error: 'border-destructive/50 text-destructive dark:border-destructive bg-destructive/10',
  warning: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/50 text-yellow-900 dark:text-yellow-50',
  info: 'border-blue-500 bg-blue-50 dark:bg-blue-950/50 text-blue-900 dark:text-blue-50',
  default: 'border-border bg-background',
} as const;

const variantIconStyles = {
  success: 'text-green-600 dark:text-green-400',
  error: 'text-destructive',
  warning: 'text-yellow-600 dark:text-yellow-400',
  info: 'text-blue-600 dark:text-blue-400',
  default: 'text-foreground',
} as const;

const variantTextStyles = {
  success: 'text-green-800 dark:text-green-200',
  error: '',
  warning: 'text-yellow-800 dark:text-yellow-200',
  info: 'text-blue-800 dark:text-blue-200',
  default: '',
} as const;

const variantIcons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
  default: AlertCircle,
} as const;

export interface AlertCustomProps {
  variant?: 'success' | 'error' | 'warning' | 'info' | 'default';
  title?: string;
  message: string;
  className?: string;
}

export function AlertCustom({
  variant = 'default',
  title,
  message,
  className,
}: AlertCustomProps) {
  const Icon = variantIcons[variant];

  return (
    <Alert
      variant={variant === 'error' ? 'destructive' : 'default'}
      className={cn(
        variantStyles[variant],
        // Fix icon alignment - override default top-4 with top-3
        '[&>svg]:top-3',
        className
      )}
    >
      <Icon className={cn('h-4 w-4', variantIconStyles[variant])} />
      {title && (
        <AlertTitle className={variantTextStyles[variant]}>
          {title}
        </AlertTitle>
      )}
      <AlertDescription className={variantTextStyles[variant]}>
        {message}
      </AlertDescription>
    </Alert>
  );
}
