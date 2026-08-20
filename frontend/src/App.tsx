import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { DatasetProvider } from './context/DatasetContext';
import { ChatProvider } from './context/ChatContext';
import { AppLayout } from './components/layout/AppLayout';
import { CopilotPage } from './pages/CopilotPage';
import { DatasetHubPage } from './pages/DatasetHubPage';
import { ExplorerPage } from './pages/ExplorerPage';
import { AdminPage } from './pages/AdminPage';
import { LoginPage } from './pages/LoginPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <DatasetProvider>
        <ChatProvider>
          <BrowserRouter>
            <Routes>
              {/* App Shell Routes */}
              <Route path="/" element={<AppLayout />}>
                <Route index element={<Navigate to="/copilot" replace />} />
                <Route path="copilot" element={<CopilotPage />} />
                <Route path="hub" element={<DatasetHubPage />} />
                <Route path="explorer" element={<ExplorerPage />} />
                <Route path="admin" element={<AdminPage />} />
                <Route path="login" element={<LoginPage />} />
                {/* Fallback */}
                <Route path="*" element={<Navigate to="/copilot" replace />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ChatProvider>
      </DatasetProvider>
    </AuthProvider>
  );
};

export default App;
