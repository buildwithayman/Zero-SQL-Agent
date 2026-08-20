import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import { useDataset } from '../../context/DatasetContext';
import { Send, Sparkles, X } from 'lucide-react';

const MAX_MESSAGE_LENGTH = 2000;

export const ChatInput: React.FC = () => {
  const { isSending, sendMessage, selectedPrompt, clearSelectedPrompt } = useChat();
  const { activeDataset } = useDataset();
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Pre-fill input if a suggested prompt is staged from Explorer or Hub
  useEffect(() => {
    if (selectedPrompt) {
      setInput(selectedPrompt);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [selectedPrompt]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    sendMessage(trimmed, activeDataset.datasetId, activeDataset.tableName);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charCount = input.length;
  const isNearLimit = charCount > 1800;

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-subtle)',
        padding: '16px 24px',
        position: 'sticky',
        bottom: 0,
        zIndex: 20,
      }}
    >
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        {/* Staged Question Banner if selected */}
        {selectedPrompt && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 14px',
              fontSize: '0.78rem',
              color: 'var(--primary-500)',
              marginBottom: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={13} />
              <span>Suggested Question Loaded (Ready to edit or send)</span>
            </div>
            <button
              onClick={() => {
                clearSelectedPrompt();
                setInput('');
              }}
              style={{ color: 'var(--text-muted)', display: 'flex' }}
              title="Clear question"
            >
              <X size={13} />
            </button>
          </div>
        )}

        {/* Input Container Box */}
        <div
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--radius-lg)',
            padding: '12px 16px',
            boxShadow: 'var(--shadow-md)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            transition: 'border-color 0.15s ease',
          }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, MAX_MESSAGE_LENGTH))}
            onKeyDown={handleKeyDown}
            placeholder={
              activeDataset.datasetName
                ? `Ask a question about ${activeDataset.datasetName} (e.g. "What is the average sales by region?")...`
                : 'Ask a question in plain English across database tables...'
            }
            disabled={isSending}
            style={{
              width: '100%',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              resize: 'none',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
              fontSize: '0.92rem',
              lineHeight: 1.5,
              maxHeight: '180px',
            }}
          />

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: '6px',
              borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              <span>
                Press <strong>Enter ↵</strong> to send, <strong>Shift + Enter</strong> for newline
              </span>
              {isNearLimit && (
                <span style={{ color: charCount >= MAX_MESSAGE_LENGTH ? 'var(--error-text)' : 'var(--warning-text)' }}>
                  {charCount}/{MAX_MESSAGE_LENGTH}
                </span>
              )}
            </div>

            <button
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              className="btn btn-primary btn-sm"
              style={{
                borderRadius: 'var(--radius-md)',
                padding: '6px 14px',
                opacity: !input.trim() || isSending ? 0.5 : 1,
              }}
            >
              {isSending ? (
                <span className="spinner" style={{ width: '14px', height: '14px' }} />
              ) : (
                <>
                  <span>Ask Copilot</span>
                  <Send size={13} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
