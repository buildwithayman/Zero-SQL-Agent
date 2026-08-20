import React from 'react';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Database, Sparkles, Filter, CheckCircle2 } from 'lucide-react';

export const DatasetHubPage: React.FC = () => {
  return (
    <div>
      <PageHeader
        title="Popular Dataset Hub"
        description="Explore curated industry-standard datasets, AI recommendation engine, and unified one-click PostgreSQL ingestion."
        badge={<Badge variant="success">7 Datasets</Badge>}
        action={
          <Button variant="secondary" icon={<Filter size={15} />}>
            Filter Categories
          </Button>
        }
      />

      <Card style={{ marginBottom: '24px', background: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--primary-500)', marginBottom: '8px', fontWeight: 600, fontSize: '0.85rem' }}>
          <Sparkles size={16} />
          <span>AI RECOMMENDATION ASSISTANT (PREVIEW)</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '16px' }}>
          Ask natural language questions like <em>"I want to analyze customer churn and retention"</em> to receive instant dataset recommendations.
        </p>

        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder="e.g. Find datasets with monthly sales, employee salary records, or financial transactions..."
            disabled
            style={{
              flex: 1,
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
            }}
          />
          <Button variant="primary" disabled>
            Find Datasets
          </Button>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
        {[
          { id: 'superstore_sales', name: 'Superstore Retail Sales', cat: 'Sales & Retail', rows: '9,994', desc: 'Global retail store transaction orders across Furniture, Office Supplies, and Technology.' },
          { id: 'customer_churn', name: 'Customer Churn & Retention', cat: 'Customer Analytics', rows: '7,043', desc: 'Telecom subscriber account profiles, tenure, service contracts, and churn status.' },
          { id: 'financial_transactions', name: 'Financial Banking Transactions', cat: 'Finance & Banking', rows: '12,500', desc: 'Personal credit ledger records including transaction types, merchant categories, and balances.' },
          { id: 'hr_employee_attrition', name: 'HR Employee Organizational Records', cat: 'Human Resources', rows: '1,470', desc: 'Employee demographics, job roles, monthly compensation, and performance metrics.' },
          { id: 'sports_player_performance', name: 'Sports Team & Athlete Analytics', cat: 'Sports & Gaming', rows: '4,500', desc: 'Player statistics, seasonal game metrics, scoring percentages, and rankings.' },
          { id: 'ecommerce_logistics', name: 'E-Commerce Logistics & Shipping', cat: 'Logistics & Supply Chain', rows: '8,200', desc: 'Supply chain delivery logs with carrier transit duration, priority status, and shipment weights.' },
        ].map((item) => (
          <Card key={item.id} interactive>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <Badge variant="info">{item.cat}</Badge>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>~{item.rows} rows</span>
            </div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '6px' }}>{item.name}</h4>
            <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
              {item.desc}
            </p>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', color: '#34d399' }}>
                <CheckCircle2 size={13} />
                <span>Verified Clean</span>
              </div>
              <Button variant="secondary" size="sm" icon={<Database size={13} />} disabled>
                Use Dataset
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
