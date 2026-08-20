import React from 'react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '48px 24px',
        color: 'var(--text-secondary)',
      }}
    >
      {icon && <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>{icon}</div>}
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.875rem', maxWidth: '420px', marginBottom: '20px', lineHeight: 1.6 }}>
        {description}
      </p>
      {action}
    </div>
  );
};
