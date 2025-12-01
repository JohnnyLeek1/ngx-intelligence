// User types
export type UserRole = 'admin' | 'user';

export interface User {
  id: string;
  username: string;
  email?: string;
  role: UserRole;
  paperless_url: string;
  paperless_username: string;
  timezone: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface UserCreate {
  username: string;
  password: string;
  email?: string;
  paperless_url: string;
  paperless_username: string;
  paperless_token: string;
  role?: UserRole;
}

export interface UserUpdate {
  email?: string;
  paperless_url?: string;
  paperless_username?: string;
  paperless_token?: string;
  is_active?: boolean;
  timezone?: string;
}

export interface UserPasswordChange {
  current_password: string;
  new_password: string;
}

export interface PaperlessCredentialsUpdate {
  paperless_url: string;
  paperless_username: string;
  paperless_token: string;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

// Document types
export type ProcessingStatus = 'queued' | 'processing' | 'success' | 'failed' | 'pending_approval';

export interface ProcessingResult {
  correspondent?: string;
  correspondent_confidence?: number;
  document_type?: string;
  document_type_confidence?: number;
  tags: string[];
  tag_confidences: number[];
  document_date?: string;
  date_confidence?: number;
  title?: string;
  title_confidence?: number;
  overall_confidence: number;
}

export interface ProcessedDocument {
  id: string;
  user_id: string;
  paperless_document_id: number;
  processed_at: string;
  status: ProcessingStatus;
  confidence_score?: number;
  original_data?: Record<string, any>;
  suggested_data?: Record<string, any>;
  applied_data?: Record<string, any>;
  error_message?: string;
  processing_time_ms?: number;
  reprocess_count: number;
}

export interface ProcessedDocumentDetail extends ProcessedDocument {
  can_reprocess: boolean;
  paperless_url?: string;
}

export interface DocumentStatsResponse {
  total: number;
  success: number;
  failed: number;
  pending_approval: number;
  success_rate: number;
  avg_processing_time_ms?: number;
  avg_confidence?: number;
}

export interface DocumentFilterRequest {
  status?: ProcessingStatus;
  start_date?: string;
  end_date?: string;
  min_confidence?: number;
  limit?: number;
  offset?: number;
}

export interface DocumentReprocessRequest {
  document_ids: number[];
  force?: boolean;
}

// Queue types
export type QueueStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface QueueItem {
  id: string;
  user_id: string;
  paperless_document_id: number;
  priority: number;
  status: QueueStatus;
  queued_at: string;
  started_at?: string;
  completed_at?: string;
  retry_count: number;
  last_error?: string;
}

export interface QueueStatsResponse {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
  estimated_time_remaining?: number;
}

export interface QueueStatusResponse {
  stats: QueueStatsResponse;
  current_items: QueueItem[];
  is_paused: boolean;
  processing_mode: string;
}

// Config types
export interface ConfigUpdateRequest {
  section: string;
  data: Record<string, any>;
}

export interface ConfigSectionResponse {
  section: string;
  data: Record<string, any>;
  is_default: boolean;
}

export interface ConfigResponse {
  app: Record<string, any>;
  database: Record<string, any>;
  ai: Record<string, any>;
  processing: Record<string, any>;
  tagging: Record<string, any>;
  naming: Record<string, any>;
  learning: Record<string, any>;
  approval_workflow: Record<string, any>;
  auto_creation: Record<string, any>;
  notifications: Record<string, any>;
}

export interface AIModelResponse {
  name: string;
  size?: string;
  parameter_count?: string;
  quantization?: string;
  is_available: boolean;
}

export interface AIModelsListResponse {
  models: AIModelResponse[];
  current_model: string;
}

export interface PromptUpdateRequest {
  prompt_type: string;
  content: string;
}

export interface PromptResponse {
  prompt_type: string;
  content: string;
  version: number;
  created_at: string;
  is_active: boolean;
}

// Dashboard types
export interface DashboardStats {
  documents_today: number;
  documents_week: number;
  documents_total: number;
  success_rate: number;
  avg_processing_time: number;
  queue_stats: QueueStatsResponse;
  recent_documents: ProcessedDocument[];
  alerts: Alert[];
}

export interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
  document_id?: string;
}

// Success rate data point for charts
export interface SuccessRateDataPoint {
  date: string;
  success_rate: number;
  total: number;
}

// Daily metrics types
export interface DailyMetrics {
  id: string;
  user_id: string;
  date: string;
  total_documents: number;
  successful_documents: number;
  failed_documents: number;
  avg_confidence_score: number | null;
  avg_processing_time_ms: number | null;
  created_at: string;
  updated_at: string;
}

export interface DailyMetricsResponse {
  today: DailyMetrics | null;
  yesterday: DailyMetrics | null;
  documents_change?: number;
  documents_change_percent?: number;
  confidence_change?: number;
  processing_time_change?: number;
}
