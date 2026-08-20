import React, { createContext, useContext, useState } from 'react';

interface ChatContextType {
  threadId: string;
  setThreadId: (id: string) => void;
  resetThread: () => void;
  selectedPrompt: string | null;
  setSelectedPrompt: (prompt: string | null) => void;
  clearSelectedPrompt: () => void;
}

const generateThreadId = () => `thread_${Math.random().toString(36).substring(2, 10)}`;

const ChatContext = createContext<ChatContextType>({
  threadId: 'default_session',
  setThreadId: () => {},
  resetThread: () => {},
  selectedPrompt: null,
  setSelectedPrompt: () => {},
  clearSelectedPrompt: () => {},
});

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [threadId, setThreadId] = useState<string>(() => generateThreadId());
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);

  const resetThread = () => {
    setThreadId(generateThreadId());
  };

  const clearSelectedPrompt = () => {
    setSelectedPrompt(null);
  };

  return (
    <ChatContext.Provider
      value={{
        threadId,
        setThreadId,
        resetThread,
        selectedPrompt,
        setSelectedPrompt,
        clearSelectedPrompt,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => useContext(ChatContext);
