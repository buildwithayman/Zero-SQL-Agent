import React, { useState, useEffect } from 'react';
import { datasetService } from '../../services/datasetService';
import { useChat } from '../../context/ChatContext';
import { useNavigate } from 'react-router-dom';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../components/../common/ErrorMessage';
import { 
  Sparkles, 
  RefreshCw, 
  Copy, 
  Check, 
  ArrowRight, 
  HelpCircle 
} from 'lucide-react';

interface SuggestedPromptsProps {
  datasetId: string;
  datasetName: string;
}

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({
  datasetId,
  datasetName,
}) => {
  const { selectedPrompt, setSelectedPrompt } = useChat();
  const navigate = useNavigate();

  const [prompts, setPrompts] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const fetchPrompts = async (id: string, isMounted = () => true) => {
    setLoading(true);
    setError(null);
    try {
      const res = await datasetService.getDatasetPrompts(id);
      if (isMounted()) {
        setPrompts(res.suggested_prompts || []);
      }
    } catch (err: any) {
      if (isMounted()) {
        setError(err.message || 'Failed to load suggested questions for this dataset.');
        setPrompts([]);
      }
    } finally {
      if (isMounted()) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    let mounted = true;
    if (datasetId) {
      fetchPrompts(datasetId, () => mounted);
    }
    return () => {
      mounted = false;
    };
  }, [datasetId]);

  const handleCopy = (text: string, index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleUseInCopilot = (prompt: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedPrompt(prompt);
    navigate('/copilot');
  };

  return (
    <div style={{ marginTop: '36px' }}>
      {/* Section Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-500)', fontWeight: 600, fontSize: '0.86rem' }}>
            <Sparkles size={16} />
            <span>AI SCHEMA-DRIVEN SUGGESTED QUESTIONS</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', marginTop: '2px' }}>
            Automatic questions generated from {datasetName}'s columns, numerical metrics, and categorical dimensions.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => fetchPrompts(datasetId)}
          loading={loading}
          disabled={loading}
          icon={<RefreshCw size={13} className={loading ? 'spinner' : ''} />}
        >
          {loading ? 'Refreshing...' : '↻ Refresh Questions'}
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <ErrorMessage
          message={error}
          onRetry={() => fetchPrompts(datasetId)}
        />
      )}

      {/* Loading State */}
      {loading ? (
        <Card>
          <LoadingSpinner label="Generating schema-driven questions from PostgreSQL metadata..." />
        </Card>
      ) : prompts.length === 0 ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            <HelpCircle size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
            <div>No suggested questions are available for this dataset yet.</div>
          </div>
        </Card>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
          {prompts.map((promptText, idx) => {
            const isSelected = selectedPrompt === promptText;
            const isCopied = copiedIndex === idx;

            return (
              <Card
                key={idx}
                interactive
                onClick={() => setSelectedPrompt(promptText)}
                style={{
                  padding: '16px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px',
                  borderColor: isSelected ? 'var(--primary-500)' : undefined,
                  background: isSelected
                    ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(30, 41, 59, 0.8) 100%)'
                    : undefined,
                  boxShadow: isSelected ? '0 0 12px rgba(59, 130, 246, 0.2)' : undefined,
                }}
              >
                {/* Question Text */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <span style={{ color: 'var(--primary-500)', fontSize: '0.9rem', marginTop: '2px' }}>💬</span>
                  <span style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.4 }}>
                    "{promptText}"
                  </span>
                </div>

                {/* Actions Bar */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: '10px',
                    borderTop: '1px solid var(--border-subtle)',
                  }}
                >
                  <button
                    onClick={(e) => handleCopy(promptText, idx, e)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '0.75rem',
                      color: isCopied ? '#34d399' : 'var(--text-muted)',
                      padding: '4px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-surface-elevated)',
                    }}
                    title="Copy question text"
                  >
                    {isCopied ? <Check size={12} /> : <Copy size={12} />}
                    <span>{isCopied ? 'Copied' : 'Copy'}</span>
                  </button>

                  <button
                    onClick={(e) => handleUseInCopilot(promptText, e)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      color: 'var(--primary-500)',
                      padding: '4px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(59, 130, 246, 0.1)',
                      border: '1px solid rgba(59, 130, 246, 0.25)',
                    }}
                    title="Stage question in Copilot"
                  >
                    <span>Use in Copilot</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
