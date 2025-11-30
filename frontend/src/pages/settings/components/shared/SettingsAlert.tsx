import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SettingsAlertProps {
  message: { type: 'success' | 'error'; text: string } | null;
}

export function SettingsAlert({ message }: SettingsAlertProps) {
  if (!message) return null;

  return (
    <Alert
      variant={message.type === 'error' ? 'destructive' : 'default'}
      className={cn(
        "animate-in fade-in slide-in-from-top-2 duration-300",
        message.type === 'success' &&
        'border-green-500 bg-green-50 dark:bg-green-950/50 text-green-900 dark:text-green-50'
      )}
    >
      {message.type === 'success' ? (
        <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
      ) : (
        <AlertCircle className="h-4 w-4" />
      )}
      <AlertDescription
        className={cn(
          "!translate-y-0",
          message.type === 'success' && 'text-green-800 dark:text-green-200'
        )}
      >
        {message.text}
      </AlertDescription>
    </Alert>
  );
}
