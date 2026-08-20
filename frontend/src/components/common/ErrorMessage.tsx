import React from 'react';

interface ErrorMessageProps {
  message: string;
  detail?: string | null;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, detail, onRetry }) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--error-bg)',
        border: '1px solid var(--error-border)',
        color: 'var(--error-text)',
        padding: '16px 20px',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        margin: '12px 0',
      }}
    >
      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>⚠️ {message}</div>
      {detail && <div style={{ fontSize: '0.8rem', opacity: 0.85 }}>{detail}</div>}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            alignSelf: 'flex-start',
            marginTop: '8px',
            padding: '4px 10px',
            background: 'var(--error-border)',
            color: '#fff',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.75rem',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
};
