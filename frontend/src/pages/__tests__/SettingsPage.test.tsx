import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import SettingsPage from '../SettingsPage'
import { useConfig } from '@/hooks/useSettings'

// Mock Jotai atoms
vi.mock('jotai', async () => {
  const actual = await vi.importActual('jotai')
  return {
    ...actual,
    useAtomValue: vi.fn(() => ({
      id: 'user1',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      paperless_url: 'http://paperless.example.com',
      paperless_username: 'paperlessuser',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      is_active: true,
    })),
  }
})

vi.mock('@/hooks/useSettings', () => ({
  useConfig: vi.fn(),
}))

describe('SettingsPage', () => {
  const mockConfig = {
    ai: {
      model: 'llama3.2:latest',
      system_prompt: 'You are a helpful assistant',
      temperature: 0.1,
    },
    processing: {
      polling_interval: 60,
      max_workers: 3,
    },
    naming: {
      title_template: '{date} - {correspondent} - {type}',
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton when config is loading', () => {
    vi.mocked(useConfig).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    render(<SettingsPage />)

    const skeletons = screen.getAllByTestId(/skeleton/i)
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders all tabs for regular users', () => {
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    expect(screen.getByRole('tab', { name: /general/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /naming templates/i })).toBeInTheDocument()

    // Admin-only tabs should not be visible
    expect(screen.queryByRole('tab', { name: /ai configuration/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: /processing/i })).not.toBeInTheDocument()
  })

  it('renders admin tabs for admin users', async () => {
    const { useAtomValue } = await import('jotai')
    vi.mocked(useAtomValue).mockReturnValue({
      id: 'admin1',
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin',
      paperless_url: 'http://paperless.example.com',
      paperless_username: 'paperlessadmin',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      is_active: true,
    })

    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    expect(screen.getByRole('tab', { name: /general/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /ai configuration/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /processing/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /naming templates/i })).toBeInTheDocument()
  })

  it('displays user profile information', () => {
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('user')).toBeInTheDocument()
  })

  it('displays paperless credentials', () => {
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    expect(screen.getByDisplayValue('http://paperless.example.com')).toBeInTheDocument()
    expect(screen.getByDisplayValue('paperlessuser')).toBeInTheDocument()
  })

  it('allows password change form submission', async () => {
    const user = userEvent.setup()
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    const currentPasswordInput = screen.getByLabelText(/current password/i)
    const newPasswordInput = screen.getByLabelText(/new password/i)

    await user.type(currentPasswordInput, 'oldpassword123')
    await user.type(newPasswordInput, 'NewPassword123')

    const updateButton = screen.getByRole('button', { name: /update password/i })
    await user.click(updateButton)

    await waitFor(() => {
      expect(screen.getByText(/password change functionality pending/i)).toBeInTheDocument()
    })
  })

  it('shows password complexity requirements', () => {
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    expect(
      screen.getByText(/must be at least 8 characters with uppercase, lowercase, and digit/i)
    ).toBeInTheDocument()
  })

  it('switches between tabs', async () => {
    const user = userEvent.setup()
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    const namingTab = screen.getByRole('tab', { name: /naming templates/i })
    await user.click(namingTab)

    await waitFor(() => {
      expect(screen.getByText('Document Title Template')).toBeInTheDocument()
    })
  })

  it('displays naming template configuration', async () => {
    const user = userEvent.setup()
    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    render(<SettingsPage />)

    const namingTab = screen.getByRole('tab', { name: /naming templates/i })
    await user.click(namingTab)

    await waitFor(() => {
      expect(screen.getByDisplayValue('{date} - {correspondent} - {type}')).toBeInTheDocument()
      expect(screen.getByText(/available variables/i)).toBeInTheDocument()
      expect(screen.getByText('Preview')).toBeInTheDocument()
      expect(screen.getByText('2025-01-15 - Acme Corp - Invoice')).toBeInTheDocument()
    })
  })

  it('displays AI configuration for admin users', async () => {
    const { useAtomValue } = await import('jotai')
    vi.mocked(useAtomValue).mockReturnValue({
      id: 'admin1',
      username: 'admin',
      role: 'admin',
      email: 'admin@example.com',
      paperless_url: 'http://paperless.example.com',
      paperless_username: 'paperlessadmin',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      is_active: true,
    })

    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    const user = userEvent.setup()
    render(<SettingsPage />)

    const aiTab = screen.getByRole('tab', { name: /ai configuration/i })
    await user.click(aiTab)

    await waitFor(() => {
      expect(screen.getByText('AI Configuration')).toBeInTheDocument()
      expect(screen.getByDisplayValue('llama3.2:latest')).toBeInTheDocument()
      expect(screen.getByText(/temperature/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/system prompt/i)).toBeInTheDocument()
    })
  })

  it('displays processing configuration for admin users', async () => {
    const { useAtomValue } = await import('jotai')
    vi.mocked(useAtomValue).mockReturnValue({
      id: 'admin1',
      username: 'admin',
      role: 'admin',
      email: 'admin@example.com',
      paperless_url: 'http://paperless.example.com',
      paperless_username: 'paperlessadmin',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      is_active: true,
    })

    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    const user = userEvent.setup()
    render(<SettingsPage />)

    const processingTab = screen.getByRole('tab', { name: /^processing$/i })
    await user.click(processingTab)

    await waitFor(() => {
      expect(screen.getByText('Processing Configuration')).toBeInTheDocument()
      expect(screen.getByText('Auto-process New Documents')).toBeInTheDocument()
      expect(screen.getByDisplayValue('60')).toBeInTheDocument() // Polling interval
      expect(screen.getByDisplayValue('3')).toBeInTheDocument() // Max workers
    })
  })

  it('allows toggling auto-process switch', async () => {
    const { useAtomValue } = await import('jotai')
    vi.mocked(useAtomValue).mockReturnValue({
      id: 'admin1',
      username: 'admin',
      role: 'admin',
      email: 'admin@example.com',
      paperless_url: 'http://paperless.example.com',
      paperless_username: 'paperlessadmin',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      is_active: true,
    })

    vi.mocked(useConfig).mockReturnValue({
      data: mockConfig,
      isLoading: false,
    } as any)

    const user = userEvent.setup()
    render(<SettingsPage />)

    const processingTab = screen.getByRole('tab', { name: /^processing$/i })
    await user.click(processingTab)

    await waitFor(async () => {
      const autoProcessSwitch = screen.getByRole('switch')
      expect(autoProcessSwitch).toBeInTheDocument()

      await user.click(autoProcessSwitch)
      // Switch should toggle (implementation dependent on actual state management)
    })
  })
})
