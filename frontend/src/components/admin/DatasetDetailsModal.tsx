import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/adminService';
import type { DatasetMetadataSchema } from '../../types/api';
import { Badge } from '../common/Badge';
import { 
  Database, 
  Sparkles, 
  RefreshCw, 
  AlertCircle, 
  X 
} from 'lucide-react';

interface DatasetDetailsModalProps {
  datasetId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const DatasetDetailsModal: React.FC<DatasetDetailsModalProps> = ({
  datasetId,
  isOpen,
  onClose,
}) => {
  const [dataset, setDataset] = useState<DatasetMetadataSchema | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && datasetId) {
      fetchDetails();
    }
  }, [isOpen, datasetId]);

  const fetchDetails = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await adminService.getDataset(datasetId);
      setDataset(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dataset details.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegeneratePrompts = async () => {
    if (!dataset || isRegenerating) return;
    setIsRegenerating(true);
    try {
      const res = await adminService.regeneratePrompts(dataset.dataset_id);
      setDataset({
        ...dataset,
        suggested_prompts: res.suggested_prompts,
      });
    } catch (err: any) {
      setError(err.message || 'Prompt regeneration failed.');
    } finally {
      setIsRegenerating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '16px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            background: 'var(--bg-surface-elevated)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--primary-gradient)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Database size={20} />
            </div>
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {dataset?.dataset_name || 'Dataset Details'}
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                ID: <code style={{ fontFamily: 'var(--font-mono)' }}>{datasetId}</code>
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ color: 'var(--text-muted)', display: 'flex', padding: '4px' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <span className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 12px' }} />
              <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>Loading metadata...</div>
            </div>
          ) : error ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 16px',
                color: 'var(--error-text)',
                fontSize: '0.84rem',
              }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          ) : dataset ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Status & Overview Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '12px',
                }}
              >
                <div style={{ background: 'var(--bg-app)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Lifecycle Status</div>
                  <Badge
                    variant={
                      dataset.processing_status === 'READY'
                        ? 'success'
                        : dataset.processing_status === 'FAILED'
                        ? 'error'
                        : 'info'
                    }
                  >
                    {dataset.processing_status}
                  </Badge>
                </div>

                <div style={{ background: 'var(--bg-app)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>PostgreSQL Table</div>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: dataset.table_name ? '#93c5fd' : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {dataset.table_name || 'Not Ingested Yet'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-app)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Dimensions</div>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {dataset.row_count !== null && dataset.row_count !== undefined
                      ? `${dataset.row_count.toLocaleString()} rows • ${dataset.column_count} cols`
                      : 'Unprocessed'}
                  </div>
                </div>
              </div>

              {/* File Info */}
              <div style={{ background: 'var(--bg-app)', padding: '14px 18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Source Artifact Metadata
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '0.8rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Filename: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{dataset.original_filename}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Format: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{dataset.file_format.toUpperCase()}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Size: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{dataset.file_size_formatted}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Uploaded: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{new Date(dataset.upload_timestamp).toLocaleDateString()}</strong>
                  </div>
                </div>
              </div>

              {/* Error Notice if FAILED */}
              {dataset.error_message && (
                <div
                  style={{
                    background: 'rgba(239, 68, 68, 0.12)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    color: 'var(--error-text)',
                    fontSize: '0.82rem',
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: '2px' }}>Processing Notice:</div>
                  <div>{dataset.error_message}</div>
                </div>
              )}

              {/* Suggested Questions Section */}
              {dataset.suggested_prompts && dataset.suggested_prompts.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      <Sparkles size={14} style={{ color: 'var(--primary-500)' }} />
                      <span>Schema-Driven Suggested Prompts ({dataset.suggested_prompts.length})</span>
                    </div>

                    <button
                      onClick={handleRegeneratePrompts}
                      disabled={isRegenerating}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.72rem',
                        color: 'var(--primary-500)',
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-sm)',
                        cursor: isRegenerating ? 'not-allowed' : 'pointer',
                      }}
                    >
                      <RefreshCw size={11} className={isRegenerating ? 'spin' : ''} />
                      <span>{isRegenerating ? 'Regenerating...' : 'Regenerate'}</span>
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {dataset.suggested_prompts.map((prompt, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'var(--bg-app)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '8px 12px',
                          fontSize: '0.8rem',
                          color: 'var(--text-primary)',
                        }}
                      >
                        💬 "{prompt}"
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
