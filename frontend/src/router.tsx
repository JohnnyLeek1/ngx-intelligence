import { createBrowserRouter, Navigate, useRouteError } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { isAuthenticatedAtom } from './store/auth';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './pages/Dashboard';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/settings';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './components/ui/button';
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert';

// Custom error element for React Router
function RouterErrorBoundary() {
  const error = useRouteError() as Error;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="max-w-2xl w-full space-y-4">
        <Alert variant="destructive">
          <AlertCircle className="h-5 w-5" />
          <AlertTitle className="text-lg font-semibold">
            Oh man... Something went wrong
          </AlertTitle>
          <AlertDescription className="!translate-y-0 mt-2">
            <p className="mb-4">
              The application encountered an unexpected error. If this is reproducible, please log a GitHub issue!
            </p>
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium mb-2">
                Error details
              </summary>
              <div className="bg-muted rounded-md p-4 mt-2 overflow-auto">
                <pre className="text-xs whitespace-pre-wrap break-words">
                  {error?.toString() || 'Unknown error'}
                </pre>
              </div>
            </details>
          </AlertDescription>
        </Alert>

        <div className="flex gap-2">
          <Button onClick={() => window.location.reload()} variant="default">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reload page
          </Button>
        </div>
      </div>
    </div>
  );
}

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
    errorElement: <RouterErrorBoundary />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
    errorElement: <RouterErrorBoundary />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    errorElement: <RouterErrorBoundary />,
    children: [
      {
        index: true,
        element: <Dashboard />,
        errorElement: <RouterErrorBoundary />,
      },
      {
        path: 'history',
        element: <HistoryPage />,
        errorElement: <RouterErrorBoundary />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
        errorElement: <RouterErrorBoundary />,
      },
    ],
  },
]);
