import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '@/api/documents';
import type { DocumentFilterRequest, DocumentReprocessRequest } from '@/types';

export function useDocuments(filters?: DocumentFilterRequest) {
  return useQuery({
    queryKey: ['documents', filters],
    queryFn: () => documentsApi.list(filters),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => documentsApi.getById(id),
    enabled: !!id,
  });
}

export function useDocumentStats() {
  return useQuery({
    queryKey: ['documentStats'],
    queryFn: () => documentsApi.getStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useRecentDocuments(limit: number = 10) {
  return useQuery({
    queryKey: ['recentDocuments', limit],
    queryFn: () => documentsApi.getRecent(limit),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useReprocessDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DocumentReprocessRequest) => documentsApi.reprocess(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['queue'] });
    },
  });
}
