import React, { useState } from 'react';
import type { CatalogDatasetSchema, UseCatalogDatasetResponse } from '../../types/api';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { useDataset } from '../../context/DatasetContext';
import { catalogService } from '../../services/catalogService';
import { 
  Database, 
  CheckCircle2, 
  Info, 
  Layers, 
  HardDrive, 
  Check, 
  Sparkles
} from 'lucide-react';

interface DatasetCardProps {
  dataset: CatalogDatasetSchema;
  onViewDetails: (dataset: CatalogDatasetSchema) => void;
  onDatasetUsed?: (result: UseCatalogDatasetResponse, dataset: CatalogDatasetSchema) => void;
  onError?: (errorMessage: string) => void;
}

export const DatasetCard: React.FC<DatasetCardProps> = ({
  dataset,
  onViewDetails,
  onDatasetUsed,
  onError,
}) => {
  const { activeDataset, setActiveDataset } = useDataset();
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState<'Preparing...' | 'Cleaning & Importing...'>('Preparing...');

  // Check if this card represents the currently active dataset
  const isActive = Boolean(
    (dataset.imported_table_name && activeDataset.tableName === dataset.imported_table_name) ||
    (dataset.imported_dataset_id && activeDataset.datasetId === dataset.imported_dataset_id)
  );

  const handleUseDataset = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading) return; // Prevent duplicate requests

    // If already imported and already active, do nothing
    if (isActive) return;

    // If already imported in database, activate immediately in context
    if (dataset.is_imported && dataset.imported_dataset_id && dataset.imported_table_name) {
      setActiveDataset({
        datasetId: dataset.imported_dataset_id,
        datasetName: dataset.name,
        tableName: dataset.imported_table_name,
      });
      if (onDatasetUsed) {
        onDatasetUsed(
          {
            status: 'READY',
            message: `Switched active context to ${dataset.name}`,
            dataset_id: dataset.imported_dataset_id,
            table_name: dataset.imported_table_name,
            rows_imported: dataset.approx_rows,
            suggested_prompts: [],
            was_reused: true,
          },
          dataset
        );
      }
      return;
    }

    // Otherwise call real backend ingestion endpoint
    setLoading(true);
    setLoadingText('Preparing...');
    try {
      setTimeout(() => {
        if (loading) setLoadingText('Cleaning & Importing...');
      }, 600);

      const response = await catalogService.useCatalogDataset(dataset.catalog_id);

      setActiveDataset({
        datasetId: response.dataset_id,
        datasetName: dataset.name,
        tableName: response.table_name,
      });

      if (onDatasetUsed) {
        onDatasetUsed(response, dataset);
      }
    } catch (err: any) {
      if (onError) {
        onError(err.message || `Failed to provision dataset ${dataset.name}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100%',
        borderColor: isActive ? 'var(--primary-500)' : undefined,
        boxShadow: isActive ? '0 0 16px rgba(59, 130, 246, 0.2)' : undefined,
        background: isActive ? 'linear-gradient(180deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)' : undefined,
      }}
    >
      <div>
        {/* Card Header: Category Badge & Status */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
          <Badge variant="info">{dataset.category}</Badge>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            {isActive && (
              <Badge variant="success" icon={<Sparkles size={11} />}>
                Active
              </Badge>
            )}
            {dataset.is_imported && !isActive && (
              <Badge variant="neutral" icon={<Check size={11} />}>
                Imported
              </Badge>
            )}
          </div>
        </div>

        {/* Dataset Title & Description */}
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px', lineHeight: 1.3 }}>
          {dataset.name}
        </h3>
        <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '14px' }}>
          {dataset.description}
        </p>

        {/* Metadata Chips: Rows, Size, Format */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.74rem',
              color: 'var(--text-muted)',
              background: 'var(--bg-surface-elevated)',
              padding: '3px 8px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <Layers size={12} />
            ~{dataset.approx_rows.toLocaleString()} rows
          </span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.74rem',
              color: 'var(--text-muted)',
              background: 'var(--bg-surface-elevated)',
              padding: '3px 8px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <HardDrive size={12} />
            {dataset.approx_size} ({dataset.file_format.toUpperCase()})
          </span>
        </div>

        {/* Analytics Topics Tags */}
        {dataset.analytics_topics && dataset.analytics_topics.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '16px' }}>
            {dataset.analytics_topics.slice(0, 3).map((topic, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-secondary)',
                  background: 'rgba(59, 130, 246, 0.08)',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                }}
              >
                {topic}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Card Footer: Source Info & Action Buttons */}
      <div
        style={{
          paddingTop: '14px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '8px',
          marginTop: '8px',
        }}
      >
        <button
          onClick={() => onViewDetails(dataset)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            padding: '6px 8px',
            borderRadius: 'var(--radius-sm)',
            transition: 'color 0.15s ease',
          }}
          title="View detailed schema & sources"
        >
          <Info size={14} />
          <span>Details</span>
        </button>

        <Button
          variant={isActive ? 'secondary' : 'primary'}
          size="sm"
          loading={loading}
          disabled={Boolean(loading || isActive)}
          onClick={handleUseDataset}
          icon={isActive ? <CheckCircle2 size={13} /> : <Database size={13} />}
        >
          {loading ? loadingText : isActive ? 'Active Context' : dataset.is_imported ? 'Use Dataset' : '⚡ Use Dataset'}
        </Button>
      </div>
    </Card>
  );
};
