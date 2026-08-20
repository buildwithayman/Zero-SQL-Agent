/**
 * ZeroSQL AI - TypeScript API Types
 * Mirrors FastAPI Pydantic schemas exactly.
 */

// ==============================================================================
// 1. Health Types
// ==============================================================================

export interface DatabaseHealthStatus {
  status: 'connected' | 'disconnected';
  healthy: boolean;
  database_name?: string | null;
  server_version?: string | null;
  total_tables: number;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  database: DatabaseHealthStatus;
}

// ==============================================================================
// 2. Authentication Types
// ==============================================================================

export interface AdminLoginRequest {
  username: string;
  password: string;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  username: string;
  expires_in_minutes: number;
}

// ==============================================================================
// 3. Chat & AI Agent Types
// ==============================================================================

export interface ChatRequest {
  message: string;
  thread_id?: string | null;
  dataset_id?: string | null;
  table_name?: string | null;
  model_name?: string | null;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  sql_query?: string | null;
  validation_passed: boolean;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  thread_id: string;
  dataset_id?: string | null;
  table_name?: string | null;
  visualization_type?: 'bar' | 'line' | 'pie' | 'table' | null;
}

// ==============================================================================
// 4. Dataset Management & Ingestion Types
// ==============================================================================

export interface DatasetMetadataSchema {
  dataset_id: string;
  dataset_name: string;
  original_filename: string;
  stored_path: string;
  file_format: string;
  file_size_bytes: number;
  file_size_formatted: string;
  upload_timestamp: string;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED' | 'DELETED';
  uploaded_by: string;
  table_name?: string | null;
  row_count?: number | null;
  column_count?: number | null;
  suggested_prompts?: string[];
  error_message?: string | null;
}

export interface DatasetUploadResponse {
  status: string;
  message: string;
  dataset: DatasetMetadataSchema;
}

export interface DatasetListResponse {
  total_count: number;
  datasets: DatasetMetadataSchema[];
}

export interface DatasetDeleteResponse {
  status: string;
  message: string;
  deleted_dataset_id: string;
}

export interface ColumnProfile {
  original_name: string;
  normalized_name: string;
  detected_type: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  sample_value?: string | null;
}

export interface CleaningReport {
  rows_before: number;
  rows_after: number;
  columns_before: number;
  columns_after: number;
  duplicate_rows_removed: number;
  empty_rows_removed: number;
  empty_columns_removed: number;
  columns_normalized: number;
  null_values_preserved: number;
  operations_performed: string[];
}

export interface DatasetPreview {
  total_rows: number;
  total_columns: number;
  preview_rows: number;
  columns: string[];
  records: Record<string, any>[];
}

export interface DatasetProcessResponse {
  status: string;
  dataset_id: string;
  dataset_name: string;
  suggested_table_name: string;
  preview: DatasetPreview;
  schema_detected: ColumnProfile[];
  cleaning_report: CleaningReport;
  suggested_prompts?: string[];
}

export interface DatasetImportRequest {
  custom_table_name?: string | null;
}

export interface DatasetImportResponse {
  status: string;
  message: string;
  dataset_id: string;
  table_name: string;
  rows_imported: number;
  columns_imported: number;
  suggested_prompts: string[];
}

export interface DatasetPromptsResponse {
  dataset_id: string;
  dataset_name: string;
  table_name?: string | null;
  suggested_prompts: string[];
}

export interface DatasetSchemaResponse {
  dataset_id: string;
  dataset_name: string;
  table_name: string;
  columns: ColumnProfile[];
}

// ==============================================================================
// 5. Popular Dataset Hub & Recommendation Types
// ==============================================================================

export interface CatalogDatasetSchema {
  catalog_id: string;
  name: string;
  description: string;
  category: string;
  source_name: string;
  source_url: string;
  download_url?: string | null;
  file_format: string;
  approx_size: string;
  approx_rows: number;
  tags: string[];
  analytics_topics: string[];
  is_imported: boolean;
  imported_dataset_id?: string | null;
  imported_table_name?: string | null;
}

export interface CatalogListResponse {
  total_count: number;
  categories: string[];
  datasets: CatalogDatasetSchema[];
}

export interface CategoryInfo {
  name: string;
  count: number;
  icon: string;
}

export interface CategoryListResponse {
  total_categories: number;
  categories: CategoryInfo[];
}

export interface DatasetRecommendationRequest {
  query: string;
  category?: string | null;
  limit?: number;
}

export interface DatasetRecommendationResponse {
  query: string;
  recommended_datasets: CatalogDatasetSchema[];
  reasoning?: string | null;
}

export interface UseCatalogDatasetResponse {
  status: string;
  message: string;
  dataset_id: string;
  table_name: string;
  rows_imported: number;
  suggested_prompts: string[];
  was_reused: boolean;
}

// ==============================================================================
// 6. Generic API Error Type
// ==============================================================================

export interface ApiError {
  message: string;
  status?: number;
  detail?: string | any;
}
