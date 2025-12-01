import { useState, useEffect } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import { currentUserAtom } from '@/store/auth';
import { authApi } from '@/api/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { AlertCustom } from '@/components/ui/alert-custom';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Save, Loader2, Globe, Clock } from 'lucide-react';

const COMMON_TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)', region: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time', region: 'North America' },
  { value: 'America/Chicago', label: 'Central Time', region: 'North America' },
  { value: 'America/Denver', label: 'Mountain Time', region: 'North America' },
  { value: 'America/Los_Angeles', label: 'Pacific Time', region: 'North America' },
  { value: 'America/Anchorage', label: 'Alaska Time', region: 'North America' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time', region: 'North America' },
  { value: 'America/Phoenix', label: 'Arizona Time', region: 'North America' },
  { value: 'America/Toronto', label: 'Toronto', region: 'North America' },
  { value: 'America/Vancouver', label: 'Vancouver', region: 'North America' },
  { value: 'America/Mexico_City', label: 'Mexico City', region: 'North America' },
  { value: 'Europe/London', label: 'London', region: 'Europe' },
  { value: 'Europe/Paris', label: 'Paris', region: 'Europe' },
  { value: 'Europe/Berlin', label: 'Berlin', region: 'Europe' },
  { value: 'Europe/Rome', label: 'Rome', region: 'Europe' },
  { value: 'Europe/Madrid', label: 'Madrid', region: 'Europe' },
  { value: 'Europe/Amsterdam', label: 'Amsterdam', region: 'Europe' },
  { value: 'Europe/Brussels', label: 'Brussels', region: 'Europe' },
  { value: 'Europe/Vienna', label: 'Vienna', region: 'Europe' },
  { value: 'Europe/Stockholm', label: 'Stockholm', region: 'Europe' },
  { value: 'Europe/Athens', label: 'Athens', region: 'Europe' },
  { value: 'Europe/Moscow', label: 'Moscow', region: 'Europe' },
  { value: 'Asia/Dubai', label: 'Dubai', region: 'Asia' },
  { value: 'Asia/Kolkata', label: 'India', region: 'Asia' },
  { value: 'Asia/Shanghai', label: 'Shanghai', region: 'Asia' },
  { value: 'Asia/Tokyo', label: 'Tokyo', region: 'Asia' },
  { value: 'Asia/Hong_Kong', label: 'Hong Kong', region: 'Asia' },
  { value: 'Asia/Singapore', label: 'Singapore', region: 'Asia' },
  { value: 'Asia/Seoul', label: 'Seoul', region: 'Asia' },
  { value: 'Asia/Bangkok', label: 'Bangkok', region: 'Asia' },
  { value: 'Australia/Sydney', label: 'Sydney', region: 'Australia/Pacific' },
  { value: 'Australia/Melbourne', label: 'Melbourne', region: 'Australia/Pacific' },
  { value: 'Australia/Brisbane', label: 'Brisbane', region: 'Australia/Pacific' },
  { value: 'Australia/Perth', label: 'Perth', region: 'Australia/Pacific' },
  { value: 'Pacific/Auckland', label: 'Auckland', region: 'Australia/Pacific' },
  { value: 'America/Sao_Paulo', label: 'São Paulo', region: 'South America' },
  { value: 'America/Buenos_Aires', label: 'Buenos Aires', region: 'South America' },
  { value: 'Africa/Johannesburg', label: 'Johannesburg', region: 'Africa' },
  { value: 'Africa/Cairo', label: 'Cairo', region: 'Africa' },
];

function getTimezoneOffset(timezone: string): string {
  try {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      timeZoneName: 'shortOffset',
    });
    const parts = formatter.formatToParts(now);
    const offsetPart = parts.find(part => part.type === 'timeZoneName');
    return offsetPart?.value || '';
  } catch {
    return '';
  }
}

function getBrowserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return 'UTC';
  }
}

export function GeneralSettings() {
  const currentUser = useAtomValue(currentUserAtom);
  const setCurrentUser = useSetAtom(currentUserAtom);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
  });
  const [passwordMessage, setPasswordMessage] = useState('');

  const [paperlessData, setPaperlessData] = useState({
    paperless_url: currentUser?.paperless_url || '',
    paperless_username: currentUser?.paperless_username || '',
    paperless_token: '',
  });
  const [paperlessMessage, setPaperlessMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isSavingPaperless, setIsSavingPaperless] = useState(false);

  const [timezoneData, setTimezoneData] = useState({
    timezone: currentUser?.timezone || getBrowserTimezone(),
  });
  const [timezoneMessage, setTimezoneMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isSavingTimezone, setIsSavingTimezone] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  const browserTimezone = getBrowserTimezone();

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Initialize timezone from user data
  useEffect(() => {
    if (currentUser?.timezone) {
      setTimezoneData({ timezone: currentUser.timezone });
    }
  }, [currentUser?.timezone]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage('');
    // This would use useChangePassword hook
    setPasswordMessage('Password change functionality pending');
  };

  const handlePaperlessCredentialsUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setPaperlessMessage(null);
    setIsSavingPaperless(true);

    try {
      const response = await authApi.updatePaperlessCredentials(paperlessData);

      // Update the current user data
      const updatedUser = await authApi.getCurrentUser();
      setCurrentUser(updatedUser);

      // Clear the token field for security
      setPaperlessData(prev => ({ ...prev, paperless_token: '' }));

      // Show success message
      setPaperlessMessage({ type: 'success', text: response.message || 'Credentials updated successfully' });

      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setPaperlessMessage(null);
      }, 3000);
    } catch (error: any) {
      // Handle different error response formats
      let errorMessage = 'Failed to update credentials. Please try again.';

      const detail = error.response?.data?.detail;
      if (detail) {
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          // Pydantic validation errors
          errorMessage = detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
        } else if (typeof detail === 'object') {
          errorMessage = detail.message || detail.error || JSON.stringify(detail);
        }
      }

      setPaperlessMessage({ type: 'error', text: errorMessage });
    } finally {
      setIsSavingPaperless(false);
    }
  };

  const handleTimezoneUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setTimezoneMessage(null);
    setIsSavingTimezone(true);

    try {
      await authApi.updateUser({ timezone: timezoneData.timezone });

      // Update the current user data
      const updatedUser = await authApi.getCurrentUser();
      setCurrentUser(updatedUser);

      // Show success message
      setTimezoneMessage({ type: 'success', text: 'Timezone updated successfully' });

      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setTimezoneMessage(null);
      }, 3000);
    } catch (error: any) {
      let errorMessage = 'Failed to update timezone. Please try again.';

      const detail = error.response?.data?.detail;
      if (detail) {
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
        } else if (typeof detail === 'object') {
          errorMessage = detail.message || detail.error || JSON.stringify(detail);
        }
      }

      setTimezoneMessage({ type: 'error', text: errorMessage });
    } finally {
      setIsSavingTimezone(false);
    }
  };

  const handleDetectTimezone = () => {
    setTimezoneData({ timezone: browserTimezone });
  };

  const isAdmin = currentUser?.role === 'admin';

  return (
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
                readOnly
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
          <CardTitle>Timezone Preferences</CardTitle>
          <CardDescription>Set your local timezone for daily statistics and date calculations</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleTimezoneUpdate} className="space-y-4">
            {timezoneMessage && (
              <AlertCustom
                variant={timezoneMessage.type}
                message={timezoneMessage.text}
              />
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="timezone">Timezone</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleDetectTimezone}
                  className="h-8"
                >
                  <Globe className="h-4 w-4 mr-2" />
                  Auto-Detect
                </Button>
              </div>

              <Select
                value={timezoneData.timezone}
                onValueChange={(value) => setTimezoneData({ timezone: value })}
              >
                <SelectTrigger id="timezone">
                  <SelectValue placeholder="Select timezone">
                    {timezoneData.timezone && (() => {
                      const selectedTz = COMMON_TIMEZONES.find(tz => tz.value === timezoneData.timezone);
                      const offset = getTimezoneOffset(timezoneData.timezone);
                      return (
                        <div className="flex items-center justify-between w-full">
                          <span>{selectedTz?.label || timezoneData.timezone}</span>
                          {offset && <span className="text-muted-foreground text-sm">{offset}</span>}
                        </div>
                      );
                    })()}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="max-h-[400px]">
                  {(() => {
                    const groupedTimezones = COMMON_TIMEZONES.reduce((acc, tz) => {
                      if (!acc[tz.region]) {
                        acc[tz.region] = [];
                      }
                      acc[tz.region].push(tz);
                      return acc;
                    }, {} as Record<string, typeof COMMON_TIMEZONES>);

                    return Object.entries(groupedTimezones).map(([region, timezones]) => (
                      <div key={region}>
                        <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                          {region}
                        </div>
                        {timezones.map((tz) => {
                          const offset = getTimezoneOffset(tz.value);
                          return (
                            <SelectItem key={tz.value} value={tz.value} className="pl-4">
                              <div className="flex items-center justify-between w-full">
                                <span>{tz.label}</span>
                                {offset && <span className="text-muted-foreground text-sm ml-2">{offset}</span>}
                              </div>
                            </SelectItem>
                          );
                        })}
                      </div>
                    ));
                  })()}
                </SelectContent>
              </Select>

              {browserTimezone && browserTimezone !== timezoneData.timezone && (
                <p className="text-xs text-muted-foreground">
                  <Globe className="h-3 w-3 inline mr-1" />
                  Browser detected: {browserTimezone}
                </p>
              )}

              <p className="text-sm text-muted-foreground">
                Your daily statistics will reset at midnight in your selected timezone
              </p>
            </div>

            {/* Current Time Display */}
            <div className="rounded-lg border bg-muted/50 p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Clock className="h-4 w-4" />
                <span>Current Time in Selected Timezone</span>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-semibold tabular-nums">
                  {currentTime.toLocaleTimeString('en-US', {
                    timeZone: timezoneData.timezone,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </div>
                <div className="text-sm text-muted-foreground">
                  {currentTime.toLocaleDateString('en-US', {
                    timeZone: timezoneData.timezone,
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </div>
              </div>
            </div>

            <Button type="submit" disabled={isSavingTimezone}>
              {isSavingTimezone ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Update Timezone
                </>
              )}
            </Button>
          </form>
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
              <AlertCustom
                variant="info"
                message={passwordMessage}
              />
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
        <CardContent>
          <form onSubmit={handlePaperlessCredentialsUpdate} className="space-y-4">
            {paperlessMessage && (
              <AlertCustom
                variant={paperlessMessage.type}
                message={paperlessMessage.text}
              />
            )}
            <div className="space-y-2">
              <Label htmlFor="paperless_url">Paperless URL</Label>
              <Input
                id="paperless_url"
                type="url"
                value={paperlessData.paperless_url}
                onChange={(e) => setPaperlessData(prev => ({ ...prev, paperless_url: e.target.value }))}
                placeholder="https://paperless.example.com"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="paperless_username">Paperless Username</Label>
              <Input
                id="paperless_username"
                value={paperlessData.paperless_username}
                onChange={(e) => setPaperlessData(prev => ({ ...prev, paperless_username: e.target.value }))}
                placeholder="your-username"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="paperless_token">Paperless Auth Token</Label>
              <Input
                id="paperless_token"
                type="password"
                value={paperlessData.paperless_token}
                onChange={(e) => setPaperlessData(prev => ({ ...prev, paperless_token: e.target.value }))}
                placeholder="Enter new token or leave empty to keep current"
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to keep your existing token
              </p>
            </div>
            <Button type="submit" disabled={isSavingPaperless}>
              {isSavingPaperless ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Update Credentials
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
