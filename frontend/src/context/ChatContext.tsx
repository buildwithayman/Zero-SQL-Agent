import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import type { ChatResponse } from '../types/api';
import { chatService } from '../services/chatService';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  chatResponse?: ChatResponse;
  isLoading?: boolean;
  error?: string | null;
}

interface ChatContextType {
  messages: ChatMessage[];
  threadId: string | null;
  isSending: boolean;
  selectedPrompt: string | null;
  setSelectedPrompt: (prompt: string | null) => void;
  clearSelectedPrompt: () => void;
  sendMessage: (content: string, datasetId?: string | null, tableName?: string | null) => Promise<void>;
  newChat: () => void;
  resetChatForDataset: (newDatasetId?: string | null) => void;
}

const ChatContext = createContext<ChatContextType>({
  messages: [],
  threadId: null,
  isSending: false,
  selectedPrompt: null,
  setSelectedPrompt: () => {},
  clearSelectedPrompt: () => {},
  sendMessage: async () => {},
  newChat: () => {},
  resetChatForDataset: () => {},
});

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);

  // Active dataset ID ref to track cross-dataset switches
  const currentDatasetIdRef = useRef<string | null>(null);

  const clearSelectedPrompt = useCallback(() => {
    setSelectedPrompt(null);
  }, []);

  const newChat = useCallback(() => {
    setMessages([]);
    setThreadId(null);
    setSelectedPrompt(null);
  }, []);

  const resetChatForDataset = useCallback((newDatasetId?: string | null) => {
    if (currentDatasetIdRef.current !== newDatasetId) {
      currentDatasetIdRef.current = newDatasetId || null;
      setMessages([]);
      setThreadId(null);
      setSelectedPrompt(null);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, datasetId?: string | null, tableName?: string | null) => {
      const trimmed = content.trim();
      if (!trimmed || isSending) return;

      const userMsgId = `user_${Date.now()}`;
      const assistantMsgId = `assistant_${Date.now() + 1}`;
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const userMsg: ChatMessage = {
        id: userMsgId,
        role: 'user',
        content: trimmed,
        timestamp: now,
      };

      const loadingAssistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: now,
        isLoading: true,
      };

      // Append user message and loading indicator
      setMessages((prev) => [...prev, userMsg, loadingAssistantMsg]);
      setIsSending(true);

      // Clear staged prompt once sent
      if (selectedPrompt === trimmed) {
        setSelectedPrompt(null);
      }

      try {
        const response = await chatService.sendMessage({
          message: trimmed,
          thread_id: threadId,
          dataset_id: datasetId || null,
          table_name: tableName || null,
          model_name: null,
        });

        // Store returned thread ID for multi-turn conversational isolation
        if (response.thread_id) {
          setThreadId(response.thread_id);
        }

        // Replace loading assistant message with real response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: response.answer || 'Query executed successfully.',
                  chatResponse: response,
                  isLoading: false,
                  error: response.success ? null : (response.answer || 'Agent query encountered an error.'),
                }
              : msg
          )
        );
      } catch (err: any) {
        // Handle network / backend failure gracefully
        const errorMessage =
          err.message || 'Unable to connect to the AI Agent. Please check that the FastAPI backend is running.';

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: '',
                  isLoading: false,
                  error: errorMessage,
                }
              : msg
          )
        );
      } finally {
        setIsSending(false);
      }
    },
    [isSending, threadId, selectedPrompt]
  );

  return (
    <ChatContext.Provider
      value={{
        messages,
        threadId,
        isSending,
        selectedPrompt,
        setSelectedPrompt,
        clearSelectedPrompt,
        sendMessage,
        newChat,
        resetChatForDataset,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => useContext(ChatContext);
