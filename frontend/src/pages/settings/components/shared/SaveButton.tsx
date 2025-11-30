import { Button } from '@/components/ui/button';
import { Save } from 'lucide-react';

interface SaveButtonProps {
  onClick: () => void;
  isPending: boolean;
  label?: string;
}

export function SaveButton({ onClick, isPending, label = 'Save Configuration' }: SaveButtonProps) {
  return (
    <Button onClick={onClick} disabled={isPending}>
      <Save className="h-4 w-4 mr-2" />
      {isPending ? 'Saving...' : label}
    </Button>
  );
}
