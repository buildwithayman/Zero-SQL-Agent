import React from 'react';
import type { ColumnProfile } from '../../types/api';
import { DataTypeBadge } from './DataTypeBadge';
import { Card } from '../common/Card';

interface SchemaTableProps {
  columns: ColumnProfile[];
}

export const SchemaTable: React.FC<SchemaTableProps> = ({ columns }) => {
  if (!columns || columns.length === 0) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>
          No column definitions available for this dataset.
        </div>
      </Card>
    );
  }

  return (
    <Card style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: '0.86rem',
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                borderBottom: '1px solid var(--border-strong)',
                color: 'var(--text-secondary)',
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              <th style={{ padding: '14px 20px', fontWeight: 600 }}>#</th>
              <th style={{ padding: '14px 20px', fontWeight: 600 }}>Column Identifier</th>
              <th style={{ padding: '14px 20px', fontWeight: 600 }}>PostgreSQL Type</th>
              <th style={{ padding: '14px 20px', fontWeight: 600 }}>Null Count (%)</th>
              <th style={{ padding: '14px 20px', fontWeight: 600 }}>Unique Values</th>
              <th style={{ padding: '14px 20px', fontWeight: 600 }}>Sample Value</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((col, idx) => {
              const isEven = idx % 2 === 0;
              const hasNulls = col.null_count > 0;

              return (
                <tr
                  key={col.normalized_name || idx}
                  style={{
                    backgroundColor: isEven ? 'var(--bg-surface)' : 'rgba(30, 41, 59, 0.4)',
                    borderBottom: '1px solid var(--border-subtle)',
                    transition: 'background-color 0.15s ease',
                  }}
                >
                  {/* Row Number */}
                  <td style={{ padding: '14px 20px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                    {idx + 1}
                  </td>

                  {/* Column Identifier */}
                  <td style={{ padding: '14px 20px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {col.original_name}
                      </span>
                      {col.normalized_name !== col.original_name && (
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.72rem',
                            color: 'var(--text-muted)',
                          }}
                        >
                          → {col.normalized_name}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Data Type */}
                  <td style={{ padding: '14px 20px' }}>
                    <DataTypeBadge type={col.detected_type} />
                  </td>

                  {/* Null Count (%) */}
                  <td style={{ padding: '14px 20px' }}>
                    <span
                      style={{
                        color: hasNulls ? '#fbbf24' : 'var(--text-secondary)',
                        fontWeight: hasNulls ? 600 : 400,
                      }}
                    >
                      {col.null_count.toLocaleString()}{' '}
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        ({col.null_percentage.toFixed(1)}%)
                      </span>
                    </span>
                  </td>

                  {/* Unique Count */}
                  <td style={{ padding: '14px 20px', color: 'var(--text-secondary)' }}>
                    {col.unique_count > 0 ? col.unique_count.toLocaleString() : '—'}
                  </td>

                  {/* Sample Value */}
                  <td style={{ padding: '14px 20px' }}>
                    {col.sample_value !== null && col.sample_value !== undefined && col.sample_value !== '' ? (
                      <code
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.76rem',
                          color: 'var(--primary-500)',
                          background: 'var(--bg-surface-elevated)',
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-sm)',
                          display: 'inline-block',
                          maxWidth: '220px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                        title={String(col.sample_value)}
                      >
                        {String(col.sample_value)}
                      </code>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.76rem' }}>
                        —
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
