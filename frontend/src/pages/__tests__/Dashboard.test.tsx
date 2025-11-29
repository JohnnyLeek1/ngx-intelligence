import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/tests/utils'
import Dashboard from '../Dashboard'
import { useDocumentStats, useRecentDocuments } from '@/hooks/useDocuments'
import { useQueueStats } from '@/hooks/useQueue'

vi.mock('@/hooks/useDocuments', () => ({
  useDocumentStats: vi.fn(),
  useRecentDocuments: vi.fn(),
}))

vi.mock('@/hooks/useQueue', () => ({
  useQueueStats: vi.fn(),
}))

describe('Dashboard', () => {
  const mockStats = {
    total: 150,
    success: 135,
    failed: 5,
    pending_approval: 10,
    success_rate: 0.9,
    avg_processing_time_ms: 1250,
    avg_confidence: 0.85,
  }

  const mockQueueStats = {
    queued: 8,
    processing: 2,
    completed: 120,
    failed: 3,
    total: 133,
  }

  const mockRecentDocs = [
    {
      id: '1',
      user_id: 'user1',
      paperless_document_id: 101,
      processed_at: new Date().toISOString(),
      status: 'success' as const,
      confidence_score: 0.95,
      processing_time_ms: 1200,
      reprocess_count: 0,
    },
    {
      id: '2',
      user_id: 'user1',
      paperless_document_id: 102,
      processed_at: new Date(Date.now() - 3600000).toISOString(),
      status: 'failed' as const,
      error_message: 'OCR failed',
      reprocess_count: 1,
    },
  ]

  it('shows loading skeleton when data is loading', () => {
    vi.mocked(useDocumentStats).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    render(<Dashboard />)

    // Should show skeletons
    const skeletons = screen.getAllByTestId(/skeleton/i)
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders dashboard with all stats cards', () => {
    vi.mocked(useDocumentStats).mockReturnValue({
      data: mockStats,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: mockRecentDocs,
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Total Documents')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
    expect(screen.getByText('Success Rate')).toBeInTheDocument()
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('Queue')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('displays queue status with progress bar', () => {
    vi.mocked(useDocumentStats).mockReturnValue({
      data: mockStats,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: mockRecentDocs,
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.getByText('Processing Queue')).toBeInTheDocument()
    expect(screen.getByText('Queued')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('Processing')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()

    // Progress should be calculated
    const progressPercentage = Math.round((120 / 133) * 100)
    expect(screen.getByText(`${progressPercentage}%`)).toBeInTheDocument()
  })

  it('shows recent activity with documents', () => {
    vi.mocked(useDocumentStats).mockReturnValue({
      data: mockStats,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: mockRecentDocs,
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    expect(screen.getByText('Document #101')).toBeInTheDocument()
    expect(screen.getByText('Document #102')).toBeInTheDocument()
    expect(screen.getByText('Confidence: 95%')).toBeInTheDocument()
    expect(screen.getByText('1200ms')).toBeInTheDocument()
  })

  it('displays alert when there are failed documents', () => {
    vi.mocked(useDocumentStats).mockReturnValue({
      data: mockStats,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: mockRecentDocs,
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.getByText('Alerts')).toBeInTheDocument()
    expect(screen.getByText('Failed Processing Jobs')).toBeInTheDocument()
    expect(screen.getByText(/5 documents failed to process/i)).toBeInTheDocument()
  })

  it('does not show alert when no failures', () => {
    const statsWithNoFailures = { ...mockStats, failed: 0 }

    vi.mocked(useDocumentStats).mockReturnValue({
      data: statsWithNoFailures,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: mockRecentDocs,
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.queryByText('Alerts')).not.toBeInTheDocument()
    expect(screen.queryByText('Failed Processing Jobs')).not.toBeInTheDocument()
  })

  it('shows "Excellent performance" trend for high success rate', () => {
    const highSuccessStats = { ...mockStats, success_rate: 0.95 }

    vi.mocked(useDocumentStats).mockReturnValue({
      data: highSuccessStats,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: mockRecentDocs,
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.getByText('Excellent performance')).toBeInTheDocument()
  })

  it('shows empty state when no recent documents', () => {
    vi.mocked(useDocumentStats).mockReturnValue({
      data: mockStats,
      isLoading: false,
    } as any)
    vi.mocked(useQueueStats).mockReturnValue({
      data: mockQueueStats,
      isLoading: false,
    } as any)
    vi.mocked(useRecentDocuments).mockReturnValue({
      data: [],
      isLoading: false,
    } as any)

    render(<Dashboard />)

    expect(screen.getByText('No recent documents')).toBeInTheDocument()
  })
})
