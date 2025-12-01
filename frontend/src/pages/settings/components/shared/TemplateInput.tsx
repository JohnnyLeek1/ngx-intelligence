import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { AlertCustom } from '@/components/ui/alert-custom';

export interface TemplateInputProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  availableVariables: string[];
  exampleData: Record<string, string>;
  commonTemplates: string[];
  exampleDescription?: string;
}

export function TemplateInput({
  id,
  label,
  value,
  onChange,
  placeholder,
  availableVariables,
  exampleData,
  commonTemplates,
  exampleDescription,
}: TemplateInputProps) {
  const cleanTemplate = (template: string) => {
    // Mimic backend cleaning logic
    // Replace problematic characters: / \ < > : " | ? *
    let cleaned = template.replace(/[<>:"/\\|?*]/g, '_');

    // Replace multiple consecutive underscores with single underscore
    cleaned = cleaned.replace(/_{2,}/g, '_');

    // Remove leading/trailing underscores and spaces
    cleaned = cleaned.replace(/^[_ ]+|[_ ]+$/g, '');

    return cleaned;
  };

  const generatePreview = (template: string) => {
    let preview = template;
    Object.entries(exampleData).forEach(([key, value]) => {
      preview = preview.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
    });

    // Apply template cleaning to show final result
    preview = cleanTemplate(preview);

    return preview || 'No template defined';
  };

  const checkProblematicChars = (template: string) => {
    // Characters that will be replaced: / \ < > : " | ? *
    const replacedChars = /[<>:"/\\|?*]/g;
    const willBeReplaced = template.match(replacedChars);

    return { willBeReplaced };
  };

  const { willBeReplaced } = checkProblematicChars(value);

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <p className="text-xs text-muted-foreground">
        Available variables: {availableVariables.join(', ')}
      </p>

      {value && willBeReplaced && willBeReplaced.length > 0 && (
        <AlertCustom
          variant="warning"
          message={`The following characters will be replaced with underscores: ${[...new Set(willBeReplaced)].join(' ')}`}
        />
      )}

      <div className="rounded-md bg-muted p-4 space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">Preview</p>
          {value && (
            <Badge variant="outline" className="text-xs">Live preview</Badge>
          )}
        </div>
        <p className="text-sm font-mono text-foreground break-all">
          {generatePreview(value)}
        </p>
        {exampleDescription && (
          <p className="text-xs text-muted-foreground">
            {exampleDescription}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-medium">Common Templates</Label>
        <div className="grid gap-2">
          {commonTemplates.map((template) => (
            <button
              key={template}
              type="button"
              className="text-left text-xs bg-muted hover:bg-muted/80 p-2 rounded-md transition-colors"
              onClick={() => onChange(template)}
            >
              <code>{template}</code>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
