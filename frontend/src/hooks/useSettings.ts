import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '@/api/settings';
import type { ConfigUpdateRequest, PromptUpdateRequest } from '@/types';

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: () => settingsApi.getConfig(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useConfigSection(section: string) {
  return useQuery({
    queryKey: ['config', section],
    queryFn: () => settingsApi.getSection(section),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ConfigUpdateRequest) => settingsApi.updateSection(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      queryClient.invalidateQueries({ queryKey: ['config', variables.section] });

      // If AI config was updated, also invalidate aiModels to refresh "currently using" label
      if (variables.section === 'ai') {
        queryClient.invalidateQueries({ queryKey: ['aiModels'] });
      }
    },
  });
}

export function useAIModels() {
  return useQuery({
    queryKey: ['aiModels'],
    queryFn: () => settingsApi.getModels(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useUpdatePrompt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PromptUpdateRequest) => settingsApi.updatePrompt(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config', 'ai'] });
    },
  });
}

export function useTestAI() {
  return useMutation({
    mutationFn: (documentContent: string) => settingsApi.testAI(documentContent),
  });
}
