import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface TableSchema {
  name: string;
  database_id: string;
  columns: Array<{
    name: string;
    data_type: string;
    description?: string;
    sample_values?: any[];
    is_nullable: boolean;
  }>;
  description?: string;
  sample_queries: string[];
  tier?: string;
  tags: string[];
}

export interface TablesState {
  availableTables: TableSchema[];
  selectedTables: string[];
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
  filters: {
    database: string[];
    tier: string[];
    tags: string[];
  };
}

const initialState: TablesState = {
  availableTables: [],
  selectedTables: [],
  searchQuery: '',
  isLoading: false,
  error: null,
  filters: {
    database: [],
    tier: [],
    tags: []
  }
};

const tablesSlice = createSlice({
  name: 'tables',
  initialState,
  reducers: {
    setAvailableTables: (state, action: PayloadAction<TableSchema[]>) => {
      state.availableTables = action.payload;
    },
    setSelectedTables: (state, action: PayloadAction<string[]>) => {
      state.selectedTables = action.payload;
    },
    toggleTableSelection: (state, action: PayloadAction<string>) => {
      const tableName = action.payload;
      if (state.selectedTables.includes(tableName)) {
        state.selectedTables = state.selectedTables.filter(
          (name) => name !== tableName
        );
      } else {
        state.selectedTables.push(tableName);
      }
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setFilters: (
      state,
      action: PayloadAction<Partial<TablesState['filters']>>
    ) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        database: [],
        tier: [],
        tags: []
      };
      state.searchQuery = '';
    }
  }
});

export const {
  setAvailableTables,
  setSelectedTables,
  toggleTableSelection,
  setSearchQuery,
  setLoading,
  setError,
  setFilters,
  clearFilters
} = tablesSlice.actions;

export default tablesSlice.reducer;
