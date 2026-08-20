import React, { useState, useMemo } from 'react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { DataTable } from './DataTable';
import { ExportButton } from './ExportButton';
import { BarChart3, Table as TableIcon, LineChart as LineChartIcon, PieChart as PieChartIcon } from 'lucide-react';

interface VisualizerProps {
  columns: string[];
  rows: Record<string, any>[];
  visualizationType?: 'bar' | 'line' | 'pie' | 'table' | string | null;
  rowCount?: number;
  executionTimeMs?: number;
  tableName?: string | null;
}

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

export const Visualizer: React.FC<VisualizerProps> = ({
  columns,
  rows,
  visualizationType = 'table',
  rowCount,
  executionTimeMs,
  tableName,
}) => {
  const hasRows = rows && rows.length > 0;
  const initialTab = (visualizationType && visualizationType !== 'table' && hasRows) ? 'chart' : 'table';
  const [activeTab, setActiveTab] = useState<'chart' | 'table'>(initialTab);

  // Analyze columns to identify category and numerical metric axes
  const { categoryKey, metricKeys, isChartable } = useMemo(() => {
    if (!columns || columns.length === 0 || !rows || rows.length === 0) {
      return { categoryKey: '', metricKeys: [], isChartable: false };
    }

    let catKey = '';
    const numKeys: string[] = [];

    // Find categorical vs numeric columns
    columns.forEach((col) => {
      const sample = rows[0][col];
      if (typeof sample === 'number') {
        numKeys.push(col);
      } else if (!catKey && (typeof sample === 'string' || typeof sample === 'boolean')) {
        catKey = col;
      }
    });

    // Fallbacks if not cleanly detected
    if (!catKey && columns.length > 0) catKey = columns[0];
    if (numKeys.length === 0 && columns.length > 1) {
      // Try to parse numeric strings
      const secondCol = columns[1];
      const parsed = parseFloat(rows[0][secondCol]);
      if (!isNaN(parsed)) {
        numKeys.push(secondCol);
      }
    }

    return {
      categoryKey: catKey,
      metricKeys: numKeys,
      isChartable: numKeys.length > 0 && !!catKey,
    };
  }, [columns, rows]);

  // Format data for Recharts (convert strings to numbers for metric keys)
  const chartData = useMemo(() => {
    if (!hasRows) return [];
    return rows.map((row) => {
      const formatted: Record<string, any> = { ...row };
      metricKeys.forEach((key) => {
        const val = parseFloat(row[key]);
        formatted[key] = isNaN(val) ? 0 : val;
      });
      return formatted;
    });
  }, [rows, metricKeys, hasRows]);

  if (!hasRows) {
    return <DataTable columns={columns} rows={rows} rowCount={rowCount} executionTimeMs={executionTimeMs} />;
  }

  const renderChart = () => {
    if (!isChartable) {
      return <DataTable columns={columns} rows={rows} rowCount={rowCount} executionTimeMs={executionTimeMs} />;
    }

    const type = (visualizationType || 'bar').toLowerCase();

    if (type === 'line') {
      return (
        <div style={{ width: '100%', height: 280, padding: '16px 8px 8px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey={categoryKey} stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {metricKeys.map((key, idx) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={PIE_COLORS[idx % PIE_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3, fill: PIE_COLORS[idx % PIE_COLORS.length] }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (type === 'pie') {
      const metricKey = metricKeys[0];
      return (
        <div style={{ width: '100%', height: 280, padding: '16px 8px 8px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Pie
                data={chartData}
                dataKey={metricKey}
                nameKey={categoryKey}
                cx="50%"
                cy="50%"
                outerRadius={90}
                innerRadius={35}
                paddingAngle={2}
                label={({ name, percent }: any) => `${name} (${(percent * 100).toFixed(0)}%)`}
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Default: Bar Chart
    return (
      <div style={{ width: '100%', height: 280, padding: '16px 8px 8px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey={categoryKey} stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
              labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {metricKeys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                fill={PIE_COLORS[idx % PIE_COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div
      style={{
        background: 'var(--bg-app)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        margin: '12px 0',
      }}
    >
      {/* Visualizer Top Bar: View Switcher & Export */}
      <div
        style={{
          padding: '8px 14px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {isChartable && (
            <button
              onClick={() => setActiveTab('chart')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 9px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.74rem',
                fontWeight: 600,
                background: activeTab === 'chart' ? 'var(--primary-gradient)' : 'var(--bg-surface-elevated)',
                color: activeTab === 'chart' ? '#fff' : 'var(--text-secondary)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {visualizationType === 'line' ? (
                <LineChartIcon size={12} />
              ) : visualizationType === 'pie' ? (
                <PieChartIcon size={12} />
              ) : (
                <BarChart3 size={12} />
              )}
              <span>Visual Chart ({visualizationType?.toUpperCase() || 'BAR'})</span>
            </button>
          )}

          <button
            onClick={() => setActiveTab('table')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 9px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.74rem',
              fontWeight: 600,
              background: activeTab === 'table' ? 'var(--primary-gradient)' : 'var(--bg-surface-elevated)',
              color: activeTab === 'table' ? '#fff' : 'var(--text-secondary)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <TableIcon size={12} />
            <span>Data Matrix</span>
          </button>
        </div>

        <ExportButton columns={columns} rows={rows} tableName={tableName} />
      </div>

      {/* View Content */}
      {activeTab === 'chart' && isChartable ? (
        renderChart()
      ) : (
        <DataTable columns={columns} rows={rows} rowCount={rowCount} executionTimeMs={executionTimeMs} />
      )}
    </div>
  );
};
