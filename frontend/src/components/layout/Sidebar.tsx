import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  BotMessageSquare, 
  Database, 
  Search, 
  Settings, 
  ShieldCheck
} from 'lucide-react';

interface SidebarProps {
  isOpen?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = false }) => {
  const navItems = [
    { to: '/copilot', label: 'AI Copilot', icon: <BotMessageSquare size={18} /> },
    { to: '/hub', label: 'Dataset Hub', icon: <Database size={18} /> },
    { to: '/explorer', label: 'Data Explorer', icon: <Search size={18} /> },
    { to: '/admin', label: 'Admin Hub', icon: <Settings size={18} /> },
  ];

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="brand-logo">⚡</div>
        <div>
          <div className="brand-title">ZeroSQL AI</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            ENTERPRISE COPILOT
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div style={{ padding: '0 8px 8px', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Navigation
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldCheck size={16} />
          </div>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600 }}>AST Guardrails Active</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Read-Only Enforced</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
