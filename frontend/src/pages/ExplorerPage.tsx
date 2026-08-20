import React, { useState, useEffect, useRef } from 'react';
import { useDataset } from '../context/DatasetContext';
import { datasetService } from '../services/datasetService';
import type { DatasetSchemaResponse } from '../types/api';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { SchemaTable } from '../components/explorer/SchemaTable';
import { SuggestedPrompts } from '../components/explorer/SuggestedPrompts';
import { NavLink } from 'react-router-dom';
import { 
  Table, 
  Database, 
  Sparkles, 
  RefreshCw, 
  Layers, 
  ArrowLeft
} from 'lucide-react';

export const ExplorerPage: React.FC = () => {
  const { activeDataset } = useDataset();
  const [schemaData, setSchemaData] = useState<DatasetSchemaResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Reference to track active request and avoid race conditions on rapid dataset switches
  const currentRequestIdRef = useRef<string | null>(null);

  const fetchSchema = async (datasetId: string) => {
    currentRequestIdRef.current = datasetId;
    setLoading(true);
    setError(null);

    try {
      const data = await datasetService.getDatasetSchema(datasetId);
      // Ensure only the most recently requested dataset updates the UI state
      if (currentRequestIdRef.current === datasetId) {
        setSchemaData(data);
      }
    } catch (err: any) {
      if (currentRequestIdRef.current === datasetId) {
        setError(err.message || 'Failed to fetch PostgreSQL schema definitions.');
        setSchemaData(null);
      }
    } finally {
      if (currentRequestIdRef.current === datasetId) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    if (activeDataset.datasetId) {
      fetchSchema(activeDataset.datasetId);
    } else {
      setSchemaData(null);
      setError(null);
    }
  }, [activeDataset.datasetId]);

  // If no dataset is active in context
  if (!activeDataset.datasetId) {
    return (
      <div>
        <PageHeader
          title="Database Schema Explorer"
          description="Inspect live relational table structures, data types, null distributions, and preview records."
          badge={<Badge variant="neutral">No Active Dataset</Badge>}
        />

        <Card>
          <EmptyState
            icon={<Table size={42} style={{ color: 'var(--text-muted)' }} />}
            title="No Dataset Selected"
            description="Select a curated dataset from the Dataset Hub to explore its column definitions, PostgreSQL types, and suggested analytical questions."
            action={
              <NavLink to="/hub">
                <Button variant="primary" icon={<Database size={15} />}>
                  Open Dataset Hub
                </Button>
              </NavLink>
            }
          />
        </Card>
      </div>
    );
  }

  const columnCount = schemaData?.columns?.length || 0;

  return (
    <div>
      {/* Page Header */}
      <PageHeader
        title="Dataset Schema Explorer"
        description="Live PostgreSQL schema metadata, normalized column identifiers, data types, and suggested analytical questions."
        badge={
          <Badge variant="success" icon={<Sparkles size={11} />}>
            {activeDataset.datasetName || 'Active Dataset'}
          </Badge>
        }
        action={
          <div style={{ display: 'flex', gap: '10px' }}>
            <NavLink to="/hub">
              <Button variant="secondary" size="sm" icon={<ArrowLeft size={13} />}>
                Switch Dataset
              </Button>
            </NavLink>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => activeDataset.datasetId && fetchSchema(activeDataset.datasetId)}
              loading={loading}
              disabled={loading}
              icon={<RefreshCw size={13} className={loading ? 'spinner' : ''} />}
            >
              {loading ? 'Refreshing...' : '↻ Refresh Schema'}
            </Button>
          </div>
        }
      />

      {/* Schema Overview Card */}
      <Card style={{ marginBottom: '24px', background: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Relational Database Table
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {activeDataset.datasetName}
              </span>
              <code
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  color: 'var(--primary-500)',
                  background: 'rgba(59, 130, 246, 0.12)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                {activeDataset.tableName || schemaData?.table_name}
              </code>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div
              style={{
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                padding: '10px 16px',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Layers size={16} style={{ color: 'var(--primary-500)' }} />
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>COLUMNS</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>
                  {loading ? '—' : columnCount}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Error Message */}
      {error && (
        <ErrorMessage
          message={error}
          onRetry={() => activeDataset.datasetId && fetchSchema(activeDataset.datasetId)}
        />
      )}

      {/* Schema Table */}
      {loading ? (
        <Card>
          <LoadingSpinner label="Fetching live column profiles and data types from PostgreSQL..." />
        </Card>
      ) : schemaData && schemaData.columns ? (
        <SchemaTable columns={schemaData.columns} />
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>
            No schema information available for this dataset.
          </div>
        </Card>
      )}

      {/* Suggested Questions Section */}
      {activeDataset.datasetId && (
        <SuggestedPrompts
          datasetId={activeDataset.datasetId}
          datasetName={activeDataset.datasetName || 'Dataset'}
        />
      )}
    </div>
  );
};
