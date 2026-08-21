import React, { useState, useRef } from 'react';
import { adminService } from '../../services/adminService';
import type { DatasetMetadataSchema } from '../../types/api';
import { UploadCloud, FileSpreadsheet, AlertCircle, CheckCircle2, X } from 'lucide-react';

export const MAX_UPLOAD_SIZE_MB = 50;
const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.json', '.parquet'];

interface UploadDropzoneProps {
  onUploadSuccess: (dataset: DatasetMetadataSchema) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onUploadSuccess }) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported format "${ext}". Allowed formats: CSV, XLSX, JSON, Parquet.`;
    }
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > MAX_UPLOAD_SIZE_MB) {
      return `File size (${sizeMb.toFixed(1)} MB) exceeds maximum allowed limit of ${MAX_UPLOAD_SIZE_MB} MB.`;
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    setError(null);
    setSuccessMessage(null);
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    if (!datasetName) {
      // Auto-populate friendly name from filename (strip extension)
      const rawName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
      setDatasetName(rawName.charAt(0).toUpperCase() + rawName.slice(1));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || isUploading) return;

    setError(null);
    setSuccessMessage(null);
    setIsUploading(true);

    try {
      const response = await adminService.uploadDataset(selectedFile, datasetName);
      setSuccessMessage(`Dataset "${response.dataset.dataset_name}" uploaded successfully!`);
      setSelectedFile(null);
      setDatasetName('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      onUploadSuccess(response.dataset);
    } catch (err: any) {
      if (err.status === 413) {
        setError(`File exceeds the maximum allowed size (${MAX_UPLOAD_SIZE_MB} MB).`);
      } else {
        setError(err.message || 'Dataset upload failed. Please verify format and try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    setDatasetName('');
    setError(null);
    setSuccessMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div style={{ marginBottom: '16px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Upload New Dataset
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          Securely upload tabular files to trigger cleaning, schema detection, and PostgreSQL ingestion.
        </p>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? 'var(--primary-500)' : 'var(--border-strong)'}`,
          borderRadius: 'var(--radius-lg)',
          background: dragOver ? 'rgba(59, 130, 246, 0.05)' : 'var(--bg-app)',
          padding: '32px 20px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          marginBottom: '16px',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.json,.parquet"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        <div
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '50%',
            background: 'var(--bg-surface-elevated)',
            color: 'var(--primary-500)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px',
          }}
        >
          <UploadCloud size={24} />
        </div>

        <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Click to browse or drag and drop dataset file
        </div>
        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
          Supported Formats: <strong>CSV, XLSX, JSON, Parquet</strong> (Max: {MAX_UPLOAD_SIZE_MB} MB)
        </div>
      </div>

      {/* Selected File Details & Custom Name */}
      {selectedFile && (
        <div
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            marginBottom: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FileSpreadsheet size={20} style={{ color: 'var(--primary-500)' }} />
              <div>
                <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {selectedFile.name}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.name.split('.').pop()?.toUpperCase()}
                </div>
              </div>
            </div>

            <button
              onClick={clearSelectedFile}
              style={{ color: 'var(--text-muted)', display: 'flex', padding: '4px' }}
              title="Remove selected file"
            >
              <X size={16} />
            </button>
          </div>

          <div>
            <label
              style={{
                display: 'block',
                fontSize: '0.76rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '4px',
              }}
            >
              Custom Dataset Name (Optional)
            </label>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g. Q3 Sales & Performance"
              disabled={isUploading}
              style={{
                width: '100%',
                background: 'var(--bg-app)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 12px',
                color: 'var(--text-primary)',
                fontSize: '0.84rem',
                outline: 'none',
              }}
            />
          </div>
        </div>
      )}

      {/* Error & Success Messages */}
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
            fontSize: '0.8rem',
            marginBottom: '14px',
          }}
        >
          <AlertCircle size={15} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            color: '#34d399',
            fontSize: '0.8rem',
            marginBottom: '14px',
          }}
        >
          <CheckCircle2 size={15} style={{ flexShrink: 0 }} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Upload Action Button */}
      {selectedFile && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="btn btn-primary"
          style={{
            width: '100%',
            padding: '10px',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.86rem',
            fontWeight: 600,
            opacity: isUploading ? 0.6 : 1,
          }}
        >
          {isUploading ? (
            <>
              <span className="spinner" style={{ width: '14px', height: '14px' }} />
              <span>Uploading Dataset...</span>
            </>
          ) : (
            <>
              <UploadCloud size={15} />
              <span>Upload Dataset</span>
            </>
          )}
        </button>
      )}
    </div>
  );
};
