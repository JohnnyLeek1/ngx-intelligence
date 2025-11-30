import { useState } from 'react';
import { useUpdateConfig } from '@/hooks/useSettings';

export function useSettingsForm(section: string) {
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const updateConfig = useUpdateConfig();

  const handleSave = async (data: any, successMessage: string) => {
    try {
      setSaveMessage(null);
      await updateConfig.mutateAsync({ section, data });
      setSaveMessage({ type: 'success', text: successMessage });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage({
        type: 'error',
        text: `Failed to save ${section} configuration`
      });
    }
  };

  return {
    saveMessage,
    handleSave,
    isPending: updateConfig.isPending,
  };
}
