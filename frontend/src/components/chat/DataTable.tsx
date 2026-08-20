import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface DataTableProps {
  columns: string[];
  rows: Record<string, any>[];
  rowCount?: number;
  executionTimeMs?: number;
}

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  rowCount,
  executionTimeMs,
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    return (
      <div
        style={{
          padding: '16px',
          background: 'var(--bg-app)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-muted)',
          fontSize: '0.82rem',
          textAlign: 'center',
          fontStyle: 'italic',
        }}
      >
        No rows returned.
      </div>
    );
  }

  const totalRows = rows.length;
  const totalPages = Math.ceil(totalRows / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const currentRows = rows.slice(startIndex, startIndex + pageSize);

  const formatCellValue = (val: any) => {
    if (val === null || val === undefined) {
      return <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>—</span>;
    }
    if (typeof val === 'number') {
      return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(2);
    }
    if (typeof val === 'boolean') {
      return val ? 'true' : 'false';
    }
    if (typeof val === 'object') {
      return JSON.stringify(val);
    }
    return String(val);
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
      {/* Table Summary Header */}
      <div
        style={{
          padding: '8px 14px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.74rem',
          color: 'var(--text-secondary)',
        }}
      >
        <div>
          <span>Rows: </span>
          <strong style={{ color: 'var(--text-primary)' }}>{rowCount !== undefined ? rowCount : totalRows}</strong>
          {executionTimeMs !== undefined && (
            <span style={{ marginLeft: '10px', color: 'var(--text-muted)' }}>
              Execution: <strong>{executionTimeMs.toFixed(1)}ms</strong>
            </span>
          )}
        </div>

        {totalPages > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <div style={{ display: 'flex', gap: '2px' }}>
              <button
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                style={{
                  padding: '2px 4px',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: currentPage === 1 ? 'var(--text-muted)' : 'var(--text-primary)',
                  cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                  display: 'flex',
                }}
              >
                <ChevronLeft size={12} />
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                disabled={currentPage === totalPages}
                style={{
                  padding: '2px 4px',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: currentPage === totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
                  cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                  display: 'flex',
                }}
              >
                <ChevronRight size={12} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Table Container */}
      <div style={{ overflowX: 'auto', maxHeight: '420px' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: '0.82rem',
          }}
        >
          <thead>
            <tr
              style={{
                background: 'rgba(30, 41, 59, 0.7)',
                borderBottom: '1px solid var(--border-strong)',
                color: 'var(--text-secondary)',
                fontSize: '0.74rem',
                letterSpacing: '0.04em',
              }}
            >
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  style={{
                    padding: '10px 14px',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, rIdx) => {
              const isEven = rIdx % 2 === 0;
              return (
                <tr
                  key={rIdx}
                  style={{
                    background: isEven ? 'var(--bg-surface)' : 'rgba(30, 41, 59, 0.3)',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  {columns.map((col, cIdx) => (
                    <td
                      key={cIdx}
                      style={{
                        padding: '10px 14px',
                        whiteSpace: 'nowrap',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {formatCellValue(row[col])}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
