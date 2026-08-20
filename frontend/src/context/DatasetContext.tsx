import React, { createContext, useContext, useState, useEffect } from 'react';

export interface ActiveDataset {
  datasetId: string | null;
  datasetName: string | null;
  tableName: string | null;
}

interface DatasetContextType {
  activeDataset: ActiveDataset;
  setActiveDataset: (dataset: ActiveDataset) => void;
  clearActiveDataset: () => void;
}

const STORAGE_KEY = 'zerosql_active_dataset';

const getInitialActiveDataset = (): ActiveDataset => {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY) || localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && typeof parsed === 'object') {
        return {
          datasetId: parsed.datasetId || null,
          datasetName: parsed.datasetName || null,
          tableName: parsed.tableName || null,
        };
      }
    }
  } catch (e) {
    // Ignore storage parsing errors
  }
  return { datasetId: null, datasetName: null, tableName: null };
};

const DatasetContext = createContext<DatasetContextType>({
  activeDataset: { datasetId: null, datasetName: null, tableName: null },
  setActiveDataset: () => {},
  clearActiveDataset: () => {},
});

export const DatasetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeDataset, setActiveDatasetState] = useState<ActiveDataset>(getInitialActiveDataset);

  useEffect(() => {
    try {
      if (activeDataset.datasetId || activeDataset.datasetName || activeDataset.tableName) {
        const serialized = JSON.stringify(activeDataset);
        sessionStorage.setItem(STORAGE_KEY, serialized);
        localStorage.setItem(STORAGE_KEY, serialized);
      } else {
        sessionStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) {
      // Ignore storage errors
    }
  }, [activeDataset]);

  const setActiveDataset = (dataset: ActiveDataset) => {
    setActiveDatasetState(dataset);
  };

  const clearActiveDataset = () => {
    setActiveDatasetState({ datasetId: null, datasetName: null, tableName: null });
  };

  return (
    <DatasetContext.Provider
      value={{
        activeDataset,
        setActiveDataset,
        clearActiveDataset,
      }}
    >
      {children}
    </DatasetContext.Provider>
  );
};

export const useDataset = () => useContext(DatasetContext);
