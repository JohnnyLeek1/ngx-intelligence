import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useDocuments, useDocumentStats, useRecentDocuments } from '../useDocuments'
import { documentsApi } from '@/api/documents'
import type { DocumentFilterRequest } from '@/types'

vi.mock('@/api/documents', () => ({
  documentsApi: {
    list: vi.fn(),
    getStats: vi.fn(),
    getRecent: vi.fn(),
  },
}))

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

describe('useDocuments hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useDocuments', () => {
    it('fetches documents with filters', async () => {
      const mockResponse = {
        documents: [
          {
            id: '1',
            user_id: 'user1',
            paperless_document_id: 101,
            processed_at: '2025-01-15T10:00:00Z',
            status: 'success' as const,
            confidence_score: 0.95,
            reprocess_count: 0,
          },
        ],
        total: 1,
      }

      vi.mocked(documentsApi.list).mockResolvedValue(mockResponse)

      const filters: DocumentFilterRequest = {
        status: 'success',
        limit: 50,
        offset: 0,
      }

      const { result } = renderHook(() => useDocuments(filters), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockResponse)
      expect(documentsApi.list).toHaveBeenCalledWith(filters)
    })

    it('handles empty document list', async () => {
      const mockResponse = {
        documents: [],
        total: 0,
      }

      vi.mocked(documentsApi.list).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useDocuments({}), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.documents).toHaveLength(0)
    })

    it('handles fetch errors', async () => {
      const error = new Error('Failed to fetch documents')
      vi.mocked(documentsApi.list).mockRejectedValue(error)

      const { result } = renderHook(() => useDocuments({}), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBe(error)
    })

    it('can be refetched', async () => {
      const mockResponse = {
        documents: [],
        total: 0,
      }

      vi.mocked(documentsApi.list).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useDocuments({}), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      result.current.refetch()

      await waitFor(() => {
        expect(documentsApi.list).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('useDocumentStats', () => {
    it('fetches document statistics', async () => {
      const mockStats = {
        total: 150,
        success: 135,
        failed: 5,
        pending_approval: 10,
        success_rate: 0.9,
        avg_processing_time_ms: 1200,
        avg_confidence: 0.85,
      }

      vi.mocked(documentsApi.getStats).mockResolvedValue(mockStats)

      const { result } = renderHook(() => useDocumentStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockStats)
      expect(documentsApi.getStats).toHaveBeenCalled()
    })

    it('handles stats fetch errors', async () => {
      const error = new Error('Failed to fetch stats')
      vi.mocked(documentsApi.getStats).mockRejectedValue(error)

      const { result } = renderHook(() => useDocumentStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBe(error)
    })

    it('auto-refetches on interval', async () => {
      const mockStats = {
        total: 150,
        success: 135,
        failed: 5,
        pending_approval: 10,
        success_rate: 0.9,
      }

      vi.mocked(documentsApi.getStats).mockResolvedValue(mockStats)

      const { result } = renderHook(() => useDocumentStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(documentsApi.getStats).toHaveBeenCalledTimes(1)
    })
  })

  describe('useRecentDocuments', () => {
    it('fetches recent documents with limit', async () => {
      const mockDocuments = [
        {
          id: '1',
          user_id: 'user1',
          paperless_document_id: 101,
          processed_at: '2025-01-15T10:00:00Z',
          status: 'success' as const,
          confidence_score: 0.95,
          reprocess_count: 0,
        },
        {
          id: '2',
          user_id: 'user1',
          paperless_document_id: 102,
          processed_at: '2025-01-14T09:00:00Z',
          status: 'failed' as const,
          reprocess_count: 1,
        },
      ]

      vi.mocked(documentsApi.getRecent).mockResolvedValue(mockDocuments)

      const { result } = renderHook(() => useRecentDocuments(10), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toHaveLength(2)
      expect(documentsApi.getRecent).toHaveBeenCalledWith(10)
    })

    it('uses default limit of 10', async () => {
      vi.mocked(documentsApi.getRecent).mockResolvedValue([])

      const { result } = renderHook(() => useRecentDocuments(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(documentsApi.getRecent).toHaveBeenCalledWith(10)
    })

    it('handles custom limit', async () => {
      vi.mocked(documentsApi.getRecent).mockResolvedValue([])

      const { result } = renderHook(() => useRecentDocuments(5), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(documentsApi.getRecent).toHaveBeenCalledWith(5)
    })
  })
})
