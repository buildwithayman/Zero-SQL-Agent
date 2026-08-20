/**
 * Popular Dataset Hub & AI Recommendation Service
 * Communicates with FastAPI /api/v1/datasets/catalog and /api/v1/datasets/recommendations endpoints.
 */

import { api } from './api';
import type {
  CatalogListResponse,
  CategoryListResponse,
  CatalogDatasetSchema,
  DatasetRecommendationRequest,
  DatasetRecommendationResponse,
  UseCatalogDatasetResponse,
} from '../types/api';

export const catalogService = {
  /**
   * Retrieves the catalog of popular datasets, optionally filtered by category.
   */
  getCatalog: async (category?: string): Promise<CatalogListResponse> => {
    const params = category && category !== 'All' ? { category } : undefined;
    return await api.get<CatalogListResponse>('/api/v1/datasets/catalog', params);
  },

  /**
   * Retrieves distinct dataset categories with dataset counts and visual icons.
   */
  getCategories: async (): Promise<CategoryListResponse> => {
    return await api.get<CategoryListResponse>('/api/v1/datasets/catalog/categories');
  },

  /**
   * Retrieves detailed metadata and analytics topics for a specific catalog dataset.
   */
  getCatalogDataset: async (catalogId: string): Promise<CatalogDatasetSchema> => {
    return await api.get<CatalogDatasetSchema>(`/api/v1/datasets/catalog/${encodeURIComponent(catalogId)}`);
  },

  /**
   * Recommends relevant catalog datasets based on natural language intent.
   */
  getRecommendations: async (payload: DatasetRecommendationRequest): Promise<DatasetRecommendationResponse> => {
    return await api.post<DatasetRecommendationResponse>('/api/v1/datasets/recommendations', payload);
  },

  /**
   * Ingests or reuses a catalog dataset via the unified backend pipeline.
   */
  useCatalogDataset: async (catalogId: string): Promise<UseCatalogDatasetResponse> => {
    return await api.post<UseCatalogDatasetResponse>(`/api/v1/datasets/catalog/${encodeURIComponent(catalogId)}/use`);
  },
};
