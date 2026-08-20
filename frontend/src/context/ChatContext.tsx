import React, { createContext, useContext, useState } from 'react';

interface ChatContextType {
  threadId: string;
  setThreadId: (id: string) => void;
  resetThread: () => void;
}

const generateThreadId = () => `thread_${Math.random().toString(36).substring(2, 10)}`;

const ChatContext = createContext<ChatContextType>({
  threadId: 'default_session',
  setThreadId: () => {},
  resetThread: () => {},
});

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [threadId, setThreadId] = useState<string>(() => generateThreadId());

  const resetThread = () => {
    setThreadId(generateThreadId());
  };

  return (
    <ChatContext.Provider
      value={{
        threadId,
        setThreadId,
        resetThread,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => useContext(ChatContext);
