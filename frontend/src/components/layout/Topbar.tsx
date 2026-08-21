import React from 'react';
import { NavLink } from 'react-router-dom';
import { BackendStatus } from '../common/BackendStatus';
import { useDataset } from '../../context/DatasetContext';
import { useAuth } from '../../context/AuthContext';
import { Database, User, LogIn, LogOut, X, Sparkles, Menu } from 'lucide-react';

interface TopbarProps {
  onToggleSidebar?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleSidebar }) => {
  const { activeDataset, clearActiveDataset } = useDataset();
  const { isAuthenticated, username, logout } = useAuth();

  const hasActiveDataset = !!(activeDataset.datasetName || activeDataset.tableName);

  return (
    <header className="topbar">
      <div className="topbar-left">
        {/* Mobile Sidebar Toggle Button */}
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="mobile-menu-btn"
            aria-label="Toggle navigation menu"
            style={{
              display: 'none',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px',
              color: 'var(--text-primary)',
              marginRight: '8px',
            }}
          >
            <Menu size={18} />
          </button>
        )}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: hasActiveDataset ? 'rgba(59, 130, 246, 0.1)' : 'var(--bg-surface-elevated)',
            border: hasActiveDataset ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 14px',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
          }}
        >
          {hasActiveDataset ? (
            <Sparkles size={14} style={{ color: 'var(--primary-500)' }} />
          ) : (
            <Database size={14} style={{ color: 'var(--text-muted)' }} />
          )}

          <span>Active Context:</span>

          {hasActiveDataset ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <strong style={{ color: 'var(--text-primary)' }}>
                {activeDataset.datasetName || 'Dataset'}
              </strong>
              {activeDataset.tableName && (
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.74rem',
                    color: 'var(--primary-500)',
                    background: 'rgba(59, 130, 246, 0.15)',
                    padding: '1px 6px',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  {activeDataset.tableName}
                </span>
              )}
              <button
                onClick={clearActiveDataset}
                aria-label="Clear active dataset selection"
                style={{
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '2px',
                  borderRadius: 'var(--radius-sm)',
                }}
                title="Clear Active Dataset"
              >
                <X size={13} />
              </button>
            </div>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No dataset selected (All Database Tables)
            </span>
          )}
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
              aria-label="Sign out of admin session"
              title="Logout"
              style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <LogOut size={13} />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <NavLink to="/login" className="btn btn-secondary btn-sm" aria-label="Sign in to admin portal">
            <LogIn size={13} />
            <span>Admin Login</span>
          </NavLink>
        )}
      </div>
    </header>
  );
};
