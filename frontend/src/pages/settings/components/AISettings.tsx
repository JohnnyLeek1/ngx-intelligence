import { useState, useEffect } from 'react';
import { useConfig, useAIModels } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCustom } from '@/components/ui/alert-custom';
import { CheckCircle2, RefreshCw, Download, Star } from 'lucide-react';
import { SettingsAlert } from './shared/SettingsAlert';
import { SaveButton } from './shared/SaveButton';
import { ModelPullHelpDialog } from './ModelPullHelpDialog';
import { useSettingsForm } from '../hooks/useSettingsForm';
import type { AIModelResponse } from '@/types';

// Recommended models for document processing tasks
const RECOMMENDED_MODELS = [
  {
    name: 'llama3.2:3b',
    description: 'Fast, good for simple tasks',
    priority: 1,
  },
  {
    name: 'llama3.1:8b',
    description: 'Better quality, balanced performance',
    priority: 2,
  },
  {
    name: 'mistral:7b',
    description: 'Excellent at instruction following',
    priority: 3,
  },
  {
    name: 'qwen2.5:7b',
    description: 'Strong reasoning capabilities',
    priority: 4,
  },
  {
    name: 'gemma2:9b',
    description: 'Good balance of speed and quality',
    priority: 5,
  },
] as const;

interface EnhancedModel extends AIModelResponse {
  isRecommended: boolean;
  description?: string;
  priority?: number;
}

export function AISettings() {
  const { data: config } = useConfig();
  const { data: modelsData, refetch: refetchModels, isRefetching, error: modelsError } = useAIModels();
  const { saveMessage, handleSave, isPending } = useSettingsForm('ai');

  const [aiSettings, setAiSettings] = useState({
    model: '',
    temperature: 0.1,
    system_prompt: '',
    ollama_url: '',
  });
  const [refreshError, setRefreshError] = useState<string | null>(null);

  // Merge available models with recommended models
  const enhancedModels: EnhancedModel[] = (() => {
    const availableModels = modelsData?.models || [];
    const modelMap = new Map<string, EnhancedModel>();

    // Add all available models
    availableModels.forEach((model) => {
      const recommendedModel = RECOMMENDED_MODELS.find((rm) => rm.name === model.name);
      modelMap.set(model.name, {
        ...model,
        isRecommended: !!recommendedModel,
        description: recommendedModel?.description,
        priority: recommendedModel?.priority,
      });
    });

    // Add recommended models that are not yet available
    RECOMMENDED_MODELS.forEach((recModel) => {
      if (!modelMap.has(recModel.name)) {
        modelMap.set(recModel.name, {
          name: recModel.name,
          is_available: false,
          isRecommended: true,
          description: recModel.description,
          priority: recModel.priority,
        });
      }
    });

    // Sort: available recommended first, then other available, then unavailable recommended
    return Array.from(modelMap.values()).sort((a, b) => {
      if (a.is_available && !b.is_available) return -1;
      if (!a.is_available && b.is_available) return 1;
      if (a.isRecommended && !b.isRecommended) return -1;
      if (!a.isRecommended && b.isRecommended) return 1;
      if (a.priority && b.priority) return a.priority - b.priority;
      return a.name.localeCompare(b.name);
    });
  })();

  // Smart default selection - only run when config or models data changes
  useEffect(() => {
    if (config?.ai) {
      const configuredModel = config.ai.model || '';
      const availableModels = modelsData?.models || [];

      // Check if configured model is available
      const isConfiguredModelAvailable = availableModels.some(
        (m) => m.name === configuredModel && m.is_available
      );

      let defaultModel = configuredModel;

      // If configured model is not available, select first available model
      if (!isConfiguredModelAvailable && availableModels.length > 0) {
        // Prioritize recommended models
        const firstAvailableRecommended = availableModels.find(
          (m) => {
            const recommendedModel = RECOMMENDED_MODELS.find((rm) => rm.name === m.name);
            return m.is_available && !!recommendedModel;
          }
        );
        const firstAvailable = availableModels.find((m) => m.is_available);

        defaultModel = firstAvailableRecommended?.name || firstAvailable?.name || configuredModel;
      }

      setAiSettings({
        model: defaultModel,
        temperature: config.ai.temperature || 0.1,
        system_prompt: config.ai.system_prompt || '',
        ollama_url: config.ai.ollama_url || '',
      });
    }
  }, [config?.ai, modelsData]);

  const handleRefreshModels = async () => {
    setRefreshError(null);
    try {
      await refetchModels();
    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : 'Failed to refresh models. Please try again.';
      setRefreshError(errorMessage);
    }
  };

  const onSave = () => {
    handleSave(aiSettings, 'AI configuration saved successfully');
  };

  // Format error messages for better user experience
  const getErrorMessage = (error: any): string => {
    if (!error) return '';

    const message = error?.message || String(error);

    if (message.includes('ECONNREFUSED') || message.includes('Network Error') || message.includes('503')) {
      return 'Cannot connect to Ollama. Ensure Ollama is running at the configured URL.';
    }

    if (message.includes('404')) {
      return 'Ollama API endpoint not found. Please check your Ollama URL configuration.';
    }

    return message || 'Failed to fetch models from Ollama.';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Configuration</CardTitle>
        <CardDescription>Configure AI model and processing parameters</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <SettingsAlert message={saveMessage} />

        {/* Error Alert for Model Fetching */}
        {(modelsError || refreshError) && (
          <AlertCustom
            variant="error"
            message={getErrorMessage(refreshError || modelsError)}
          />
        )}

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Label htmlFor="ai_model">AI Model</Label>
              <ModelPullHelpDialog recommendedModels={RECOMMENDED_MODELS} />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshModels}
              disabled={isRefetching}
              className="h-8"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
              {isRefetching ? 'Refreshing...' : 'Refresh Models'}
            </Button>
          </div>

          <Select
            value={aiSettings.model}
            onValueChange={(value) =>
              setAiSettings((prev) => ({ ...prev, model: value }))
            }
          >
            <SelectTrigger id="ai_model" className="[&>span]:w-full [&>span]:block">
              <SelectValue placeholder="Select a model">
                {aiSettings.model && (() => {
                  const selectedModel = enhancedModels.find(m => m.name === aiSettings.model);
                  if (!selectedModel) return aiSettings.model;
                  return (
                    <div className="grid grid-cols-[1fr_auto] gap-x-4 items-center">
                      <span className="font-medium text-sm text-left">{selectedModel.name}</span>
                      <div className="flex items-center gap-2 justify-end">
                        {selectedModel.size && (
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {selectedModel.size}
                          </span>
                        )}
                        {selectedModel.isRecommended && (
                          <Badge variant="default" className="text-xs h-5 px-1.5 whitespace-nowrap">
                            <Star className="h-3 w-3 mr-1" />
                            Recommended
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </SelectValue>
            </SelectTrigger>
            <SelectContent className="max-h-[400px] w-full min-w-[500px]">
              {enhancedModels.length > 0 ? (
                enhancedModels.map((model) => (
                  <SelectItem
                    key={model.name}
                    value={model.name}
                    disabled={!model.is_available}
                    className="py-3 w-full [&>span]:block [&>span]:w-[calc(100%-2rem)] [&>span]:ml-auto"
                  >
                    <div className="grid grid-cols-[1fr_auto] gap-x-4">
                      {/* Top row: Model name on left */}
                      <span className="font-medium text-sm">{model.name}</span>

                      {/* Top row: Size and badges on right */}
                      <div className="flex items-center gap-2 justify-end">
                        {model.size && (
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {model.size}
                          </span>
                        )}
                        {model.isRecommended && (
                          <Badge variant="default" className="text-xs h-5 px-1.5 whitespace-nowrap">
                            <Star className="h-3 w-3 mr-1" />
                            Recommended
                          </Badge>
                        )}
                        {!model.is_available && (
                          <Badge variant="warning" className="text-xs h-5 px-1.5 whitespace-nowrap">
                            <Download className="h-3 w-3 mr-1" />
                            Pull Required
                          </Badge>
                        )}
                      </div>

                      {/* Bottom row: Description spanning full width */}
                      {model.description && (
                        <p className="text-xs text-muted-foreground leading-relaxed col-span-2">
                          {model.description}
                        </p>
                      )}
                    </div>
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="no-models" disabled>
                  No models available
                </SelectItem>
              )}
            </SelectContent>
          </Select>

          <p className="text-xs text-muted-foreground">
            Ollama model to use for document processing tasks. Recommended models are
            optimized for describing documents, extracting correspondents, creating titles,
            and tagging.
          </p>

          {modelsData?.current_model && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <CheckCircle2 className="h-3 w-3 text-green-500" />
              <span>Currently using: {modelsData.current_model}</span>
            </div>
          )}

          {enhancedModels.length === 0 && !modelsError && !refreshError && (
            <AlertCustom
              variant="info"
              message="No models found. Make sure Ollama is running and has models installed. Run 'ollama pull llama3.2:3b' to get started."
            />
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
