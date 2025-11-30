import { useState } from 'react';
import { useAtomValue } from 'jotai';
import { currentUserAtom } from '@/store/auth';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useConfig } from '@/hooks/useSettings';
import { GeneralSettings } from './components/GeneralSettings';
import { AISettings } from './components/AISettings';
import { ProcessingSettings } from './components/ProcessingSettings';
import { NamingSettings } from './components/NamingSettings';
import { SettingsLoadingSkeleton } from './components/shared/SettingsLoadingSkeleton';

export default function SettingsPage() {
  const currentUser = useAtomValue(currentUserAtom);
  const { isLoading } = useConfig();
  const [activeTab, setActiveTab] = useState('general');

  const isAdmin = currentUser?.role === 'admin';

  if (isLoading) {
    return <SettingsLoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and system configuration
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          {isAdmin && <TabsTrigger value="ai">AI Configuration</TabsTrigger>}
          {isAdmin && <TabsTrigger value="processing">Processing</TabsTrigger>}
          <TabsTrigger value="naming">Naming Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <GeneralSettings />
        </TabsContent>

        {isAdmin && (
          <TabsContent value="ai">
            <AISettings />
          </TabsContent>
        )}

        {isAdmin && (
          <TabsContent value="processing">
            <ProcessingSettings />
          </TabsContent>
        )}

        <TabsContent value="naming">
          <NamingSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
