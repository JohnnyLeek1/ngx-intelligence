import apiClient from './client';
import type {
  ConfigResponse,
  ConfigUpdateRequest,
  AIModelsListResponse,
  PromptUpdateRequest,
  PromptResponse
} from '@/types';

export const settingsApi = {
  // Get full configuration
  getConfig: async (): Promise<ConfigResponse> => {
    const response = await apiClient.get<ConfigResponse>('/config');
    return response.data;
  },

  // Get specific section
  getSection: async (section: string): Promise<Record<string, any>> => {
    const response = await apiClient.get<{ data: Record<string, any> }>(`/config/${section}`);
    return response.data.data;
  },

  // Update configuration section
  updateSection: async (data: ConfigUpdateRequest): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>('/config', data);
    return response.data;
  },

  // Get available AI models
  getModels: async (): Promise<AIModelsListResponse> => {
    const response = await apiClient.get<AIModelsListResponse>('/config/ai/models');
    return response.data;
  },

  // Update AI prompt
  updatePrompt: async (data: PromptUpdateRequest): Promise<PromptResponse> => {
    const response = await apiClient.put<PromptResponse>('/config/ai/prompts', data);
    return response.data;
  },

  // Test AI configuration
  testAI: async (documentContent: string): Promise<any> => {
    const response = await apiClient.post('/config/ai/test', {
      document_content: documentContent,
      test_types: ['classification', 'tagging', 'correspondent']
    });
    return response.data;
  },
};
