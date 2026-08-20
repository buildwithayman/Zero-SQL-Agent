import React from 'react';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { UploadCloud } from 'lucide-react';

export const AdminPage: React.FC = () => {
  return (
    <div>
      <PageHeader
        title="Admin Dataset Hub"
        description="Secure admin portal for dataset upload, tabular cleaning, type inference, dynamic table ingestion, and prompt regeneration."
        badge={<Badge variant="error">Admin Only</Badge>}
      />

      <Card>
        <EmptyState
          icon={<UploadCloud size={40} style={{ color: 'var(--primary-500)' }} />}
          title="Secure Ingestion & Management Portal"
          description="In future steps, this page will host the drag-and-drop dataset upload zone (CSV, XLSX, JSON, Parquet), cleaning report visualizer, and dynamic table creation actions."
        />
      </Card>
    </div>
  );
};
