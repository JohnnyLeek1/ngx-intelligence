import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queueApi } from '@/api/queue';

export function useQueueStats() {
  return useQuery({
    queryKey: ['queueStats'],
    queryFn: () => queueApi.getStats(),
    refetchInterval: 10000, // Refresh every 10 seconds for real-time updates
  });
}

export function usePauseQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => queueApi.pause(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });
}

export function useResumeQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => queueApi.resume(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });
}

export function useProcessNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (limit?: number) => queueApi.processNow(limit),
    onSuccess: () => {
      // Refresh queue stats and recent documents
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
      queryClient.invalidateQueries({ queryKey: ['recentDocuments'] });
      queryClient.invalidateQueries({ queryKey: ['documentStats'] });
    },
  });
}

export function useResetQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => queueApi.reset(),
    onSuccess: () => {
      // Refresh queue stats after clearing
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });
}
