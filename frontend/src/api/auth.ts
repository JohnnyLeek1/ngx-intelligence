import apiClient from './client';
import type {
  LoginRequest,
  TokenResponse,
  UserCreate,
  User,
  UserPasswordChange,
  TokenRefreshRequest
} from '@/types';

export const authApi = {
  // Register new user
  register: async (userData: UserCreate): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', userData);
    return response.data;
  },

  // Login
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  // Refresh access token
  refresh: async (refreshData: TokenRefreshRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/refresh', refreshData);
    return response.data;
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  // Change password
  changePassword: async (passwordData: UserPasswordChange): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>('/auth/password', passwordData);
    return response.data;
  },

  // Logout
  logout: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/logout');
    return response.data;
  },
};
