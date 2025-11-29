import { Outlet, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useCurrentUser } from '@/hooks/useAuth';
import { useSetAtom } from 'jotai';
import { clearAuthAtom } from '@/store/auth';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function Layout() {
  const navigate = useNavigate();
  const clearAuth = useSetAtom(clearAuthAtom);

  // Fetch current user data when layout mounts
  const { isLoading, error } = useCurrentUser();

  // If there's an error fetching user (e.g., invalid/expired token), clear auth and redirect
  useEffect(() => {
    if (error) {
      clearAuth();
      navigate('/login', { replace: true });
    }
  }, [error, clearAuth, navigate]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-2 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-2 text-sm text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 pt-20 md:ml-64">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
