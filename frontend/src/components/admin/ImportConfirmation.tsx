import React, { useState } from 'react';
import { adminService } from '../../services/adminService';
import { useDataset } from '../../context/DatasetContext';
import type { DatasetImportResponse } from '../../types/api';
import { Database, CheckCircle2, AlertCircle, ArrowRight, Layers, BotMessageSquare } from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface ImportConfirmationProps {
  datasetId: string;
  datasetName: string;
  suggestedTableName: string;
  onImportSuccess: (response: DatasetImportResponse) => void;
  onCancel: () => void;
}

export const ImportConfirmation: React.FC<ImportConfirmationProps> = ({
  datasetId,
  datasetName,
  suggestedTableName,
  onImportSuccess,
  onCancel,
}) => {
  const [tableName, setTableName] = useState(suggestedTableName);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<DatasetImportResponse | null>(null);

  const { setActiveDataset } = useDataset();

  const handleImport = async () => {
    if (isImporting) return;

    setError(null);
    setIsImporting(true);

    try {
      const response = await adminService.importDataset(datasetId, tableName);
      setImportResult(response);

      // Automatically sync newly imported dataset into active context
      setActiveDataset({
        datasetId: response.dataset_id,
        datasetName: datasetName,
        tableName: response.table_name,
      });
      onImportSuccess(response);
    } catch (err: any) {
      setError(err.message || 'PostgreSQL table creation or bulk ingestion failed.');
    } finally {
      setIsImporting(false);
    }
  };

  if (importResult) {
    return (
      <div
        style={{
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          marginTop: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <CheckCircle2 size={24} style={{ color: '#34d399' }} />
          <div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Dataset Imported & Provisioned Successfully!
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Dynamic PostgreSQL table created, indexes built, and dataset set as active context.
            </p>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-app)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            fontSize: '0.84rem',
            marginBottom: '16px',
            display: 'flex',
            gap: '24px',
          }}
        >
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Table: </span>
            <strong style={{ fontFamily: 'var(--font-mono)', color: '#93c5fd' }}>{importResult.table_name}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Rows Ingested: </span>
            <strong style={{ color: 'var(--text-primary)' }}>{importResult.rows_imported.toLocaleString()}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Columns: </span>
            <strong style={{ color: 'var(--text-primary)' }}>{importResult.columns_imported}</strong>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <NavLink to="/copilot" className="btn btn-primary btn-sm">
            <BotMessageSquare size={14} />
            <span>Open AI Copilot</span>
            <ArrowRight size={13} />
          </NavLink>
          <NavLink to="/explorer" className="btn btn-secondary btn-sm">
            <Layers size={14} />
            <span>View Schema & Questions</span>
          </NavLink>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface-elevated)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        marginTop: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <Database size={18} style={{ color: 'var(--primary-500)' }} />
        <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Confirm PostgreSQL Dynamic Table Ingestion
        </h4>
      </div>

      <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
        This step will create a dedicated, isolated PostgreSQL table, execute bulk transactional ingestion, and generate
        schema-driven AI analytical prompts.
      </p>

      {error && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            color: 'var(--error-text)',
            fontSize: '0.82rem',
            marginBottom: '14px',
          }}
        >
          <AlertCircle size={15} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      <div style={{ marginBottom: '18px' }}>
        <label
          style={{
            display: 'block',
            fontSize: '0.78rem',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            marginBottom: '6px',
          }}
        >
          Destination Table Name
        </label>
        <input
          type="text"
          value={tableName}
          onChange={(e) => setTableName(e.target.value)}
          placeholder="e.g. ds_sales_data"
          disabled={isImporting}
          style={{
            width: '100%',
            maxWidth: '380px',
            background: 'var(--bg-app)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 12px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.86rem',
            color: '#93c5fd',
            outline: 'none',
          }}
        />
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Safe PostgreSQL identifier normalized automatically by the backend.
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handleImport}
          disabled={!tableName.trim() || isImporting}
          className="btn btn-primary"
          style={{
            padding: '8px 18px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.86rem',
            fontWeight: 600,
            opacity: !tableName.trim() || isImporting ? 0.6 : 1,
          }}
        >
          {isImporting ? (
            <>
              <span className="spinner" style={{ width: '14px', height: '14px' }} />
              <span>Creating Table & Ingesting Data...</span>
            </>
          ) : (
            <>
              <Database size={14} />
              <span>Confirm & Ingest into PostgreSQL</span>
            </>
          )}
        </button>

        <button
          onClick={onCancel}
          disabled={isImporting}
          className="btn btn-secondary btn-sm"
          style={{ padding: '8px 14px' }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
