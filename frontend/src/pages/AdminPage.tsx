import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useDataset } from '../context/DatasetContext';
import { useChat } from '../context/ChatContext';
import { adminService } from '../services/adminService';
import type { 
  DatasetMetadataSchema, 
  DatasetProcessResponse, 
  DatasetImportResponse 
} from '../types/api';
import { UploadDropzone } from '../components/admin/UploadDropzone';
import { DatasetTable } from '../components/admin/DatasetTable';
import { CleaningReport } from '../components/admin/CleaningReport';
import { DataPreview } from '../components/admin/DataPreview';
import { DetectedSchema } from '../components/admin/DetectedSchema';
import { ImportConfirmation } from '../components/admin/ImportConfirmation';
import { DatasetDetailsModal } from '../components/admin/DatasetDetailsModal';
import { DeleteConfirmModal } from '../components/admin/DeleteConfirmModal';
import { 
  ShieldCheck, 
  RefreshCw, 
  LogOut, 
  Database, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  Play,
  X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const AdminPage: React.FC = () => {
  const { username, logout } = useAuth();
  const { activeDataset, clearActiveDataset } = useDataset();
  const { newChat } = useChat();
  const navigate = useNavigate();

  const [datasets, setDatasets] = useState<DatasetMetadataSchema[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Processing state
  const [processingDatasetId, setProcessingDatasetId] = useState<string | null>(null);
  const [activeProcessResult, setActiveProcessResult] = useState<DatasetProcessResponse | null>(null);
  const [processError, setProcessError] = useState<string | null>(null);

  // Modals state
  const [selectedDetailsDatasetId, setSelectedDetailsDatasetId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DatasetMetadataSchema | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchDatasets = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminService.getDatasets();
      setDatasets(response.datasets || []);
    } catch (err: any) {
      if (err.status === 401) {
        logout();
        navigate('/login', { replace: true });
      } else {
        setError(err.message || 'Failed to load dataset list from admin API.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [logout, navigate]);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const handleUploadSuccess = (_uploadedDataset: DatasetMetadataSchema) => {
    fetchDatasets();
  };

  const handleProcess = async (dataset: DatasetMetadataSchema) => {
    setProcessingDatasetId(dataset.dataset_id);
    setActiveProcessResult(null);
    setProcessError(null);

    try {
      const result = await adminService.processDataset(dataset.dataset_id);
      setActiveProcessResult(result);
      fetchDatasets();
    } catch (err: any) {
      setProcessError(err.message || 'Processing failed.');
    } finally {
      setProcessingDatasetId(null);
    }
  };

  const handleImportSuccess = (_response: DatasetImportResponse) => {
    fetchDatasets();
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget || isDeleting) return;

    setIsDeleting(true);
    try {
      await adminService.deleteDataset(deleteTarget.dataset_id);

      // If deleted dataset is currently active, clear context
      if (activeDataset.datasetId === deleteTarget.dataset_id) {
        clearActiveDataset();
        newChat();
      }

      setDeleteTarget(null);
      if (activeProcessResult && activeProcessResult.dataset_id === deleteTarget.dataset_id) {
        setActiveProcessResult(null);
      }
      fetchDatasets();
    } catch (err: any) {
      alert(`Deletion failed: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Compute summary stats
  const totalCount = datasets.length;
  const readyCount = datasets.filter((d) => d.processing_status === 'READY').length;
  const processingCount = datasets.filter((d) => d.processing_status === 'PROCESSING' || d.processing_status === 'UPLOADED').length;
  const failedCount = datasets.filter((d) => d.processing_status === 'FAILED').length;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--primary-gradient)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-glow)',
            }}
          >
            <ShieldCheck size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Admin Dataset Management
            </h1>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
              Secure tabular ingestion, schema detection & PostgreSQL dynamic provisioning
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-full)',
              padding: '4px 12px',
            }}
          >
            Admin: <strong style={{ color: 'var(--text-primary)' }}>{username || 'Administrator'}</strong>
          </div>

          <button
            onClick={fetchDatasets}
            disabled={isLoading}
            className="btn btn-secondary btn-sm"
            style={{ padding: '6px 12px' }}
            title="Refresh dataset list"
          >
            <RefreshCw size={13} className={isLoading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleLogout}
            className="btn btn-secondary btn-sm"
            style={{ padding: '6px 12px', color: '#f87171' }}
            title="Sign out of admin"
          >
            <LogOut size={13} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Dataset Statistics Metric Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '14px',
        }}
      >
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(59, 130, 246, 0.12)',
              color: 'var(--primary-500)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Database size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Total Datasets</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>{totalCount}</div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(16, 185, 129, 0.12)',
              color: '#34d399',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>READY (Ingested)</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>{readyCount}</div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(245, 158, 11, 0.12)',
              color: '#f59e0b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Clock size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Uploaded / Processing</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f59e0b' }}>{processingCount}</div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(239, 68, 68, 0.12)',
              color: '#f87171',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <AlertCircle size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Failed Ingestion</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f87171' }}>{failedCount}</div>
          </div>
        </div>
      </div>

      {/* Upload Dropzone */}
      <UploadDropzone onUploadSuccess={handleUploadSuccess} />

      {/* Process Result Workspace (if dataset was processed) */}
      {processError && (
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
          <span>Processing Error: {processError}</span>
        </div>
      )}

      {activeProcessResult && (
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Play size={18} style={{ color: 'var(--primary-500)' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Processing Results: {activeProcessResult.dataset_name}
              </h3>
            </div>
            <button
              onClick={() => setActiveProcessResult(null)}
              style={{ color: 'var(--text-muted)', display: 'flex', padding: '4px' }}
              title="Close process review"
            >
              <X size={18} />
            </button>
          </div>

          <CleaningReport report={activeProcessResult.cleaning_report} />
          <DetectedSchema schema={activeProcessResult.schema_detected} />
          <DataPreview preview={activeProcessResult.preview} />

          <ImportConfirmation
            datasetId={activeProcessResult.dataset_id}
            datasetName={activeProcessResult.dataset_name}
            suggestedTableName={activeProcessResult.suggested_table_name}
            onImportSuccess={handleImportSuccess}
            onCancel={() => setActiveProcessResult(null)}
          />
        </div>
      )}

      {/* Uploaded Datasets Table */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Uploaded Datasets & Ingestion Registry
          </h3>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {datasets.length} Total Registered
          </span>
        </div>

        {error ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '14px 18px',
              color: 'var(--error-text)',
              fontSize: '0.84rem',
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        ) : (
          <DatasetTable
            datasets={datasets}
            onViewDetails={(ds) => setSelectedDetailsDatasetId(ds.dataset_id)}
            onProcess={handleProcess}
            onDelete={(ds) => setDeleteTarget(ds)}
            processingDatasetId={processingDatasetId}
          />
        )}
      </div>

      {/* Dataset Details Modal */}
      {selectedDetailsDatasetId && (
        <DatasetDetailsModal
          datasetId={selectedDetailsDatasetId}
          isOpen={!!selectedDetailsDatasetId}
          onClose={() => setSelectedDetailsDatasetId(null)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <DeleteConfirmModal
          datasetName={deleteTarget.dataset_name}
          tableName={deleteTarget.table_name}
          isOpen={!!deleteTarget}
          isDeleting={isDeleting}
          onConfirm={handleDeleteConfirm}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
};
