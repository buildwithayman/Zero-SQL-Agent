import React, { useState, useEffect } from 'react';
import { healthService } from '../../services/healthService';
import type { HealthResponse } from '../../types/api';
import { RefreshCw } from 'lucide-react';

export const BackendStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await healthService.getHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Offline');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Periodic health check ping every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const isOnline = health && health.status === 'ok' && health.database.healthy;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'var(--bg-surface-elevated)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-full)',
        padding: '4px 12px',
        fontSize: '0.78rem',
        fontWeight: 500,
      }}
      title={
        isOnline
          ? `Connected to ${health?.app_name} (${health?.version}) | DB: ${health?.database.database_name || 'PostgreSQL'} (${health?.database.total_tables} tables)`
          : error || 'Connecting to backend...'
      }
    >
      <span className={`status-dot ${loading ? 'loading' : isOnline ? 'online' : 'offline'}`} />
      <span style={{ color: isOnline ? 'var(--text-primary)' : 'var(--error-text)' }}>
        {loading && !health
          ? 'Connecting...'
          : isOnline
          ? `Backend Online (${health?.database.total_tables} Tables)`
          : 'Backend Offline'}
      </span>
      <button
        onClick={fetchStatus}
        style={{
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          padding: '2px',
        }}
        title="Refresh Status"
      >
        <RefreshCw size={12} className={loading ? 'spinner' : ''} />
      </button>
    </div>
  );
};
