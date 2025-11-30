import { useState, useEffect } from 'react';
import { useConfig } from '@/hooks/useSettings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SettingsAlert } from './shared/SettingsAlert';
import { SaveButton } from './shared/SaveButton';
import { useSettingsForm } from '../hooks/useSettingsForm';

export function ProcessingSettings() {
  const { data: config } = useConfig();
  const { saveMessage, handleSave, isPending } = useSettingsForm('processing');

  const [settings, setSettings] = useState({
    mode: 'realtime',
    polling_interval: 60,
    max_workers: 3,
  });

  useEffect(() => {
    if (config?.processing) {
      setSettings({
        mode: config.processing.mode || 'realtime',
        polling_interval: config.processing.polling_interval || 60,
        max_workers: config.processing.max_workers || 3,
      });
    }
  }, [config?.processing]);

  const onSave = () => {
    handleSave(settings, 'Processing configuration saved successfully');
  };

  const showPollingInterval = settings.mode === 'realtime' || settings.mode === 'batch';
  const showMaxWorkers = settings.mode === 'realtime' || settings.mode === 'batch';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Configuration</CardTitle>
        <CardDescription>Configure document processing behavior</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <SettingsAlert message={saveMessage} />

        <div className="space-y-2">
          <Label htmlFor="processing_mode">Processing Mode</Label>
          <Select
            value={settings.mode}
            onValueChange={(value) =>
              setSettings((prev) => ({ ...prev, mode: value }))
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
            {settings.mode === 'realtime' && 'Documents will be processed automatically as they arrive with continuous polling'}
            {settings.mode === 'batch' && 'Documents will be processed in batches at scheduled intervals'}
            {settings.mode === 'manual' && 'Documents will only be processed when you manually trigger processing'}
          </p>
        </div>

        {showPollingInterval && (
          <div className="space-y-2">
            <Label htmlFor="polling_interval">Polling Interval (seconds)</Label>
            <Input
              id="polling_interval"
              type="number"
              min="10"
              max="3600"
              value={settings.polling_interval}
              onChange={(e) =>
                setSettings((prev) => ({
                  ...prev,
                  polling_interval: parseInt(e.target.value) || 60,
                }))
              }
            />
            <p className="text-xs text-muted-foreground">
              {settings.mode === 'realtime'
                ? 'How often to check for new documents (10-3600 seconds)'
                : 'How often to run batch processing (10-3600 seconds)'}
            </p>
          </div>
        )}

        {showMaxWorkers && (
          <div className="space-y-2">
            <Label htmlFor="max_workers">Concurrent Workers</Label>
            <Input
              id="max_workers"
              type="number"
              min="1"
              max="10"
              value={settings.max_workers}
              onChange={(e) =>
                setSettings((prev) => ({
                  ...prev,
                  max_workers: parseInt(e.target.value) || 3,
                }))
              }
            />
            <p className="text-xs text-muted-foreground">
              {settings.mode === 'realtime'
                ? 'Maximum number of documents to process simultaneously (1-10)'
                : 'Number of documents to process in each batch (1-10)'}
            </p>
          </div>
        )}

        <SaveButton
          onClick={onSave}
          isPending={isPending}
          label="Save Processing Configuration"
        />
      </CardContent>
    </Card>
  );
}
