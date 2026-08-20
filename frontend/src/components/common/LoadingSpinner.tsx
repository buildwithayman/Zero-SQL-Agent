import React from 'react';

export const LoadingSpinner: React.FC<{ label?: string }> = ({ label }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center', padding: '24px' }}>
      <div className="spinner" />
      {label && <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{label}</span>}
    </div>
  );
};
