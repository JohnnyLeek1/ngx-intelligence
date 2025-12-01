import { useState, useEffect } from 'react';
import { useConfig } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { AlertCustom } from '@/components/ui/alert-custom';
import { SettingsAlert } from './shared/SettingsAlert';
import { SaveButton } from './shared/SaveButton';
import { useSettingsForm } from '../hooks/useSettingsForm';

export function NamingSettings() {
  const { data: config } = useConfig();
  const { saveMessage, handleSave, isPending } = useSettingsForm('naming');

  const [settings, setSettings] = useState({
    default_template: '',
  });

  useEffect(() => {
    if (config?.naming) {
      setSettings({
        default_template: config.naming.default_template || '{date}_{correspondent}_{type}_{title}',
      });
    }
  }, [config?.naming]);

  const onSave = () => {
    handleSave(settings, 'Naming configuration saved successfully');
  };

  const cleanFilename = (filename: string) => {
    // Mimic backend cleaning logic
    // Replace problematic characters: / \ < > : " | ? *
    let cleaned = filename.replace(/[<>:"/\\|?*]/g, '_');

    // Replace multiple consecutive underscores with single underscore
    cleaned = cleaned.replace(/_{2,}/g, '_');

    // Remove leading/trailing underscores and spaces
    cleaned = cleaned.replace(/^[_ ]+|[_ ]+$/g, '');

    return cleaned;
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

    // Apply filename cleaning to show final result
    preview = cleanFilename(preview);

    return preview || 'No template defined';
  };

  const checkProblematicChars = (template: string) => {
    // Characters that will be replaced: / \ < > : " | ? *
    const replacedChars = /[<>:"/\\|?*]/g;

    const willBeReplaced = template.match(replacedChars);

    return { willBeReplaced };
  };

  const commonTemplates = [
    '{date}_{correspondent}_{type}_{title}',
    '{correspondent}_{date}_{title}',
    '{type}_{date}_{correspondent}_{title}',
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Naming Templates</CardTitle>
        <CardDescription>Configure document naming templates</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <SettingsAlert message={saveMessage} />

        <AlertCustom
          variant="info"
          message={'Spaces and most punctuation are preserved in filenames. Only problematic characters (/ \\ < > : " | ? *) are replaced with underscores for filesystem compatibility.'}
        />

        <div className="space-y-2">
          <Label htmlFor="default_template">Document Filename Template</Label>
          <Input
            id="default_template"
            placeholder="{date}_{correspondent}_{type}_{title}"
            value={settings.default_template}
            onChange={(e) => setSettings(prev => ({ ...prev, default_template: e.target.value }))}
          />
          <p className="text-xs text-muted-foreground">
            Available variables: {'{date}'}, {'{correspondent}'}, {'{type}'}, {'{title}'}, {'{tags}'}
          </p>

          {settings.default_template && (() => {
            const { willBeReplaced } = checkProblematicChars(settings.default_template);

            return (
              <>
                {willBeReplaced && willBeReplaced.length > 0 && (
                  <AlertCustom
                    variant="warning"
                    message={`The following characters will be replaced with underscores: ${[...new Set(willBeReplaced)].join(' ')}`}
                  />
                )}
              </>
            );
          })()}
        </div>

        <div className="rounded-md bg-muted p-4 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Preview</p>
            {settings.default_template && (
              <Badge variant="outline" className="text-xs">Live preview</Badge>
            )}
          </div>
          <p className="text-sm font-mono text-foreground break-all">
            {generatePreview(settings.default_template)}
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
                onClick={() => setSettings(prev => ({ ...prev, default_template: template }))}
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
