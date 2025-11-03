import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import QueryTab from '../QueryTab';

describe('QueryTab', () => {
  it('renders query input and results sections', () => {
    render(
      <Provider store={store}>
        <QueryTab />
      </Provider>
    );

    expect(screen.getByText('Natural Language Query')).toBeInTheDocument();
    expect(screen.getByText('Generated SQL & Explanation')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/Ask a question about your data/)
    ).toBeInTheDocument();
  });

  it('shows generate SQL button', () => {
    render(
      <Provider store={store}>
        <QueryTab />
      </Provider>
    );

    expect(screen.getByText('Generate SQL')).toBeInTheDocument();
  });
});
