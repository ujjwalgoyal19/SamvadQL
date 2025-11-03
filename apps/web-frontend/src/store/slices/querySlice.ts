import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface QueryState {
  currentQuery: string;
  generatedSQL: string;
  explanation: string;
  isLoading: boolean;
  error: string | null;
  selectedTables: string[];
  queryHistory: Array<{
    id: string;
    query: string;
    sql: string;
    timestamp: string;
  }>;
}

const initialState: QueryState = {
  currentQuery: '',
  generatedSQL: '',
  explanation: '',
  isLoading: false,
  error: null,
  selectedTables: [],
  queryHistory: []
};

const querySlice = createSlice({
  name: 'query',
  initialState,
  reducers: {
    setCurrentQuery: (state, action: PayloadAction<string>) => {
      state.currentQuery = action.payload;
    },
    setGeneratedSQL: (state, action: PayloadAction<string>) => {
      state.generatedSQL = action.payload;
    },
    setExplanation: (state, action: PayloadAction<string>) => {
      state.explanation = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setSelectedTables: (state, action: PayloadAction<string[]>) => {
      state.selectedTables = action.payload;
    },
    addToHistory: (
      state,
      action: PayloadAction<{
        id: string;
        query: string;
        sql: string;
        timestamp: string;
      }>
    ) => {
      state.queryHistory.unshift(action.payload);
      // Keep only last 50 queries
      if (state.queryHistory.length > 50) {
        state.queryHistory = state.queryHistory.slice(0, 50);
      }
    },
    clearQuery: (state) => {
      state.currentQuery = '';
      state.generatedSQL = '';
      state.explanation = '';
      state.error = null;
      state.selectedTables = [];
    }
  }
});

export const {
  setCurrentQuery,
  setGeneratedSQL,
  setExplanation,
  setLoading,
  setError,
  setSelectedTables,
  addToHistory,
  clearQuery
} = querySlice.actions;

export default querySlice.reducer;
