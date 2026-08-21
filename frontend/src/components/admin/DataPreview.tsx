import React from 'react';
import type { DatasetPreview } from '../../types/api';
import { Eye } from 'lucide-react';

interface DataPreviewProps {
  preview: DatasetPreview;
}

export const DataPreview: React.FC<DataPreviewProps> = ({ preview }) => {
  if (!preview || !preview.records || preview.records.length === 0) {
    return null;
  }

  const { columns, records, total_rows, total_columns, preview_rows } = preview;

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
      {/* Header */}
      <div
        style={{
          padding: '12px 18px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Eye size={16} style={{ color: 'var(--primary-500)' }} />
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Parsed Data Preview
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          <span>
            Previewing <strong>{preview_rows}</strong> of <strong>{total_rows.toLocaleString()}</strong> rows
          </span>
          <span>•</span>
          <span>
            <strong>{total_columns}</strong> columns
          </span>
        </div>
      </div>

      {/* Preview Table */}
      <div style={{ overflowX: 'auto', maxHeight: '360px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'rgba(30, 41, 59, 0.7)', borderBottom: '1px solid var(--border-strong)' }}>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  style={{
                    padding: '10px 14px',
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((row, rIdx) => (
              <tr
                key={rIdx}
                style={{
                  background: rIdx % 2 === 0 ? 'var(--bg-surface)' : 'rgba(30, 41, 59, 0.3)',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                {columns.map((col, cIdx) => {
                  const val = row[col];
                  return (
                    <td
                      key={cIdx}
                      style={{
                        padding: '8px 14px',
                        color: val === null || val === undefined ? 'var(--text-muted)' : 'var(--text-primary)',
                        fontStyle: val === null || val === undefined ? 'italic' : 'normal',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {val === null || val === undefined ? '—' : String(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
