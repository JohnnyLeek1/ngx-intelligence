import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import HistoryPage from '../HistoryPage'
import { useDocuments } from '@/hooks/useDocuments'

vi.mock('@/hooks/useDocuments', () => ({
  useDocuments: vi.fn(),
}))

describe('HistoryPage', () => {
  const mockDocuments = {
    documents: [
      {
        id: '1',
        user_id: 'user1',
        paperless_document_id: 101,
        processed_at: '2025-01-15T10:30:00Z',
        status: 'success' as const,
        confidence_score: 0.95,
        processing_time_ms: 1200,
        suggested_data: { title: 'Test Doc' },
        reprocess_count: 0,
      },
      {
        id: '2',
        user_id: 'user1',
        paperless_document_id: 102,
        processed_at: '2025-01-14T15:45:00Z',
        status: 'failed' as const,
        error_message: 'OCR processing failed',
        processing_time_ms: 500,
        reprocess_count: 1,
      },
      {
        id: '3',
        user_id: 'user1',
        paperless_document_id: 103,
        processed_at: '2025-01-13T09:15:00Z',
        status: 'pending_approval' as const,
        confidence_score: 0.65,
        processing_time_ms: 1500,
        reprocess_count: 0,
      },
    ],
    total: 3,
    limit: 50,
    offset: 0,
  }

  const mockRefetch = vi.fn()

  it('renders history page with document table', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    expect(screen.getByText('Processing History')).toBeInTheDocument()
    expect(screen.getByText('Showing 3 of 3 documents')).toBeInTheDocument()
    expect(screen.getByText('#101')).toBeInTheDocument()
    expect(screen.getByText('#102')).toBeInTheDocument()
    expect(screen.getByText('#103')).toBeInTheDocument()
  })

  it('shows loading skeleton when data is loading', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: undefined,
      isLoading: true,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const skeletons = screen.getAllByTestId(/skeleton/i)
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('displays correct status badges', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    expect(screen.getByText('Success')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })

  it('shows confidence scores correctly', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    expect(screen.getByText('95%')).toBeInTheDocument()
    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('filters documents by status when clicking filter buttons', async () => {
    const user = userEvent.setup()
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const successButton = screen.getByRole('button', { name: 'Success' })
    await user.click(successButton)

    await waitFor(() => {
      expect(vi.mocked(useDocuments)).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'success',
          offset: 0,
        })
      )
    })
  })

  it('allows searching by document ID', async () => {
    const user = userEvent.setup()
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const searchInput = screen.getByPlaceholderText(/search by document id/i)
    await user.type(searchInput, '101')

    expect(searchInput).toHaveValue('101')
  })

  it('refreshes data when clicking refresh button', async () => {
    const user = userEvent.setup()
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    await user.click(refreshButton)

    expect(mockRefetch).toHaveBeenCalled()
  })

  it('opens document details dialog when clicking View Details', async () => {
    const user = userEvent.setup()
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const viewButtons = screen.getAllByRole('button', { name: /view details/i })
    await user.click(viewButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Document Details')).toBeInTheDocument()
      expect(screen.getByText('Document #101')).toBeInTheDocument()
    })
  })

  it('shows suggested data in detail dialog', async () => {
    const user = userEvent.setup()
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const viewButtons = screen.getAllByRole('button', { name: /view details/i })
    await user.click(viewButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Suggested Data')).toBeInTheDocument()
      expect(screen.getByText(/"title": "Test Doc"/)).toBeInTheDocument()
    })
  })

  it('shows error message in detail dialog for failed documents', async () => {
    const user = userEvent.setup()
    vi.mocked(useDocuments).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const viewButtons = screen.getAllByRole('button', { name: /view details/i })
    await user.click(viewButtons[1])

    await waitFor(() => {
      expect(screen.getByText('Error Message')).toBeInTheDocument()
      expect(screen.getByText('OCR processing failed')).toBeInTheDocument()
    })
  })

  it('shows pagination controls when there are more documents', () => {
    const manyDocuments = {
      ...mockDocuments,
      total: 100,
      limit: 50,
      offset: 0,
    }

    vi.mocked(useDocuments).mockReturnValue({
      data: manyDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    expect(screen.getByText(/showing 1 to 50 of 100/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /next/i })).toBeEnabled()
  })

  it('navigates to next page when clicking Next', async () => {
    const user = userEvent.setup()
    const manyDocuments = {
      ...mockDocuments,
      total: 100,
      limit: 50,
      offset: 0,
    }

    vi.mocked(useDocuments).mockReturnValue({
      data: manyDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(vi.mocked(useDocuments)).toHaveBeenCalledWith(
        expect.objectContaining({
          offset: 50,
        })
      )
    })
  })

  it('shows empty state when no documents found', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: { documents: [], total: 0, limit: 50, offset: 0 },
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    expect(screen.getByText('No documents found')).toBeInTheDocument()
  })

  it('resets offset when changing status filter', async () => {
    const user = userEvent.setup()
    const manyDocuments = {
      ...mockDocuments,
      total: 100,
      limit: 50,
      offset: 50, // On second page
    }

    vi.mocked(useDocuments).mockReturnValue({
      data: manyDocuments,
      isLoading: false,
      refetch: mockRefetch,
    } as any)

    render(<HistoryPage />)

    const failedButton = screen.getByRole('button', { name: 'Failed' })
    await user.click(failedButton)

    await waitFor(() => {
      expect(vi.mocked(useDocuments)).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'failed',
          offset: 0, // Should reset to first page
        })
      )
    })
  })
})
