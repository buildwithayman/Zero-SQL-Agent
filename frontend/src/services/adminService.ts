/**
 * ZeroSQL Admin Service
 * Interacts with FastAPI /api/v1/admin endpoints for authentication and dataset lifecycle.
 */

import { api } from './api';
import type {
  AdminLoginRequest,
  AdminLoginResponse,
  DatasetUploadResponse,
  DatasetListResponse,
  DatasetMetadataSchema,
  DatasetProcessResponse,
  DatasetImportRequest,
  DatasetImportResponse,
  DatasetDeleteResponse,
  DatasetPromptsResponse,
} from '../types/api';

export const adminService = {
  /**
   * Authenticates admin user and returns Bearer access token.
   */
  login: async (credentials: AdminLoginRequest): Promise<AdminLoginResponse> => {
    return await api.post<AdminLoginResponse>('/api/v1/admin/auth/login', credentials);
  },

  /**
   * Uploads a tabular dataset (CSV, XLSX, JSON, Parquet).
   */
  uploadDataset: async (file: File, datasetName?: string): Promise<DatasetUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (datasetName && datasetName.trim()) {
      formData.append('dataset_name', datasetName.trim());
    }
    return await api.postForm<DatasetUploadResponse>('/api/v1/admin/datasets/upload', formData);
  },

  /**
   * Lists all uploaded datasets with metadata and processing status.
   */
  getDatasets: async (): Promise<DatasetListResponse> => {
    return await api.get<DatasetListResponse>('/api/v1/admin/datasets');
  },

  /**
   * Retrieves single dataset detailed metadata.
   */
  getDataset: async (datasetId: string): Promise<DatasetMetadataSchema> => {
    return await api.get<DatasetMetadataSchema>(`/api/v1/admin/datasets/${encodeURIComponent(datasetId)}`);
  },

  /**
   * Triggers dataset parsing, cleaning, profiling, type inference, and prompt suggestions.
   */
  processDataset: async (datasetId: string): Promise<DatasetProcessResponse> => {
    return await api.post<DatasetProcessResponse>(`/api/v1/admin/datasets/${encodeURIComponent(datasetId)}/process`);
  },

  /**
   * Explicitly imports processed dataset into PostgreSQL.
   */
  importDataset: async (datasetId: string, customTableName?: string): Promise<DatasetImportResponse> => {
    const body: DatasetImportRequest = {
      custom_table_name: customTableName && customTableName.trim() ? customTableName.trim() : null,
    };
    return await api.post<DatasetImportResponse>(`/api/v1/admin/datasets/${encodeURIComponent(datasetId)}/import`, body);
  },

  /**
   * Deletes dataset from disk and database according to backend lifecycle.
   */
  deleteDataset: async (datasetId: string): Promise<DatasetDeleteResponse> => {
    return await api.delete<DatasetDeleteResponse>(`/api/v1/admin/datasets/${encodeURIComponent(datasetId)}`);
  },

  /**
   * Regenerates prompt suggestions for an admin dataset.
   */
  regeneratePrompts: async (datasetId: string): Promise<DatasetPromptsResponse> => {
    return await api.post<DatasetPromptsResponse>(
      `/api/v1/admin/datasets/${encodeURIComponent(datasetId)}/prompts/regenerate`
    );
  },
};
