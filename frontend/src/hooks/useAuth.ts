import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAtom, useSetAtom } from 'jotai';
import { authApi } from '@/api/auth';
import { setAuthTokensAtom, clearAuthAtom, currentUserAtom } from '@/store/auth';
import type { LoginRequest, UserCreate, UserPasswordChange } from '@/types';

export function useLogin() {
  const setTokens = useSetAtom(setAuthTokensAtom);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      setTokens(data);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (userData: UserCreate) => authApi.register(userData),
  });
}

export function useCurrentUser() {
  const [, setCurrentUser] = useAtom(currentUserAtom);

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const user = await authApi.getCurrentUser();
      setCurrentUser(user);
      return user;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  });
}

export function useLogout() {
  const clearAuth = useSetAtom(clearAuthAtom);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      clearAuth();
      queryClient.clear();
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: UserPasswordChange) => authApi.changePassword(data),
  });
}
