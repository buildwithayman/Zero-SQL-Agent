/**
 * Dataset Schema & Prompt API Service
 * Interacts with FastAPI /api/v1/datasets/{dataset_id}/schema and /prompts endpoints.
 */

import { api } from './api';
import type { DatasetSchemaResponse, DatasetPromptsResponse } from '../types/api';

export const datasetService = {
  /**
   * Fetches the dynamic schema and column metadata for an imported dataset.
   */
  getDatasetSchema: async (datasetId: string): Promise<DatasetSchemaResponse> => {
    return await api.get<DatasetSchemaResponse>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/schema`);
  },

  /**
   * Fetches schema-driven suggested analytical questions for a dataset.
   */
  getDatasetPrompts: async (datasetId: string): Promise<DatasetPromptsResponse> => {
    return await api.get<DatasetPromptsResponse>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/prompts`);
  },
};
