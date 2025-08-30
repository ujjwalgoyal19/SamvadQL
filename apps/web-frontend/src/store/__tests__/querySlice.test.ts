import { describe, it, expect } from 'vitest';
import queryReducer, {
  setCurrentQuery,
  setGeneratedSQL,
  setExplanation,
  setLoading,
  clearQuery
} from '../slices/querySlice';

describe('querySlice', () => {
  const initialState = {
    currentQuery: '',
    generatedSQL: '',
    explanation: '',
    isLoading: false,
    error: null,
    selectedTables: [],
    queryHistory: []
  };

  it('should handle setCurrentQuery', () => {
    const actual = queryReducer(initialState, setCurrentQuery('test query'));
    expect(actual.currentQuery).toBe('test query');
  });

  it('should handle setGeneratedSQL', () => {
    const actual = queryReducer(
      initialState,
      setGeneratedSQL('SELECT * FROM users')
    );
    expect(actual.generatedSQL).toBe('SELECT * FROM users');
  });

  it('should handle setExplanation', () => {
    const actual = queryReducer(
      initialState,
      setExplanation('This query selects all users')
    );
    expect(actual.explanation).toBe('This query selects all users');
  });

  it('should handle setLoading', () => {
    const actual = queryReducer(initialState, setLoading(true));
    expect(actual.isLoading).toBe(true);
  });

  it('should handle clearQuery', () => {
    const stateWithData = {
      ...initialState,
      currentQuery: 'test',
      generatedSQL: 'SELECT * FROM test',
      explanation: 'test explanation'
    };

    const actual = queryReducer(stateWithData, clearQuery());
    expect(actual.currentQuery).toBe('');
    expect(actual.generatedSQL).toBe('');
    expect(actual.explanation).toBe('');
  });
});
