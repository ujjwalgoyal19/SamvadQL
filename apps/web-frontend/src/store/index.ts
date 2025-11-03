import { configureStore } from '@reduxjs/toolkit';
import queryReducer from './slices/querySlice';
import uiReducer from './slices/uiSlice';
import tablesReducer from './slices/tablesSlice';

export const store = configureStore({
  reducer: {
    query: queryReducer,
    ui: uiReducer,
    tables: tablesReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST']
      }
    })
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
