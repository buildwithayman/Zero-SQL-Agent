import React, { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import { useDataset } from '../../context/DatasetContext';
import { MessageBubble } from './MessageBubble';
import { Sparkles, BotMessageSquare, Database, ArrowRight } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export const ChatContainer: React.FC = () => {
  const { messages, sendMessage, isSending } = useChat();
  const { activeDataset } = useDataset();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const hasDataset = !!(activeDataset.datasetName || activeDataset.tableName);

  const defaultStarterQuestions = hasDataset
    ? [
        `What is the total and average metrics in ${activeDataset.datasetName}?`,
        `Show the top 5 records by highest numeric metric.`,
        `Calculate counts and distributions grouped by category or segment.`,
        `Show the first 10 rows of this dataset ordered ascending.`,
      ]
    : [
        'List all available database tables and their total record counts.',
        'Show summary statistics across the active schema.',
        'What tables exist in the database with sales or employee records?',
      ];

  return (
    <div style={{ flex: 1, padding: '24px 16px', overflowY: 'auto', minHeight: '380px' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        {messages.length === 0 ? (
          /* Empty State / Welcome Screen */
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: '48px 16px',
            }}
          >
            <div
              style={{
                width: '54px',
                height: '54px',
                borderRadius: 'var(--radius-lg)',
                background: 'var(--primary-gradient)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
                boxShadow: 'var(--shadow-glow)',
              }}
            >
              <BotMessageSquare size={28} />
            </div>

            <h2 style={{ fontSize: '1.45rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
              {hasDataset ? `AI Analytics Copilot for ${activeDataset.datasetName}` : 'Enterprise AI SQL Copilot'}
            </h2>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '580px', lineHeight: 1.6, marginBottom: '28px' }}>
              {hasDataset
                ? `Query table ${activeDataset.tableName} in natural English. Multi-turn reasoning, AST token guardrails, and automated charts are active.`
                : 'Ask questions across all relational tables in natural English, or select a curated dataset from the Dataset Hub.'}
            </p>

            {/* Starter Questions Grid */}
            <div style={{ width: '100%', maxWidth: '780px', textAlign: 'left' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} style={{ color: 'var(--primary-500)' }} />
                <span>Suggested Analytical Prompts</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '10px' }}>
                {defaultStarterQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => !isSending && sendMessage(q, activeDataset.datasetId, activeDataset.tableName)}
                    disabled={isSending}
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 16px',
                      color: 'var(--text-primary)',
                      fontSize: '0.84rem',
                      textAlign: 'left',
                      lineHeight: 1.4,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '8px',
                      transition: 'all 0.15s ease',
                      cursor: isSending ? 'not-allowed' : 'pointer',
                    }}
                    className="card-interactive"
                  >
                    <span>💬 "{q}"</span>
                    <ArrowRight size={13} style={{ color: 'var(--primary-500)', flexShrink: 0 }} />
                  </button>
                ))}
              </div>

              {!hasDataset && (
                <div style={{ marginTop: '20px', textAlign: 'center' }}>
                  <NavLink to="/hub" className="btn btn-secondary btn-sm">
                    <Database size={13} />
                    <span>Browse 7 Curated Datasets in Hub</span>
                  </NavLink>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Chronological Messages */
          <div>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};
