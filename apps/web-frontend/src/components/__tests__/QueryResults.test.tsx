import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import QueryResults from '../QueryResults';

describe('QueryResults', () => {
  const mockProps = {
    sql: 'SELECT * FROM users WHERE created_at > NOW() - INTERVAL 30 DAY',
    explanation: 'This query retrieves users created in the last 30 days',
    queryBreakdown: {
      tables: ['users'],
      joins: [],
      filters: ['created_at > NOW() - INTERVAL 30 DAY'],
      aggregations: [],
      sorting: []
    },
    optimizationSuggestions: [
      {
        id: '1',
        type: 'performance' as const,
        title: 'Add Index',
        description: 'Consider adding an index',
        impact: 'high' as const,
        category: 'indexing' as const,
        suggestion: 'CREATE INDEX idx_created_at ON users(created_at)',
        estimatedImprovement: '50% faster'
      }
    ]
  };

  it('renders SQL display tab by default', () => {
    render(
      <Provider store={store}>
        <QueryResults {...mockProps} />
      </Provider>
    );

    expect(screen.getByText('SQL')).toBeInTheDocument();
    expect(screen.getByText('Generated SQL')).toBeInTheDocument();
  });

  it('switches between tabs', () => {
    render(
      <Provider store={store}>
        <QueryResults {...mockProps} />
      </Provider>
    );

    // Click on explanation tab
    fireEvent.click(screen.getByText('Explanation'));
    expect(screen.getByText('Query Explanation')).toBeInTheDocument();

    // Click on optimization tab
    fireEvent.click(screen.getByText('Optimize'));
    expect(screen.getByText('Optimization Suggestions')).toBeInTheDocument();
  });

  it('shows optimization badge when suggestions exist', () => {
    render(
      <Provider store={store}>
        <QueryResults {...mockProps} />
      </Provider>
    );

    expect(screen.getByText('1')).toBeInTheDocument(); // Badge showing count
  });

  it('renders feedback tab', () => {
    render(
      <Provider store={store}>
        <QueryResults {...mockProps} />
      </Provider>
    );

    fireEvent.click(screen.getByText('Feedback'));
    expect(screen.getByText('Provide Feedback')).toBeInTheDocument();
  });
});
