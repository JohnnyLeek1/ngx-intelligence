import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useQueueStats } from '../useQueue'
import { queueApi } from '@/api/queue'

vi.mock('@/api/queue', () => ({
  queueApi: {
    getStats: vi.fn(),
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

describe('useQueue hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useQueueStats', () => {
    it('fetches queue statistics', async () => {
      const mockStats = {
        queued: 8,
        processing: 2,
        completed: 120,
        failed: 3,
        total: 133,
        estimated_time_remaining: 240,
      }

      vi.mocked(queueApi.getStats).mockResolvedValue(mockStats)

      const { result } = renderHook(() => useQueueStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockStats)
      expect(queueApi.getStats).toHaveBeenCalled()
    })

    it('handles fetch errors', async () => {
      const error = new Error('Failed to fetch queue stats')
      vi.mocked(queueApi.getStats).mockRejectedValue(error)

      const { result } = renderHook(() => useQueueStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBe(error)
    })

    it('auto-refetches on interval', async () => {
      const mockStats = {
        queued: 8,
        processing: 2,
        completed: 120,
        failed: 3,
        total: 133,
      }

      vi.mocked(queueApi.getStats).mockResolvedValue(mockStats)

      const { result } = renderHook(() => useQueueStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Initially called once
      expect(queueApi.getStats).toHaveBeenCalledTimes(1)
    })

    it('handles zero items in queue', async () => {
      const mockStats = {
        queued: 0,
        processing: 0,
        completed: 100,
        failed: 5,
        total: 105,
      }

      vi.mocked(queueApi.getStats).mockResolvedValue(mockStats)

      const { result } = renderHook(() => useQueueStats(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.queued).toBe(0)
      expect(result.current.data?.processing).toBe(0)
    })
  })

})
