import React from 'react';

interface DataTypeBadgeProps {
  type: string;
}

export const DataTypeBadge: React.FC<DataTypeBadgeProps> = ({ type }) => {
  const upperType = (type || 'TEXT').toUpperCase();

  // Pick semantic styling based on standard PostgreSQL types
  let bg = 'rgba(148, 163, 184, 0.12)';
  let color = '#94a3b8';
  let border = 'rgba(148, 163, 184, 0.25)';

  if (upperType === 'INTEGER' || upperType === 'BIGINT') {
    bg = 'rgba(6, 182, 212, 0.12)';
    color = '#22d3ee';
    border = 'rgba(6, 182, 212, 0.3)';
  } else if (upperType === 'NUMERIC' || upperType === 'DOUBLE PRECISION' || upperType === 'REAL') {
    bg = 'rgba(59, 130, 246, 0.12)';
    color = '#60a5fa';
    border = 'rgba(59, 130, 246, 0.3)';
  } else if (upperType === 'DATE' || upperType === 'TIMESTAMP' || upperType === 'TIMESTAMP WITH TIME ZONE') {
    bg = 'rgba(245, 158, 11, 0.12)';
    color = '#fbbf24';
    border = 'rgba(245, 158, 11, 0.3)';
  } else if (upperType === 'BOOLEAN') {
    bg = 'rgba(16, 185, 129, 0.12)';
    color = '#34d399';
    border = 'rgba(16, 185, 129, 0.3)';
  } else if (upperType === 'TEXT' || upperType === 'VARCHAR') {
    bg = 'rgba(168, 85, 247, 0.12)';
    color = '#c084fc';
    border = 'rgba(168, 85, 247, 0.3)';
  }

  return (
    <span
      style={{
        display: 'inline-block',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.72rem',
        fontWeight: 600,
        padding: '2px 8px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
        letterSpacing: '0.02em',
      }}
    >
      {upperType}
    </span>
  );
};
