import React from 'react';
import type { CleaningReport as CleaningReportType } from '../../types/api';
import { Sparkles, CheckCircle2 } from 'lucide-react';

interface CleaningReportProps {
  report: CleaningReportType;
}

export const CleaningReport: React.FC<CleaningReportProps> = ({ report }) => {
  if (!report) return null;

  return (
    <div
      style={{
        background: 'var(--bg-app)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
        margin: '16px 0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <Sparkles size={18} style={{ color: 'var(--primary-500)' }} />
        <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Data Cleaning & Sanitization Report
        </h4>
      </div>

      {/* Grid of Cleaning Metrics */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '18px',
        }}
      >
        {/* Rows Card */}
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Rows Processed
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {report.rows_before.toLocaleString()}{' '}
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>→</span>{' '}
            <span style={{ color: '#34d399' }}>{report.rows_after.toLocaleString()}</span>
          </div>
        </div>

        {/* Columns Card */}
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Columns Sanitized
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {report.columns_before}{' '}
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>→</span>{' '}
            <span style={{ color: '#34d399' }}>{report.columns_after}</span>
          </div>
        </div>

        {/* Duplicates Removed */}
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Duplicates Removed
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: report.duplicate_rows_removed > 0 ? '#f59e0b' : 'var(--text-primary)' }}>
            {report.duplicate_rows_removed.toLocaleString()}
          </div>
        </div>

        {/* Empty Rows & Cols */}
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Empty Rows / Columns Filtered
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {report.empty_rows_removed} rows • {report.empty_columns_removed} cols
          </div>
        </div>

        {/* Nulls Preserved */}
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
            Null Values Preserved
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {report.null_values_preserved.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Applied Operations List */}
      {report.operations_performed && report.operations_performed.length > 0 && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.5)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Sanitization Pipeline Steps Applied:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {report.operations_performed.map((op, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-primary)' }}>
                <CheckCircle2 size={13} style={{ color: '#34d399', flexShrink: 0 }} />
                <span>{op}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
