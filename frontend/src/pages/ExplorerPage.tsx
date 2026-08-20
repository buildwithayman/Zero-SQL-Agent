import React from 'react';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { Table } from 'lucide-react';

export const ExplorerPage: React.FC = () => {
  return (
    <div>
      <PageHeader
        title="Database Schema Explorer"
        description="Inspect relational table structures, data types, null distributions, and preview records."
        badge={<Badge variant="neutral">Schema Viewer</Badge>}
      />

      <Card>
        <EmptyState
          icon={<Table size={36} style={{ color: 'var(--primary-500)' }} />}
          title="Data Matrix & Schema Explorer"
          description="In future steps, this page will provide live column definitions, primary keys, null percentages, and interactive table previews."
        />
      </Card>
    </div>
  );
};
