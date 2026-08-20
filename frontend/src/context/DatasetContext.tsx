import React, { createContext, useContext, useState } from 'react';

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

const DatasetContext = createContext<DatasetContextType>({
  activeDataset: { datasetId: null, datasetName: null, tableName: null },
  setActiveDataset: () => {},
  clearActiveDataset: () => {},
});

export const DatasetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeDataset, setActiveDataset] = useState<ActiveDataset>({
    datasetId: null,
    datasetName: null,
    tableName: null,
  });

  const clearActiveDataset = () => {
    setActiveDataset({ datasetId: null, datasetName: null, tableName: null });
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
