import React, { useState } from 'react';
import type { 
  CatalogDatasetSchema, 
  DatasetRecommendationResponse,
  UseCatalogDatasetResponse 
} from '../../types/api';
import { catalogService } from '../../services/catalogService';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { DatasetCard } from './DatasetCard';
import { Sparkles, Search, X, Bot } from 'lucide-react';

interface RecommendationBarProps {
  onViewDetails: (dataset: CatalogDatasetSchema) => void;
  onDatasetUsed: (result: UseCatalogDatasetResponse, dataset: CatalogDatasetSchema) => void;
  selectedCategory?: string;
  onError: (msg: string) => void;
}

export const RecommendationBar: React.FC<RecommendationBarProps> = ({
  onViewDetails,
  onDatasetUsed,
  selectedCategory,
  onError,
}) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DatasetRecommendationResponse | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleRecommend = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    try {
      const data = await catalogService.getRecommendations({
        query: trimmed,
        category: selectedCategory && selectedCategory !== 'All' ? selectedCategory : undefined,
        limit: 3,
      });
      setResult(data);
      setHasSearched(true);
    } catch (err: any) {
      onError(err.message || 'Failed to get dataset recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResult(null);
    setHasSearched(false);
  };

  return (
    <div style={{ marginBottom: '28px' }}>
      <Card
        style={{
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
          border: '1px solid var(--border-strong)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-500)', fontWeight: 600, fontSize: '0.86rem', marginBottom: '8px' }}>
          <Sparkles size={16} />
          <span>AI DATASET RECOMMENDATION ASSISTANT</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '16px', lineHeight: 1.5 }}>
          Describe your business question or analytical goal in plain English. The AI agent will match the best curated datasets.
        </p>

        <form onSubmit={handleRecommend} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '260px', position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '14px', top: '12px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. telecom customer churn, store sales revenue, employee salary & attrition..."
              style={{
                width: '100%',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 14px 10px 40px',
                color: 'var(--text-primary)',
                fontSize: '0.88rem',
              }}
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            loading={loading}
            disabled={loading || !query.trim()}
            icon={<Sparkles size={14} />}
          >
            {loading ? 'Analyzing Goal...' : '✨ Recommend'}
          </Button>

          {hasSearched && (
            <Button
              type="button"
              variant="secondary"
              onClick={handleClear}
              icon={<X size={14} />}
            >
              Clear Results
            </Button>
          )}
        </form>

        {/* AI Recommendations Results Box */}
        {hasSearched && result && (
          <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)' }}>
            {/* Reasoning Alert */}
            {result.reasoning && (
              <div
                style={{
                  background: 'rgba(59, 130, 246, 0.08)',
                  border: '1px solid rgba(59, 130, 246, 0.25)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 18px',
                  display: 'flex',
                  gap: '12px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ color: 'var(--primary-500)', marginTop: '2px' }}>
                  <Bot size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--primary-500)', marginBottom: '3px' }}>
                    AI INTENT ANALYSIS & REASONING
                  </div>
                  <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {result.reasoning}
                  </div>
                </div>
              </div>
            )}

            {/* Recommended Datasets Cards Grid */}
            {result.recommended_datasets.length > 0 ? (
              <div>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                  Recommended Datasets ({result.recommended_datasets.length})
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                  {result.recommended_datasets.map((dataset) => (
                    <DatasetCard
                      key={dataset.catalog_id}
                      dataset={dataset}
                      onViewDetails={onViewDetails}
                      onDatasetUsed={onDatasetUsed}
                      onError={onError}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
                No specific dataset match found for "{result.query}". Try a broader term like "sales", "finance", or "employee".
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
