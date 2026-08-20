import React, { useState, useEffect } from 'react';
import type { 
  CatalogDatasetSchema, 
  UseCatalogDatasetResponse 
} from '../types/api';
import { catalogService } from '../services/catalogService';
import { PageHeader } from '../components/common/PageHeader';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { DatasetCard } from '../components/hub/DatasetCard';
import { DatasetDetailsModal } from '../components/hub/DatasetDetailsModal';
import { RecommendationBar } from '../components/hub/RecommendationBar';
import { CategoryPills } from '../components/hub/CategoryPills';
import { NavLink } from 'react-router-dom';
import { Database, CheckCircle2, ArrowRight, X, RefreshCw } from 'lucide-react';

export const DatasetHubPage: React.FC = () => {
  const [datasets, setDatasets] = useState<CatalogDatasetSchema[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [selectedDatasetForDetails, setSelectedDatasetForDetails] = useState<CatalogDatasetSchema | null>(null);

  // Success Notification State
  const [successNotification, setSuccessNotification] = useState<{
    message: string;
    datasetName: string;
    tableName: string;
  } | null>(null);

  const fetchCatalog = async (category: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await catalogService.getCatalog(category);
      setDatasets(res.datasets);
    } catch (err: any) {
      setError(err.message || 'Failed to load popular dataset catalog.');
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog(selectedCategory);
  }, [selectedCategory]);

  const handleDatasetUsed = (result: UseCatalogDatasetResponse, dataset: CatalogDatasetSchema) => {
    setSuccessNotification({
      message: result.message || 'Dataset successfully provisioned and ready for analysis.',
      datasetName: dataset.name,
      tableName: result.table_name,
    });

    // Update imported state in current dataset list
    setDatasets((prev) =>
      prev.map((d) =>
        d.catalog_id === dataset.catalog_id
          ? {
              ...d,
              is_imported: true,
              imported_dataset_id: result.dataset_id,
              imported_table_name: result.table_name,
            }
          : d
      )
    );
  };

  return (
    <div>
      {/* Page Header */}
      <PageHeader
        title="Dataset Hub"
        description="Discover curated industry datasets, explore analytical topics, or let AI recommend the best dataset for your analysis."
        badge={<Badge variant="success">{datasets.length} Curated Datasets</Badge>}
        action={
          <button
            onClick={() => fetchCatalog(selectedCategory)}
            className="btn btn-secondary btn-sm"
            title="Refresh Catalog"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={13} className={loading ? 'spinner' : ''} />
            <span>Refresh</span>
          </button>
        }
      />

      {/* Success Notification Banner */}
      {successNotification && (
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#34d399',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CheckCircle2 size={18} />
            </div>
            <div>
              <div style={{ fontWeight: 600, color: '#34d399', fontSize: '0.92rem' }}>
                Dataset Ready for Analysis
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Active context set to <strong>{successNotification.datasetName}</strong> (Table:{' '}
                <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-500)' }}>
                  {successNotification.tableName}
                </code>
                )
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <NavLink to="/copilot" className="btn btn-primary btn-sm">
              <span>Open Copilot</span>
              <ArrowRight size={13} />
            </NavLink>
            <button
              onClick={() => setSuccessNotification(null)}
              style={{ color: 'var(--text-muted)', padding: '4px' }}
              title="Dismiss"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && <ErrorMessage message={error} onRetry={() => fetchCatalog(selectedCategory)} />}

      {/* AI Recommendation Assistant */}
      <RecommendationBar
        onViewDetails={(d) => setSelectedDatasetForDetails(d)}
        onDatasetUsed={handleDatasetUsed}
        selectedCategory={selectedCategory}
        onError={(msg) => setError(msg)}
      />

      {/* Category Pills Filtering */}
      <CategoryPills
        selectedCategory={selectedCategory}
        onSelectCategory={(cat) => setSelectedCategory(cat)}
        onError={(msg) => setError(msg)}
      />

      {/* Catalog Grid */}
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {selectedCategory === 'All' ? 'All Popular Datasets' : `${selectedCategory} Datasets`} ({datasets.length})
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label="Loading popular dataset catalog..." />
      ) : datasets.length === 0 ? (
        <EmptyState
          icon={<Database size={40} style={{ color: 'var(--text-muted)' }} />}
          title="No Datasets Found"
          description={`No catalog datasets found in category "${selectedCategory}". Try selecting "All Domains".`}
          action={
            <button
              onClick={() => setSelectedCategory('All')}
              className="btn btn-secondary btn-sm"
            >
              Show All Datasets
            </button>
          }
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '20px',
          }}
        >
          {datasets.map((dataset) => (
            <DatasetCard
              key={dataset.catalog_id}
              dataset={dataset}
              onViewDetails={(d) => setSelectedDatasetForDetails(d)}
              onDatasetUsed={handleDatasetUsed}
              onError={(msg) => setError(msg)}
            />
          ))}
        </div>
      )}

      {/* Details Modal */}
      <DatasetDetailsModal
        dataset={selectedDatasetForDetails}
        onClose={() => setSelectedDatasetForDetails(null)}
        onDatasetUsed={handleDatasetUsed}
        onError={(msg) => setError(msg)}
      />
    </div>
  );
};
