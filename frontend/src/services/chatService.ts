/**
 * AI SQL Copilot Chat Service
 * Interacts with FastAPI POST /api/v1/chat endpoint.
 */

import { api } from './api';
import type { ChatRequest, ChatResponse } from '../types/api';

export const chatService = {
  /**
   * Sends a user natural language query to the LangGraph ReAct SQL agent.
   */
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    return await api.post<ChatResponse>('/api/v1/chat', {
      message: request.message.trim(),
      thread_id: request.thread_id || null,
      dataset_id: request.dataset_id || null,
      table_name: request.table_name || null,
      model_name: request.model_name || null,
    });
  },
};
