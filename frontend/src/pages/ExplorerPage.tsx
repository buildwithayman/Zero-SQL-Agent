import React from 'react';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { useDataset } from '../context/DatasetContext';
import { NavLink } from 'react-router-dom';
import { Table, Database, Sparkles } from 'lucide-react';

export const ExplorerPage: React.FC = () => {
  const { activeDataset } = useDataset();
  const hasActiveDataset = !!(activeDataset.datasetName || activeDataset.tableName);

  return (
    <div>
      <PageHeader
        title="Database Schema Explorer"
        description="Inspect relational table structures, data types, null distributions, and preview records."
        badge={
          hasActiveDataset ? (
            <Badge variant="success" icon={<Sparkles size={12} />}>
              {activeDataset.datasetName}
            </Badge>
          ) : (
            <Badge variant="neutral">Schema Viewer</Badge>
          )
        }
      />

      <Card>
        <EmptyState
          icon={<Table size={36} style={{ color: 'var(--primary-500)' }} />}
          title={
            hasActiveDataset
              ? `Data Matrix for ${activeDataset.datasetName}`
              : 'Data Matrix & Schema Explorer'
          }
          description={
            hasActiveDataset
              ? `Active table: ${activeDataset.tableName}. In future steps, this page will provide live column definitions, primary keys, null percentages, and interactive table previews.`
              : 'Select a dataset from the Dataset Hub to focus the schema explorer and preview its underlying PostgreSQL table columns.'
          }
          action={
            !hasActiveDataset ? (
              <NavLink to="/hub">
                <Button variant="primary" icon={<Database size={14} />}>
                  Browse Dataset Hub
                </Button>
              </NavLink>
            ) : undefined
          }
        />
      </Card>
    </div>
  );
};
