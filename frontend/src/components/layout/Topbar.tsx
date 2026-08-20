import React from 'react';
import { NavLink } from 'react-router-dom';
import { BackendStatus } from '../common/BackendStatus';
import { useDataset } from '../../context/DatasetContext';
import { useAuth } from '../../context/AuthContext';
import { Database, User, LogIn, LogOut } from 'lucide-react';

interface TopbarProps {
  onToggleSidebar?: () => void;
}

export const Topbar: React.FC<TopbarProps> = () => {
  const { activeDataset } = useDataset();
  const { isAuthenticated, username, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 14px',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
          }}
        >
          <Database size={14} style={{ color: 'var(--primary-500)' }} />
          <span>Active Context:</span>
          <strong style={{ color: 'var(--text-primary)' }}>
            {activeDataset.datasetName
              ? `${activeDataset.datasetName} (Table: ${activeDataset.tableName})`
              : 'All Database Tables (Full Schema)'}
          </strong>
        </div>
      </div>

      <div className="topbar-right">
        <BackendStatus />

        {isAuthenticated ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.82rem',
                color: 'var(--text-primary)',
              }}
            >
              <User size={14} style={{ color: 'var(--primary-500)' }} />
              <span>{username || 'Admin'}</span>
            </div>
            <button
              onClick={logout}
              className="btn btn-secondary btn-sm"
              title="Logout"
              style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <LogOut size={13} />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <NavLink to="/login" className="btn btn-secondary btn-sm">
            <LogIn size={13} />
            <span>Admin Login</span>
          </NavLink>
        )}
      </div>
    </header>
  );
};
