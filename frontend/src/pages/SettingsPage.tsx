import { useState, useEffect } from 'react';
import { useAtomValue } from 'jotai';
import { currentUserAtom } from '@/store/auth';
import { useConfig, useUpdateConfig, useAIModels } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Save, AlertCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const currentUser = useAtomValue(currentUserAtom);
  const { data: config, isLoading } = useConfig();
  const { data: modelsData } = useAIModels();
  const updateConfig = useUpdateConfig();
  const [activeTab, setActiveTab] = useState('general');
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Password change state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
  });
  const [passwordMessage, setPasswordMessage] = useState('');

  // AI settings state
  const [aiSettings, setAiSettings] = useState({
    model: '',
    temperature: 0.1,
    system_prompt: '',
    ollama_url: '',
  });

  // Processing settings state
  const [processingSettings, setProcessingSettings] = useState({
    mode: 'realtime',
    polling_interval: 60,
    max_workers: 3,
  });

  // Initialize form values from config
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

  useEffect(() => {
    if (config?.processing) {
      setProcessingSettings({
        mode: config.processing.mode || 'realtime',
        polling_interval: config.processing.polling_interval || 60,
        max_workers: config.processing.max_workers || 3,
      });
    }
  }, [config?.processing]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage('');
    // This would use useChangePassword hook
    setPasswordMessage('Password change functionality pending');
  };

  const handleSaveAISettings = async () => {
    try {
      setSaveMessage(null);
      await updateConfig.mutateAsync({
        section: 'ai',
        data: aiSettings,
      });
      setSaveMessage({ type: 'success', text: 'AI configuration saved successfully' });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage({ type: 'error', text: 'Failed to save AI configuration' });
    }
  };

  const handleSaveProcessingSettings = async () => {
    try {
      setSaveMessage(null);
      await updateConfig.mutateAsync({
        section: 'processing',
        data: processingSettings,
      });
      setSaveMessage({ type: 'success', text: 'Processing configuration saved successfully' });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      setSaveMessage({ type: 'error', text: 'Failed to save processing configuration' });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-96 mt-2" />
        </div>
        <Skeleton className="h-12 w-full" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-full" />
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const isAdmin = currentUser?.role === 'admin';

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

        {/* General Tab */}
        <TabsContent value="general">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>User Profile</CardTitle>
                <CardDescription>View and update your profile information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Username</Label>
                    <Input value={currentUser?.username || ''} disabled />
                  </div>
                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={currentUser?.email || ''}
                      placeholder="your.email@example.com"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <div>
                    <Badge variant={isAdmin ? 'default' : 'secondary'}>
                      {currentUser?.role || 'user'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>Update your account password</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordChange} className="space-y-4">
                  {passwordMessage && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{passwordMessage}</AlertDescription>
                    </Alert>
                  )}
                  <div className="space-y-2">
                    <Label htmlFor="current_password">Current Password</Label>
                    <Input
                      id="current_password"
                      type="password"
                      value={passwordData.current_password}
                      onChange={(e) =>
                        setPasswordData(prev => ({ ...prev, current_password: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="new_password">New Password</Label>
                    <Input
                      id="new_password"
                      type="password"
                      value={passwordData.new_password}
                      onChange={(e) =>
                        setPasswordData(prev => ({ ...prev, new_password: e.target.value }))
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Must be at least 8 characters with uppercase, lowercase, and digit
                    </p>
                  </div>
                  <Button type="submit">
                    <Save className="h-4 w-4 mr-2" />
                    Update Password
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Paperless-ngx Credentials</CardTitle>
                <CardDescription>Update your Paperless-ngx connection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Paperless URL</Label>
                  <Input value={currentUser?.paperless_url || ''} />
                </div>
                <div className="space-y-2">
                  <Label>Paperless Username</Label>
                  <Input value={currentUser?.paperless_username || ''} />
                </div>
                <div className="space-y-2">
                  <Label>Paperless Auth Token</Label>
                  <Input type="password" placeholder="••••••••••••" />
                </div>
                <Button>
                  <Save className="h-4 w-4 mr-2" />
                  Update Credentials
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Configuration Tab (Admin Only) */}
        {isAdmin && (
          <TabsContent value="ai">
            <Card>
              <CardHeader>
                <CardTitle>AI Configuration</CardTitle>
                <CardDescription>
                  Configure AI model and processing parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {saveMessage && (
                  <Alert
                    variant={saveMessage.type === 'error' ? 'destructive' : 'default'}
                    className={cn(
                      "animate-in fade-in slide-in-from-top-2 duration-300",
                      saveMessage.type === 'success' &&
                      'border-green-500 bg-green-50 dark:bg-green-950/50 text-green-900 dark:text-green-50'
                    )}
                  >
                    {saveMessage.type === 'success' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    <AlertDescription
                      className={cn(
                        "!translate-y-0",
                        saveMessage.type === 'success' && 'text-green-800 dark:text-green-200'
                      )}
                    >
                      {saveMessage.text}
                    </AlertDescription>
                  </Alert>
                )}
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

                <div className="flex items-center gap-2">
                  <Button
                    onClick={handleSaveAISettings}
                    disabled={updateConfig.isPending}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {updateConfig.isPending ? 'Saving...' : 'Save AI Configuration'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Processing Tab (Admin Only) */}
        {isAdmin && (
          <TabsContent value="processing">
            <Card>
              <CardHeader>
                <CardTitle>Processing Configuration</CardTitle>
                <CardDescription>
                  Configure document processing behavior
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {saveMessage && (
                  <Alert
                    variant={saveMessage.type === 'error' ? 'destructive' : 'default'}
                    className={cn(
                      "animate-in fade-in slide-in-from-top-2 duration-300",
                      saveMessage.type === 'success' &&
                      'border-green-500 bg-green-50 dark:bg-green-950/50 text-green-900 dark:text-green-50'
                    )}
                  >
                    {saveMessage.type === 'success' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    <AlertDescription
                      className={cn(
                        "!translate-y-0",
                        saveMessage.type === 'success' && 'text-green-800 dark:text-green-200'
                      )}
                    >
                      {saveMessage.text}
                    </AlertDescription>
                  </Alert>
                )}
                <div className="space-y-2">
                  <Label htmlFor="processing_mode">Processing Mode</Label>
                  <Select
                    value={processingSettings.mode}
                    onValueChange={(value) =>
                      setProcessingSettings((prev) => ({ ...prev, mode: value }))
                    }
                  >
                    <SelectTrigger id="processing_mode">
                      <SelectValue placeholder="Select processing mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="realtime">
                        <div className="flex flex-col items-start">
                          <span className="font-medium">Real-time</span>
                          <span className="text-xs text-muted-foreground">
                            Process documents immediately as they arrive
                          </span>
                        </div>
                      </SelectItem>
                      <SelectItem value="batch">
                        <div className="flex flex-col items-start">
                          <span className="font-medium">Batch</span>
                          <span className="text-xs text-muted-foreground">
                            Process multiple documents at scheduled intervals
                          </span>
                        </div>
                      </SelectItem>
                      <SelectItem value="manual">
                        <div className="flex flex-col items-start">
                          <span className="font-medium">Manual</span>
                          <span className="text-xs text-muted-foreground">
                            Only process when manually triggered
                          </span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    {processingSettings.mode === 'realtime' && 'Documents will be processed automatically as they arrive with continuous polling'}
                    {processingSettings.mode === 'batch' && 'Documents will be processed in batches at scheduled intervals'}
                    {processingSettings.mode === 'manual' && 'Documents will only be processed when you manually trigger processing'}
                  </p>
                </div>

                {/* Only show polling interval for realtime and batch modes */}
                {(processingSettings.mode === 'realtime' || processingSettings.mode === 'batch') && (
                  <div className="space-y-2">
                    <Label htmlFor="polling_interval">Polling Interval (seconds)</Label>
                    <Input
                      id="polling_interval"
                      type="number"
                      min="10"
                      max="3600"
                      value={processingSettings.polling_interval}
                      onChange={(e) =>
                        setProcessingSettings((prev) => ({
                          ...prev,
                          polling_interval: parseInt(e.target.value) || 60,
                        }))
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      {processingSettings.mode === 'realtime'
                        ? 'How often to check for new documents (10-3600 seconds)'
                        : 'How often to run batch processing (10-3600 seconds)'}
                    </p>
                  </div>
                )}

                {/* Only show concurrent workers for realtime and batch modes */}
                {(processingSettings.mode === 'realtime' || processingSettings.mode === 'batch') && (
                  <div className="space-y-2">
                    <Label htmlFor="max_workers">Concurrent Workers</Label>
                    <Input
                      id="max_workers"
                      type="number"
                      min="1"
                      max="10"
                      value={processingSettings.max_workers}
                      onChange={(e) =>
                        setProcessingSettings((prev) => ({
                          ...prev,
                          max_workers: parseInt(e.target.value) || 3,
                        }))
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      {processingSettings.mode === 'realtime'
                        ? 'Maximum number of documents to process simultaneously (1-10)'
                        : 'Number of documents to process in each batch (1-10)'}
                    </p>
                  </div>
                )}

                <Button
                  onClick={handleSaveProcessingSettings}
                  disabled={updateConfig.isPending}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {updateConfig.isPending ? 'Saving...' : 'Save Processing Configuration'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Naming Templates Tab */}
        <TabsContent value="naming">
          <Card>
            <CardHeader>
              <CardTitle>Naming Templates</CardTitle>
              <CardDescription>
                Configure document naming templates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Document Title Template</Label>
                <Input
                  placeholder="{date} - {correspondent} - {type}"
                  defaultValue={config?.naming?.title_template || ''}
                />
                <p className="text-xs text-muted-foreground">
                  Available variables: date, correspondent, type, tags
                </p>
              </div>
              <div className="rounded-md bg-muted p-4">
                <p className="text-sm font-medium mb-2">Preview</p>
                <p className="text-sm text-muted-foreground">
                  2025-01-15 - Acme Corp - Invoice
                </p>
              </div>
              <Button>
                <Save className="h-4 w-4 mr-2" />
                Save Template
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
