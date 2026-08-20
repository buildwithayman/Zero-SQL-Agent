/**
 * Centralized Fetch-based API Client for ZeroSQL AI Backend
 */

import type { ApiError } from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private getAuthHeader(): Record<string, string> {
    const token = localStorage.getItem('zerosql_admin_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      let errorDetail: any = null;

      try {
        const errorJson = await response.json();
        if (errorJson && errorJson.detail) {
          if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail;
          } else if (Array.isArray(errorJson.detail)) {
            errorMessage = errorJson.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
          }
          errorDetail = errorJson.detail;
        }
      } catch {
        // Response was not JSON
      }

      const error: ApiError = {
        message: errorMessage,
        status: response.status,
        detail: errorDetail,
      };
      throw error;
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json() as Promise<T>;
  }

  public async get<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`);
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null) {
          url.searchParams.append(key, String(val));
        }
      });
    }

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          ...this.getAuthHeader(),
        },
      });
      return await this.handleResponse<T>(response);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        message: err.message || 'Network connection error. Is the FastAPI backend running?',
        status: 0,
      } as ApiError;
    }
  }

  public async post<T>(path: string, body?: any): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...this.getAuthHeader(),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      return await this.handleResponse<T>(response);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        message: err.message || 'Network connection error. Is the FastAPI backend running?',
        status: 0,
      } as ApiError;
    }
  }

  public async postForm<T>(path: string, formData: FormData): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          ...this.getAuthHeader(),
        },
        body: formData,
      });
      return await this.handleResponse<T>(response);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        message: err.message || 'Network connection error. Is the FastAPI backend running?',
        status: 0,
      } as ApiError;
    }
  }

  public async delete<T>(path: string): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          ...this.getAuthHeader(),
        },
      });
      return await this.handleResponse<T>(response);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        message: err.message || 'Network connection error. Is the FastAPI backend running?',
        status: 0,
      } as ApiError;
    }
  }
}

export const api = new ApiClient(BASE_URL);
