import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useLogin, useRegister, useCurrentUser, useLogout, useChangePassword } from '../useAuth'
import { authApi } from '@/api/auth'
import type { LoginRequest, UserCreate } from '@/types'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
    changePassword: vi.fn(),
  },
}))

vi.mock('@/store/auth', () => ({
  setAuthTokensAtom: { write: vi.fn() },
  clearAuthAtom: { write: vi.fn() },
  currentUserAtom: { read: vi.fn(), write: vi.fn() },
}))

vi.mock('jotai', async () => {
  const actual = await vi.importActual('jotai')
  return {
    ...actual,
    useSetAtom: () => vi.fn(),
    useAtom: () => [null, vi.fn()],
  }
})

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useAuth hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useLogin', () => {
    it('successfully logs in a user', async () => {
      const mockTokens = {
        access_token: 'access123',
        refresh_token: 'refresh456',
        token_type: 'Bearer',
      }

      vi.mocked(authApi.login).mockResolvedValue(mockTokens)

      const { result } = renderHook(() => useLogin(), {
        wrapper: createWrapper(),
      })

      const credentials: LoginRequest = {
        username: 'testuser',
        password: 'password123',
      }

      result.current.mutate(credentials)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(authApi.login).toHaveBeenCalledWith(credentials)
    })

    it('handles login errors', async () => {
      const error = new Error('Invalid credentials')
      vi.mocked(authApi.login).mockRejectedValue(error)

      const { result } = renderHook(() => useLogin(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        username: 'wronguser',
        password: 'wrongpass',
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBe(error)
    })

    it('sets pending state during login', async () => {
      vi.mocked(authApi.login).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      const { result } = renderHook(() => useLogin(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        username: 'testuser',
        password: 'password123',
      })

      expect(result.current.isPending).toBe(true)
    })
  })

  describe('useRegister', () => {
    it('successfully registers a new user', async () => {
      const mockUser = {
        id: 'user1',
        username: 'newuser',
        email: 'new@example.com',
        role: 'user' as const,
        paperless_url: 'http://paperless.local',
        paperless_username: 'paperlessuser',
        timezone: 'UTC',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        is_active: true,
      }

      vi.mocked(authApi.register).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useRegister(), {
        wrapper: createWrapper(),
      })

      const userData: UserCreate = {
        username: 'newuser',
        password: 'SecurePass123',
        email: 'new@example.com',
        paperless_url: 'http://paperless.local',
        paperless_username: 'paperlessuser',
        paperless_token: 'token123',
      }

      result.current.mutate(userData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(authApi.register).toHaveBeenCalledWith(userData)
    })

    it('handles registration errors', async () => {
      const error = new Error('Username already exists')
      vi.mocked(authApi.register).mockRejectedValue(error)

      const { result } = renderHook(() => useRegister(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        username: 'existinguser',
        password: 'password123',
        paperless_url: 'http://paperless.local',
        paperless_username: 'paperlessuser',
        paperless_token: 'token123',
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBe(error)
    })
  })

  describe('useCurrentUser', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.removeItem('auth_token')
      localStorage.removeItem('refresh_token')
    })

    it('fetches current user successfully when token exists', async () => {
      // Set up auth token in localStorage
      localStorage.setItem('auth_token', JSON.stringify('valid_token'))

      const mockUser = {
        id: 'user1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user' as const,
        paperless_url: 'http://paperless.local',
        paperless_username: 'paperlessuser',
        timezone: 'UTC',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        is_active: true,
      }

      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockUser)
      expect(authApi.getCurrentUser).toHaveBeenCalled()
    })

    it('does not fetch when no token exists', async () => {
      // No token in localStorage

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      })

      // Query should be disabled, so it stays in idle state
      expect(result.current.status).toBe('pending')
      expect(result.current.fetchStatus).toBe('idle')
      expect(authApi.getCurrentUser).not.toHaveBeenCalled()
    })

    it('does not fetch when token is null string', async () => {
      localStorage.setItem('auth_token', 'null')

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      })

      // Query should be disabled
      expect(result.current.status).toBe('pending')
      expect(result.current.fetchStatus).toBe('idle')
      expect(authApi.getCurrentUser).not.toHaveBeenCalled()
    })

    it('handles fetch errors without retry', async () => {
      // Set up auth token in localStorage
      localStorage.setItem('auth_token', JSON.stringify('invalid_token'))

      const error = new Error('Unauthorized')
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(error)

      const { result } = renderHook(() => useCurrentUser(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      // Should only be called once (no retries)
      expect(authApi.getCurrentUser).toHaveBeenCalledTimes(1)
    })
  })

  describe('useLogout', () => {
    it('successfully logs out a user', async () => {
      vi.mocked(authApi.logout).mockResolvedValue({ message: 'Logged out successfully' })

      const { result } = renderHook(() => useLogout(), {
        wrapper: createWrapper(),
      })

      result.current.mutate()

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(authApi.logout).toHaveBeenCalled()
    })

    it('handles logout errors', async () => {
      const error = new Error('Logout failed')
      vi.mocked(authApi.logout).mockRejectedValue(error)

      const { result } = renderHook(() => useLogout(), {
        wrapper: createWrapper(),
      })

      result.current.mutate()

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })
    })
  })

  describe('useChangePassword', () => {
    it('successfully changes password', async () => {
      const mockResponse = { message: 'Password updated successfully' }
      vi.mocked(authApi.changePassword).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useChangePassword(), {
        wrapper: createWrapper(),
      })

      const passwordData = {
        current_password: 'OldPass123',
        new_password: 'NewPass456',
      }

      result.current.mutate(passwordData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(authApi.changePassword).toHaveBeenCalledWith(passwordData)
    })

    it('handles password change errors', async () => {
      const error = new Error('Current password incorrect')
      vi.mocked(authApi.changePassword).mockRejectedValue(error)

      const { result } = renderHook(() => useChangePassword(), {
        wrapper: createWrapper(),
      })

      result.current.mutate({
        current_password: 'WrongPass',
        new_password: 'NewPass456',
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBe(error)
    })
  })
})
