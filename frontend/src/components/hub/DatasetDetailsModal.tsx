import React, { useState } from 'react';
import type { CatalogDatasetSchema, UseCatalogDatasetResponse } from '../../types/api';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { useDataset } from '../../context/DatasetContext';
import { catalogService } from '../../services/catalogService';
import { 
  X, 
  Database, 
  ExternalLink, 
  Download, 
  CheckCircle2, 
  Sparkles,
  Tag,
  BarChart2
} from 'lucide-react';

interface DatasetDetailsModalProps {
  dataset: CatalogDatasetSchema | null;
  onClose: () => void;
  onDatasetUsed?: (result: UseCatalogDatasetResponse, dataset: CatalogDatasetSchema) => void;
  onError?: (errorMessage: string) => void;
}

export const DatasetDetailsModal: React.FC<DatasetDetailsModalProps> = ({
  dataset,
  onClose,
  onDatasetUsed,
  onError,
}) => {
  const { activeDataset, setActiveDataset } = useDataset();
  const [loading, setLoading] = useState(false);

  if (!dataset) return null;

  const isActive = Boolean(
    (dataset.imported_table_name && activeDataset.tableName === dataset.imported_table_name) ||
    (dataset.imported_dataset_id && activeDataset.datasetId === dataset.imported_dataset_id)
  );

  const handleUseDataset = async () => {
    if (loading || isActive) return;

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
      onClose();
      return;
    }

    setLoading(true);
    try {
      const response = await catalogService.useCatalogDataset(dataset.catalog_id);
      setActiveDataset({
        datasetId: response.dataset_id,
        datasetName: dataset.name,
        tableName: response.table_name,
      });

      if (onDatasetUsed) {
        onDatasetUsed(response, dataset);
      }
      onClose();
    } catch (err: any) {
      if (onError) {
        onError(err.message || `Failed to provision dataset ${dataset.name}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-lg)',
          width: '100%',
          maxWidth: '680px',
          maxHeight: '85vh',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-lg)',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            backgroundColor: 'var(--bg-surface)',
            zIndex: 2,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Badge variant="info">{dataset.category}</Badge>
            {isActive && (
              <Badge variant="success" icon={<Sparkles size={11} />}>
                Active Context
              </Badge>
            )}
            {dataset.is_imported && !isActive && (
              <Badge variant="neutral" icon={<CheckCircle2 size={11} />}>
                Imported in DB
              </Badge>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              color: 'var(--text-muted)',
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
            {dataset.name}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.6, marginBottom: '20px' }}>
            {dataset.description}
          </p>

          {/* Key Metrics Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '12px',
              marginBottom: '24px',
            }}
          >
            <div style={{ background: 'var(--bg-surface-elevated)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>APPROX ROWS</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                ~{dataset.approx_rows.toLocaleString()}
              </div>
            </div>
            <div style={{ background: 'var(--bg-surface-elevated)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>APPROX SIZE</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {dataset.approx_size}
              </div>
            </div>
            <div style={{ background: 'var(--bg-surface-elevated)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>FORMAT</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {dataset.file_format.toUpperCase()}
              </div>
            </div>
            {dataset.imported_table_name && (
              <div style={{ background: 'var(--bg-surface-elevated)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>POSTGRES TABLE</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--primary-500)', fontFamily: 'var(--font-mono)' }}>
                  {dataset.imported_table_name}
                </div>
              </div>
            )}
          </div>

          {/* Analytics Topics */}
          {dataset.analytics_topics && dataset.analytics_topics.length > 0 && (
            <div style={{ marginBottom: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px' }}>
                <BarChart2 size={15} style={{ color: 'var(--primary-500)' }} />
                <span>Suggested Analytical Topics</span>
              </div>
              <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.86rem', lineHeight: 1.7 }}>
                {dataset.analytics_topics.map((topic, i) => (
                  <li key={i}>{topic}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Tags */}
          {dataset.tags && dataset.tags.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px' }}>
                <Tag size={15} style={{ color: 'var(--primary-500)' }} />
                <span>Keywords & Metadata Tags</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {dataset.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: '0.75rem',
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-subtle)',
                      padding: '3px 10px',
                      borderRadius: 'var(--radius-full)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source Attribution & Links */}
          <div
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '14px 18px',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              fontSize: '0.82rem',
            }}
          >
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Source: </span>
              <strong style={{ color: 'var(--text-primary)' }}>{dataset.source_name}</strong>
            </div>
            <div style={{ display: 'flex', gap: '14px' }}>
              {dataset.source_url && (
                <a
                  href={dataset.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: 'var(--primary-500)',
                    fontWeight: 500,
                  }}
                >
                  <span>Source Webpage</span>
                  <ExternalLink size={12} />
                </a>
              )}
              {dataset.download_url && (
                <a
                  href={dataset.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: 'var(--primary-500)',
                    fontWeight: 500,
                  }}
                >
                  <span>Direct Download</span>
                  <Download size={12} />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            position: 'sticky',
            bottom: 0,
            backgroundColor: 'var(--bg-surface)',
            zIndex: 2,
          }}
        >
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Button
            variant="primary"
            loading={loading}
            disabled={Boolean(loading || isActive)}
            onClick={handleUseDataset}
            icon={isActive ? <CheckCircle2 size={14} /> : <Database size={14} />}
          >
            {loading ? 'Ingesting Dataset...' : isActive ? 'Active Context' : dataset.is_imported ? 'Set as Active Dataset' : '⚡ Ingest & Use Dataset'}
          </Button>
        </div>
      </div>
    </div>
  );
};
