import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import LoginPage from '../LoginPage'
import { useLogin } from '@/hooks/useAuth'

// Mock the useAuth hook
vi.mock('@/hooks/useAuth', () => ({
  useLogin: vi.fn(),
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('LoginPage', () => {
  const mockMutateAsync = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useLogin).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any)
  })

  it('renders login form with all fields', () => {
    render(<LoginPage />)

    expect(screen.getByText('NGX Intelligence')).toBeInTheDocument()
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument()
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
  })

  it('submits form with valid credentials', async () => {
    const user = userEvent.setup()
    mockMutateAsync.mockResolvedValue({ access_token: 'token', refresh_token: 'refresh' })

    render(<LoginPage />)

    await user.type(screen.getByLabelText(/username/i), 'testuser')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      })
    })

    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('shows loading state during login', () => {
    vi.mocked(useLogin).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any)

    render(<LoginPage />)

    expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
  })

  it('displays error message on failed login', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Invalid credentials'
    mockMutateAsync.mockRejectedValue({
      response: { data: { detail: errorMessage } }
    })

    render(<LoginPage />)

    await user.type(screen.getByLabelText(/username/i), 'wronguser')
    await user.type(screen.getByLabelText(/password/i), 'wrongpass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('displays generic error on network failure', async () => {
    const user = userEvent.setup()
    mockMutateAsync.mockRejectedValue(new Error('Network error'))

    render(<LoginPage />)

    await user.type(screen.getByLabelText(/username/i), 'testuser')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/login failed/i)).toBeInTheDocument()
    })
  })

  it('requires username and password fields', async () => {
    render(<LoginPage />)

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)

    expect(usernameInput).toHaveAttribute('required')
    expect(passwordInput).toHaveAttribute('required')
  })

  it('has link to registration page', () => {
    render(<LoginPage />)

    const registerLink = screen.getByRole('link', { name: /register/i })
    expect(registerLink).toHaveAttribute('href', '/register')
  })

  it('clears error message when submitting new form', async () => {
    const user = userEvent.setup()
    mockMutateAsync
      .mockRejectedValueOnce({ response: { data: { detail: 'Error 1' } } })
      .mockRejectedValueOnce({ response: { data: { detail: 'Error 2' } } })

    render(<LoginPage />)

    // First failed attempt
    await user.type(screen.getByLabelText(/username/i), 'user1')
    await user.type(screen.getByLabelText(/password/i), 'pass1')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Error 1')).toBeInTheDocument()
    })

    // Second attempt - error should be cleared briefly
    await user.clear(screen.getByLabelText(/username/i))
    await user.clear(screen.getByLabelText(/password/i))
    await user.type(screen.getByLabelText(/username/i), 'user2')
    await user.type(screen.getByLabelText(/password/i), 'pass2')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Error 2')).toBeInTheDocument()
    })
  })
})
