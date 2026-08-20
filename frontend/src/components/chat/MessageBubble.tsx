import React from 'react';
import type { ChatMessage } from '../../context/ChatContext';
import { SqlViewer } from './SqlViewer';
import { Visualizer } from './Visualizer';
import { Bot, AlertCircle } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          marginBottom: '20px',
          padding: '0 8px',
        }}
      >
        <div style={{ maxWidth: '75%', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <div
            style={{
              background: 'var(--primary-gradient)',
              color: '#ffffff',
              padding: '12px 18px',
              borderRadius: '16px 16px 4px 16px',
              fontSize: '0.92rem',
              lineHeight: 1.5,
              boxShadow: 'var(--shadow-sm)',
              wordBreak: 'break-word',
            }}
          >
            {message.content}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px', paddingRight: '4px' }}>
            {message.timestamp}
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message
  const res = message.chatResponse;
  const hasSql = !!(res && res.sql_query);
  const hasData = !!(res && res.columns && res.columns.length > 0);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        marginBottom: '24px',
        padding: '0 8px',
      }}
    >
      {/* Assistant Avatar */}
      <div
        style={{
          width: '34px',
          height: '34px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--primary-gradient)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: '2px',
          boxShadow: 'var(--shadow-glow)',
        }}
      >
        <Bot size={18} />
      </div>

      <div style={{ flex: 1, maxWidth: 'calc(100% - 46px)' }}>
        {/* Assistant Header & Timestamp */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            ZeroSQL Copilot
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {message.timestamp}
          </span>
        </div>

        {/* Loading State Skeleton */}
        {message.isLoading ? (
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <span className="spinner" style={{ width: '16px', height: '16px' }} />
            <span style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
              Reasoning across database schema and running validated SQL query...
            </span>
          </div>
        ) : message.error ? (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '14px 18px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              color: 'var(--error-text)',
            }}
          >
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>Query Execution Notice</div>
              <div style={{ fontSize: '0.84rem', marginTop: '2px', opacity: 0.9 }}>{message.error}</div>
            </div>
          </div>
        ) : (
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '18px 22px',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            {/* Natural Language Answer */}
            {message.content && (
              <div
                style={{
                  fontSize: '0.92rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  marginBottom: hasSql || hasData ? '14px' : '0',
                }}
              >
                {message.content}
              </div>
            )}

            {/* Generated SQL Accordion */}
            {hasSql && (
              <SqlViewer
                sql={res!.sql_query!}
                validationPassed={res!.validation_passed}
                executionTimeMs={res!.execution_time_ms}
              />
            )}

            {/* Visualization & Tabular Results */}
            {hasData && (
              <Visualizer
                columns={res!.columns}
                rows={res!.rows}
                visualizationType={res!.visualization_type}
                rowCount={res!.row_count}
                executionTimeMs={res!.execution_time_ms}
                tableName={res!.table_name}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
};
