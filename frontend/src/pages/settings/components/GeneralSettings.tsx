import { useState } from 'react';
import { useAtomValue } from 'jotai';
import { currentUserAtom } from '@/store/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Save, AlertCircle } from 'lucide-react';

export function GeneralSettings() {
  const currentUser = useAtomValue(currentUserAtom);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
  });
  const [passwordMessage, setPasswordMessage] = useState('');

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage('');
    // This would use useChangePassword hook
    setPasswordMessage('Password change functionality pending');
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
            <Input value={currentUser?.paperless_url || ''} readOnly />
          </div>
          <div className="space-y-2">
            <Label>Paperless Username</Label>
            <Input value={currentUser?.paperless_username || ''} readOnly />
          </div>
          <div className="space-y-2">
            <Label>Paperless Auth Token</Label>
            <Input type="password" placeholder="••••••••••••" readOnly />
          </div>
          <Button>
            <Save className="h-4 w-4 mr-2" />
            Update Credentials
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
