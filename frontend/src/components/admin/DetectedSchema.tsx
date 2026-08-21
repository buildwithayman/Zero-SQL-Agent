import React from 'react';
import type { ColumnProfile } from '../../types/api';
import { DataTypeBadge } from '../explorer/DataTypeBadge';
import { Binary } from 'lucide-react';

interface DetectedSchemaProps {
  schema: ColumnProfile[];
}

export const DetectedSchema: React.FC<DetectedSchemaProps> = ({ schema }) => {
  if (!schema || schema.length === 0) return null;

  return (
    <div
      style={{
        background: 'var(--bg-app)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        margin: '16px 0',
      }}
    >
      <div
        style={{
          padding: '12px 18px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <Binary size={16} style={{ color: 'var(--primary-500)' }} />
        <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Inferred PostgreSQL Schema & Types ({schema.length} columns)
        </span>
      </div>

      <div style={{ overflowX: 'auto', maxHeight: '360px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'rgba(30, 41, 59, 0.7)', borderBottom: '1px solid var(--border-strong)' }}>
              <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Normalized Column Name
              </th>
              <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Original Header
              </th>
              <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Detected Type
              </th>
              <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Nulls
              </th>
              <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Unique Values
              </th>
              <th style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Sample Value
              </th>
            </tr>
          </thead>
          <tbody>
            {schema.map((col, idx) => (
              <tr
                key={idx}
                style={{
                  background: idx % 2 === 0 ? 'var(--bg-surface)' : 'rgba(30, 41, 59, 0.3)',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <td style={{ padding: '9px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  <code style={{ fontFamily: 'var(--font-mono)', color: '#93c5fd' }}>
                    {col.normalized_name}
                  </code>
                </td>
                <td style={{ padding: '9px 14px', color: 'var(--text-secondary)' }}>
                  {col.original_name}
                </td>
                <td style={{ padding: '9px 14px' }}>
                  <DataTypeBadge type={col.detected_type} />
                </td>
                <td style={{ padding: '9px 14px', color: col.null_count > 0 ? '#f59e0b' : 'var(--text-muted)' }}>
                  {col.null_count.toLocaleString()} ({col.null_percentage.toFixed(1)}%)
                </td>
                <td style={{ padding: '9px 14px', color: 'var(--text-primary)' }}>
                  {col.unique_count.toLocaleString()}
                </td>
                <td style={{ padding: '9px 14px', color: 'var(--text-secondary)', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {col.sample_value ? String(col.sample_value) : <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
