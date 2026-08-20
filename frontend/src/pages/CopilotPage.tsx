import React from 'react';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useDataset } from '../context/DatasetContext';
import { NavLink } from 'react-router-dom';
import { 
  BotMessageSquare, 
  Sparkles, 
  Database, 
  ShieldAlert, 
  BarChart3, 
  ArrowRight,
  Layers
} from 'lucide-react';

export const CopilotPage: React.FC = () => {
  const { activeDataset } = useDataset();
  const hasActiveDataset = !!(activeDataset.datasetName || activeDataset.tableName);

  return (
    <div>
      <PageHeader
        title="AI SQL Copilot"
        description="Query relational databases and dynamic datasets using natural language. Get instant SQL, verified results, and chart analytics."
        badge={<Badge variant="info">Enterprise V2</Badge>}
        action={
          <NavLink to="/hub">
            <Button variant="primary" icon={<Database size={16} />}>
              Explore Dataset Hub
            </Button>
          </NavLink>
        }
      />

      {/* Active Dataset Focus Banner */}
      <div
        style={{
          background: hasActiveDataset
            ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(99, 102, 241, 0.15) 100%)'
            : 'var(--bg-surface)',
          border: hasActiveDataset ? '1px solid rgba(59, 130, 246, 0.35)' : '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '18px 24px',
          marginBottom: '28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              background: hasActiveDataset ? 'var(--primary-gradient)' : 'var(--bg-surface-elevated)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {hasActiveDataset ? <Sparkles size={20} /> : <Database size={20} />}
          </div>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: hasActiveDataset ? 'var(--primary-500)' : 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {hasActiveDataset ? 'Active Analysis Context' : 'General Schema Context'}
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
              {hasActiveDataset ? (
                <span>
                  {activeDataset.datasetName}{' '}
                  <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
                    (Table: <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-500)' }}>{activeDataset.tableName}</code>)
                  </span>
                </span>
              ) : (
                'No Specific Dataset Selected'
              )}
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '3px' }}>
              {hasActiveDataset
                ? 'AI queries will prioritize this active dataset and its schema metadata.'
                : 'Select a curated dataset from the Dataset Hub or query across all available tables.'}
            </div>
          </div>
        </div>

        <div>
          <NavLink to="/hub">
            <Button variant="secondary" size="sm" icon={<Layers size={14} />}>
              {hasActiveDataset ? 'Switch Dataset' : 'Browse Datasets'}
            </Button>
          </NavLink>
        </div>
      </div>

      {/* Hero Welcome Card */}
      <Card
        style={{
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
          border: '1px solid var(--border-strong)',
          marginBottom: '28px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ position: 'relative', zIndex: 2, maxWidth: '680px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--primary-500)', fontSize: '0.82rem', fontWeight: 600, marginBottom: '12px' }}>
            <Sparkles size={16} />
            <span>POWERED BY LANGGRAPH & GROQ AI</span>
          </div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 700, marginBottom: '10px', lineHeight: 1.3 }}>
            Natural Language Database Analytics with AST Security
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.6, marginBottom: '20px' }}>
            Ask plain English questions, explore dynamic multi-turn data trends, and view schema-driven suggested prompts without writing SQL.
          </p>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <NavLink to="/hub">
              <Button variant="primary" icon={<ArrowRight size={15} />}>
                Browse 7 Curated Datasets
              </Button>
            </NavLink>
            <NavLink to="/explorer">
              <Button variant="secondary" icon={<Database size={15} />}>
                Inspect Live Schema
              </Button>
            </NavLink>
          </div>
        </div>
      </Card>

      {/* Feature Overview Grid */}
      <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '16px', color: 'var(--text-primary)' }}>
        Core Capabilities
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
        <Card interactive>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(59, 130, 246, 0.15)', color: 'var(--primary-500)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BotMessageSquare size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 600 }}>Multi-Turn AI Reasoning</h4>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MemorySaver Isolation</span>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Maintains conversational context across turns. Follow up with "now sort by salary" or "filter by department" naturally.
          </p>
        </Card>

        <Card interactive>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldAlert size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 600 }}>AST SQL Validator</h4>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Read-Only Guarantee</span>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Multi-stage defense-in-depth token parsing strictly blocks INSERT, UPDATE, DELETE, DROP, and multi-statements.
          </p>
        </Card>

        <Card interactive>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Database size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 600 }}>Dataset Hub Catalog</h4>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Unified Ingestion</span>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            One-click provisioning for popular datasets across Sales, Customer Analytics, Finance, HR, Sports, and Logistics.
          </p>
        </Card>

        <Card interactive>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: 'var(--radius-md)', background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart3 size={20} />
            </div>
            <div>
              <h4 style={{ fontSize: '0.98rem', fontWeight: 600 }}>Automated Visual Charts</h4>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Bar, Line, Pie, Table</span>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Infers chart visualizer hints directly from query dimensions and metrics for immediate visual insights.
          </p>
        </Card>
      </div>
    </div>
  );
};
