import React, { useEffect } from 'react';
import { useDataset } from '../context/DatasetContext';
import { useChat } from '../context/ChatContext';
import { Button } from '../components/common/Button';
import { ChatContainer } from '../components/chat/ChatContainer';
import { ChatInput } from '../components/chat/ChatInput';
import { NavLink } from 'react-router-dom';
import { 
  PlusCircle, 
  Database, 
  Layers, 
  BotMessageSquare 
} from 'lucide-react';

export const CopilotPage: React.FC = () => {
  const { activeDataset } = useDataset();
  const { newChat, resetChatForDataset, messages } = useChat();

  const hasDataset = !!(activeDataset.datasetName || activeDataset.tableName);

  // Automatically reset conversation when dataset is switched to prevent cross-dataset memory leakage
  useEffect(() => {
    resetChatForDataset(activeDataset.datasetId);
  }, [activeDataset.datasetId, resetChatForDataset]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - var(--topbar-height) - 64px)' }}>
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--primary-gradient)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <BotMessageSquare size={18} />
          </div>
          <div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              AI SQL Copilot
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Context:{' '}
              {hasDataset ? (
                <span>
                  <strong style={{ color: 'var(--text-primary)' }}>{activeDataset.datasetName}</strong> (Table:{' '}
                  <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-500)' }}>
                    {activeDataset.tableName}
                  </code>
                  )
                </span>
              ) : (
                <span style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
                  All Database Tables (General Schema)
                </span>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {hasDataset && (
            <NavLink to="/explorer" className="btn btn-secondary btn-sm">
              <Layers size={13} />
              <span>Explore Schema</span>
            </NavLink>
          )}

          <NavLink to="/hub" className="btn btn-secondary btn-sm">
            <Database size={13} />
            <span>{hasDataset ? 'Switch Dataset' : 'Select Dataset'}</span>
          </NavLink>

          <Button
            variant="primary"
            size="sm"
            onClick={newChat}
            disabled={messages.length === 0}
            icon={<PlusCircle size={14} />}
          >
            New Chat
          </Button>
        </div>
      </div>

      {/* Main Conversation Container */}
      <ChatContainer />

      {/* Input Bar */}
      <ChatInput />
    </div>
  );
};
