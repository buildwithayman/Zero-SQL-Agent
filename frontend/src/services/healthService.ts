/**
 * Backend Health Service
 * Handles live pings to /api/v1/health.
 */

import { api } from './api';
import type { HealthResponse } from '../types/api';

export const healthService = {
  getHealth: async (): Promise<HealthResponse> => {
    return await api.get<HealthResponse>('/api/v1/health');
  },
};
