import { useState, useEffect } from 'react';
import { useConfig } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { SettingsAlert } from './shared/SettingsAlert';
import { SaveButton } from './shared/SaveButton';
import { useSettingsForm } from '../hooks/useSettingsForm';

export function NamingSettings() {
  const { data: config } = useConfig();
  const { saveMessage, handleSave, isPending } = useSettingsForm('naming');

  const [settings, setSettings] = useState({
    title_template: '',
  });

  useEffect(() => {
    if (config?.naming) {
      setSettings({
        title_template: config.naming.title_template || '{date}_{correspondent}_{type}',
      });
    }
  }, [config?.naming]);

  const onSave = () => {
    handleSave(settings, 'Naming configuration saved successfully');
  };

  const generatePreview = (template: string) => {
    const exampleData = {
      date: '2025-01-15',
      correspondent: 'Acme Corp',
      type: 'Invoice',
      title: 'Monthly Service Bill',
      tags: 'finance, important',
    };

    let preview = template;
    Object.entries(exampleData).forEach(([key, value]) => {
      preview = preview.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
    });

    return preview || 'No template defined';
  };

  const commonTemplates = [
    '{date} {correspondent} {type}',
    '{correspondent} {date} {title}',
    '{type} {date} {correspondent}',
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Naming Templates</CardTitle>
        <CardDescription>Configure document naming templates</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <SettingsAlert message={saveMessage} />

        <div className="space-y-2">
          <Label htmlFor="title_template">Document Title Template</Label>
          <Input
            id="title_template"
            placeholder="{date} {correspondent} {type}"
            value={settings.title_template}
            onChange={(e) => setSettings(prev => ({ ...prev, title_template: e.target.value }))}
          />
          <p className="text-xs text-muted-foreground">
            Available variables: {'{date}'}, {'{correspondent}'}, {'{type}'}, {'{title}'}, {'{tags}'}
          </p>
        </div>

        <div className="rounded-md bg-muted p-4 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Preview</p>
            {settings.title_template && (
              <Badge variant="outline" className="text-xs">Live preview</Badge>
            )}
          </div>
          <p className="text-sm font-mono text-foreground break-all">
            {generatePreview(settings.title_template)}
          </p>
          <p className="text-xs text-muted-foreground">
            Example document: Invoice from Acme Corp dated 2025-01-15
          </p>
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-medium">Common Templates</Label>
          <div className="grid gap-2">
            {commonTemplates.map((template) => (
              <button
                key={template}
                type="button"
                className="text-left text-xs bg-muted hover:bg-muted/80 p-2 rounded-md transition-colors"
                onClick={() => setSettings(prev => ({ ...prev, title_template: template }))}
              >
                <code>{template}</code>
              </button>
            ))}
          </div>
        </div>

        <SaveButton
          onClick={onSave}
          isPending={isPending}
          label="Save Template"
        />
      </CardContent>
    </Card>
  );
}
