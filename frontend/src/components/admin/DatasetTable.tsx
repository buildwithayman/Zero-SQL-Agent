import React from 'react';
import type { DatasetMetadataSchema } from '../../types/api';
import { Badge } from '../common/Badge';
import { 
  FileSpreadsheet, 
  Trash2, 
  Eye, 
  Play 
} from 'lucide-react';

interface DatasetTableProps {
  datasets: DatasetMetadataSchema[];
  onViewDetails: (dataset: DatasetMetadataSchema) => void;
  onProcess: (dataset: DatasetMetadataSchema) => void;
  onDelete: (dataset: DatasetMetadataSchema) => void;
  processingDatasetId?: string | null;
}

export const DatasetTable: React.FC<DatasetTableProps> = ({
  datasets,
  onViewDetails,
  onProcess,
  onDelete,
  processingDatasetId,
}) => {
  if (!datasets || datasets.length === 0) {
    return (
      <div
        style={{
          padding: '48px 16px',
          textAlign: 'center',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-secondary)',
        }}
      >
        <FileSpreadsheet size={36} style={{ color: 'var(--text-muted)', margin: '0 auto 12px' }} />
        <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
          No Datasets Uploaded Yet
        </h4>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Upload a CSV, XLSX, JSON, or Parquet file using the upload dropzone above.
        </p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'READY':
        return <Badge variant="success">READY</Badge>;
      case 'PROCESSING':
        return <Badge variant="info">PROCESSING</Badge>;
      case 'FAILED':
        return <Badge variant="error">FAILED</Badge>;
      case 'DELETED':
        return <Badge variant="neutral">DELETED</Badge>;
      default:
        return <Badge variant="info">UPLOADED</Badge>;
    }
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-strong)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Dataset Name
              </th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Format / Size
              </th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Status
              </th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                PostgreSQL Table
              </th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Rows / Cols
              </th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Uploaded
              </th>
              <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'right' }}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {datasets.map((ds) => {
              const isCurrentlyProcessing = processingDatasetId === ds.dataset_id;
              return (
                <tr
                  key={ds.dataset_id}
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    transition: 'background-color 0.15s ease',
                  }}
                >
                  {/* Name & Filename */}
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                      {ds.dataset_name}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {ds.original_filename}
                    </div>
                  </td>

                  {/* Format & Size */}
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {ds.file_format.toUpperCase()}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.74rem', marginLeft: '6px' }}>
                      ({ds.file_size_formatted})
                    </span>
                  </td>

                  {/* Status Badge */}
                  <td style={{ padding: '12px 16px' }}>
                    {getStatusBadge(ds.processing_status)}
                  </td>

                  {/* Table Name */}
                  <td style={{ padding: '12px 16px' }}>
                    {ds.table_name ? (
                      <code style={{ fontFamily: 'var(--font-mono)', color: '#93c5fd', fontSize: '0.78rem' }}>
                        {ds.table_name}
                      </code>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.76rem' }}>
                        None
                      </span>
                    )}
                  </td>

                  {/* Dimensions */}
                  <td style={{ padding: '12px 16px' }}>
                    {ds.row_count !== null && ds.row_count !== undefined ? (
                      <span>
                        <strong>{ds.row_count.toLocaleString()}</strong> rows ({ds.column_count} cols)
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>

                  {/* Upload Date */}
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '0.74rem' }}>
                    {new Date(ds.upload_timestamp).toLocaleDateString()}
                  </td>

                  {/* Actions */}
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                      {/* Process Dataset Button (if UPLOADED or FAILED) */}
                      {(ds.processing_status === 'UPLOADED' || ds.processing_status === 'FAILED') && (
                        <button
                          onClick={() => onProcess(ds)}
                          disabled={isCurrentlyProcessing}
                          className="btn btn-primary btn-sm"
                          style={{ padding: '4px 10px', fontSize: '0.74rem' }}
                          title="Parse, clean, and profile dataset"
                        >
                          {isCurrentlyProcessing ? (
                            <span className="spinner" style={{ width: '11px', height: '11px' }} />
                          ) : (
                            <Play size={11} />
                          )}
                          <span>Process</span>
                        </button>
                      )}

                      {/* Details View */}
                      <button
                        onClick={() => onViewDetails(ds)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '4px 8px', fontSize: '0.74rem' }}
                        title="View details & metadata"
                      >
                        <Eye size={12} />
                        <span>Details</span>
                      </button>

                      {/* Delete Action */}
                      <button
                        onClick={() => onDelete(ds)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#f87171',
                          padding: '4px 6px',
                          borderRadius: 'var(--radius-sm)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                        title="Delete dataset"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
