import apiClient from './client';
import type {
  ProcessedDocument,
  ProcessedDocumentDetail,
  DocumentStatsResponse,
  DocumentFilterRequest,
  DocumentReprocessRequest,
  DailyMetricsResponse
} from '@/types';

export const documentsApi = {
  // Get processed documents with filters
  list: async (filters?: DocumentFilterRequest): Promise<{ documents: ProcessedDocument[]; total: number }> => {
    const response = await apiClient.get<ProcessedDocument[]>(
      '/documents',
      { params: filters }
    );
    // Backend returns array directly, wrap it for consistency
    return {
      documents: response.data,
      total: response.data.length
    };
  },

  // Get single document details
  getById: async (id: string): Promise<ProcessedDocumentDetail> => {
    const response = await apiClient.get<ProcessedDocumentDetail>(`/documents/${id}`);
    return response.data;
  },

  // Get document statistics
  getStats: async (): Promise<DocumentStatsResponse> => {
    const response = await apiClient.get<DocumentStatsResponse>('/documents/stats');
    return response.data;
  },

  // Reprocess documents
  reprocess: async (data: DocumentReprocessRequest): Promise<{ message: string; queued: number }> => {
    const response = await apiClient.post<{ message: string; queued: number }>(
      '/documents/reprocess',
      data
    );
    return response.data;
  },

  // Get recent documents
  getRecent: async (limit: number = 10): Promise<ProcessedDocument[]> => {
    const response = await apiClient.get<ProcessedDocument[]>('/documents', {
      params: { limit, offset: 0 }
    });
    return response.data;
  },

  // Get daily metrics (today vs yesterday)
  getDailyMetrics: async (): Promise<DailyMetricsResponse> => {
    const response = await apiClient.get<DailyMetricsResponse>('/metrics/daily');
    return response.data;
  },
};
