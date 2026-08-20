import React from 'react';
import { Download } from 'lucide-react';

interface ExportButtonProps {
  columns: string[];
  rows: Record<string, any>[];
  tableName?: string | null;
}

export const ExportButton: React.FC<ExportButtonProps> = ({
  columns,
  rows,
  tableName,
}) => {
  const hasRows = rows && rows.length > 0;

  const handleExportCSV = () => {
    if (!hasRows || !columns || columns.length === 0) return;

    // Build CSV Header
    const headerRow = columns.map((col) => `"${col.replace(/"/g, '""')}"`).join(',');

    // Build CSV Data Rows
    const dataRows = rows.map((row) =>
      columns
        .map((col) => {
          const val = row[col];
          if (val === null || val === undefined) return '""';
          if (typeof val === 'object') return `"${JSON.stringify(val).replace(/"/g, '""')}"`;
          return `"${String(val).replace(/"/g, '""')}"`;
        })
        .join(',')
    );

    const csvContent = [headerRow, ...dataRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    const filename = `${tableName ? tableName.toLowerCase() : 'query'}-results-${Date.now()}.csv`;
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleExportCSV}
      disabled={!hasRows}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontSize: '0.74rem',
        fontWeight: 500,
        color: hasRows ? 'var(--text-secondary)' : 'var(--text-muted)',
        background: 'var(--bg-surface-elevated)',
        border: '1px solid var(--border-subtle)',
        padding: '3px 9px',
        borderRadius: 'var(--radius-sm)',
        opacity: hasRows ? 1 : 0.5,
        cursor: hasRows ? 'pointer' : 'not-allowed',
      }}
      title={hasRows ? 'Export results as CSV' : 'No data to export'}
    >
      <Download size={12} />
      <span>Export CSV</span>
    </button>
  );
};
