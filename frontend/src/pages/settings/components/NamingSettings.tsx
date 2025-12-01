import { useState, useEffect } from 'react';
import { useConfig } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCustom } from '@/components/ui/alert-custom';
import { SettingsAlert } from './shared/SettingsAlert';
import { SaveButton } from './shared/SaveButton';
import { TemplateInput } from './shared/TemplateInput';
import { useSettingsForm } from '../hooks/useSettingsForm';
import { Separator } from '@/components/ui/separator';

export function NamingSettings() {
  const { data: config } = useConfig();
  const { saveMessage, handleSave, isPending } = useSettingsForm('naming');

  const [settings, setSettings] = useState({
    default_template: '',
    title_template: '',
  });

  useEffect(() => {
    if (config?.naming) {
      setSettings({
        default_template: config.naming.default_template || '{date}_{correspondent}_{type}_{title}',
        title_template: config.naming.title_template || '{title}',
      });
    }
  }, [config?.naming]);

  const onSave = () => {
    handleSave(settings, 'Naming configuration saved successfully');
  };

  const filenameVariables = ['{date}', '{correspondent}', '{type}', '{title}', '{tags}'];
  const titleVariables = ['{date}', '{correspondent}', '{type}', '{title}'];

  const filenameExampleData = {
    date: '2025-01-15',
    correspondent: 'Acme Corp',
    type: 'Invoice',
    title: 'Monthly Service Bill',
    tags: 'finance, important',
  };

  const titleExampleData = {
    date: '2025-01-15',
    correspondent: 'Acme Corp',
    type: 'Invoice',
    title: 'Monthly Service Bill',
  };

  const filenameCommonTemplates = [
    '{date}_{correspondent}_{type}_{title}',
    '{correspondent}_{date}_{title}',
    '{type}_{date}_{correspondent}_{title}',
  ];

  const titleCommonTemplates = [
    '{title}',
    '{type} - {title}',
    '{correspondent} {type}',
    '{date} - {correspondent} - {title}',
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
          message="These templates guide the AI in generating document titles and filenames. While the AI is instructed to follow the templates, the actual output depends on the model's capabilities and may vary. Templates are applied as formatting rules after AI generation to ensure consistency."
        />

        <TemplateInput
          id="title_template"
          label="Document Title Template"
          value={settings.title_template}
          onChange={(value) => setSettings(prev => ({ ...prev, title_template: value }))}
          placeholder="{title}"
          availableVariables={titleVariables}
          exampleData={titleExampleData}
          commonTemplates={titleCommonTemplates}
          exampleDescription="Example document: Invoice from Acme Corp dated 2025-01-15"
        />

        <Separator className="my-6" />

        <AlertCustom
          variant="info"
          message={'The filename template automatically cleans special characters for filesystem compatibility. Problematic characters (/ \\ < > : " | ? *) are replaced with underscores. This does not apply to the document title.'}
        />

        <TemplateInput
          id="default_template"
          label="Document Filename Template"
          value={settings.default_template}
          onChange={(value) => setSettings(prev => ({ ...prev, default_template: value }))}
          placeholder="{date}_{correspondent}_{type}_{title}"
          availableVariables={filenameVariables}
          exampleData={filenameExampleData}
          commonTemplates={filenameCommonTemplates}
          exampleDescription="Example document: Invoice from Acme Corp dated 2025-01-15"
        />

        <SaveButton
          onClick={onSave}
          isPending={isPending}
          label="Save Templates"
        />
      </CardContent>
    </Card>
  );
}
