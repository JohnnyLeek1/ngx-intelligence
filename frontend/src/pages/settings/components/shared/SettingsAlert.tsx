import { AlertCustom } from '@/components/ui/alert-custom';

interface SettingsAlertProps {
  message: { type: 'success' | 'error'; text: string } | null;
}

export function SettingsAlert({ message }: SettingsAlertProps) {
  if (!message) return null;

  return (
    <AlertCustom
      variant={message.type}
      message={message.text}
      className="animate-in fade-in slide-in-from-top-2 duration-300"
    />
  );
}
