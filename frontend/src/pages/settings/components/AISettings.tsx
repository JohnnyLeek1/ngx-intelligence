import { useState, useEffect } from 'react';
import { useConfig, useAIModels } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle2 } from 'lucide-react';
import { SettingsAlert } from './shared/SettingsAlert';
import { SaveButton } from './shared/SaveButton';
import { useSettingsForm } from '../hooks/useSettingsForm';

export function AISettings() {
  const { data: config } = useConfig();
  const { data: modelsData } = useAIModels();
  const { saveMessage, handleSave, isPending } = useSettingsForm('ai');

  const [aiSettings, setAiSettings] = useState({
    model: '',
    temperature: 0.1,
    system_prompt: '',
    ollama_url: '',
  });

  useEffect(() => {
    if (config?.ai) {
      setAiSettings({
        model: config.ai.model || 'llama3.2:latest',
        temperature: config.ai.temperature || 0.1,
        system_prompt: config.ai.system_prompt || '',
        ollama_url: config.ai.ollama_url || '',
      });
    }
  }, [config?.ai]);

  const onSave = () => {
    handleSave(aiSettings, 'AI configuration saved successfully');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Configuration</CardTitle>
        <CardDescription>Configure AI model and processing parameters</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <SettingsAlert message={saveMessage} />

        <div className="space-y-2">
          <Label htmlFor="ai_model">AI Model</Label>
          <Select
            value={aiSettings.model}
            onValueChange={(value) =>
              setAiSettings((prev) => ({ ...prev, model: value }))
            }
          >
            <SelectTrigger id="ai_model">
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent>
              {modelsData?.models.map((model) => (
                <SelectItem key={model.name} value={model.name}>
                  <div className="flex items-center justify-between gap-2">
                    <span>{model.name}</span>
                    {!model.is_available && (
                      <Badge variant="outline" className="text-xs">
                        Not available
                      </Badge>
                    )}
                  </div>
                </SelectItem>
              )) || (
                <SelectItem value="llama3.2:latest">
                  llama3.2:latest
                </SelectItem>
              )}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Ollama model to use for document processing
          </p>
          {modelsData?.current_model && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <CheckCircle2 className="h-3 w-3 text-green-500" />
              <span>Currently using: {modelsData.current_model}</span>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="ollama_url">Ollama API URL</Label>
          <Input
            id="ollama_url"
            type="url"
            placeholder="http://localhost:11434"
            value={aiSettings.ollama_url || ''}
            onChange={(e) =>
              setAiSettings((prev) => ({ ...prev, ollama_url: e.target.value }))
            }
          />
          <p className="text-xs text-muted-foreground">
            URL of your Ollama API server. Default: http://localhost:11434
          </p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="temperature">Temperature</Label>
            <span className="text-sm font-medium">
              {aiSettings.temperature.toFixed(1)}
            </span>
          </div>
          <Slider
            id="temperature"
            value={[aiSettings.temperature]}
            onValueChange={(value) =>
              setAiSettings((prev) => ({ ...prev, temperature: value[0] }))
            }
            min={0}
            max={2}
            step={0.1}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            Controls randomness in AI responses. Lower values (0.1-0.5) are more
            focused and deterministic, higher values (1.0-2.0) are more creative
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="system_prompt">System Prompt</Label>
          <Textarea
            id="system_prompt"
            placeholder="Enter custom system prompt for document analysis..."
            className="min-h-[200px] font-mono text-sm"
            value={aiSettings.system_prompt}
            onChange={(e) =>
              setAiSettings((prev) => ({ ...prev, system_prompt: e.target.value }))
            }
          />
          <p className="text-xs text-muted-foreground">
            Custom instructions for the AI model when analyzing documents. Leave
            empty to use the default prompt.
          </p>
        </div>

        <SaveButton
          onClick={onSave}
          isPending={isPending}
          label="Save AI Configuration"
        />
      </CardContent>
    </Card>
  );
}
