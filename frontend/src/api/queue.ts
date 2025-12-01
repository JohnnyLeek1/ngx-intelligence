import apiClient from './client';
import type { QueueStatsResponse } from '@/types';

export interface ProcessNowResponse {
  message: string;
  queued: number;
  total_found: number;
  already_processed: number;
  already_queued: number;
}

export const queueApi = {
  // Get queue statistics
  getStats: async (): Promise<QueueStatsResponse> => {
    const response = await apiClient.get<QueueStatsResponse>('/queue/stats');
    return response.data;
  },

  // Pause queue processing
  pause: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/queue/pause');
    return response.data;
  },

  // Resume queue processing
  resume: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/queue/resume');
    return response.data;
  },

  // Manually trigger document processing
  processNow: async (limit: number = 10): Promise<ProcessNowResponse> => {
    const response = await apiClient.post<ProcessNowResponse>('/queue/process-now', {
      limit,
    });
    return response.data;
  },

  // Reset queue statistics (clear completed/failed items)
  reset: async (): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>('/queue/completed');
    return response.data;
  },
};
