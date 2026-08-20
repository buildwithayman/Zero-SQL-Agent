import React, { useState } from 'react';
import { 
  Code2, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  ShieldAlert 
} from 'lucide-react';

interface SqlViewerProps {
  sql: string;
  validationPassed?: boolean;
  executionTimeMs?: number;
}

export const SqlViewer: React.FC<SqlViewerProps> = ({
  sql,
  validationPassed = true,
  executionTimeMs,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [copied, setCopied] = useState(false);

  if (!sql) return null;

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        background: 'var(--bg-app)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        margin: '12px 0',
      }}
    >
      {/* Header Bar */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          padding: '8px 14px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderBottom: isOpen ? '1px solid var(--border-subtle)' : 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Code2 size={15} style={{ color: 'var(--primary-500)' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Generated SQL
          </span>

          {/* Validation Status Pill */}
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.7rem',
              fontWeight: 600,
              padding: '1px 7px',
              borderRadius: 'var(--radius-full)',
              background: validationPassed ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
              color: validationPassed ? '#34d399' : '#f87171',
              border: `1px solid ${validationPassed ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            }}
          >
            {validationPassed ? <ShieldCheck size={11} /> : <ShieldAlert size={11} />}
            <span>{validationPassed ? 'Read-Only Validated' : 'Validation Failed'}</span>
          </span>

          {executionTimeMs !== undefined && executionTimeMs > 0 && (
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              ({executionTimeMs.toFixed(1)}ms)
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleCopy}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.72rem',
              color: copied ? '#34d399' : 'var(--text-muted)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              padding: '3px 8px',
              borderRadius: 'var(--radius-sm)',
            }}
            title="Copy SQL query"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <span style={{ color: 'var(--text-muted)', display: 'flex' }}>
            {isOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          </span>
        </div>
      </div>

      {/* SQL Code Body */}
      {isOpen && (
        <div style={{ padding: '12px 16px', overflowX: 'auto', backgroundColor: '#050811' }}>
          <pre
            style={{
              margin: 0,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82rem',
              lineHeight: 1.5,
              color: '#93c5fd',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            <code>{sql}</code>
          </pre>
        </div>
      )}
    </div>
  );
};
