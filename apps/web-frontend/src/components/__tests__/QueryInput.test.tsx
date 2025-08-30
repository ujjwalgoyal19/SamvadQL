import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import QueryInput from '../QueryInput';

describe('QueryInput', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders query input form', () => {
    render(
      <Provider store={store}>
        <QueryInput onSubmit={mockOnSubmit} />
      </Provider>
    );

    expect(screen.getByText('Natural Language Query')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/Ask a question about your data/)
    ).toBeInTheDocument();
    expect(screen.getByText('Generate SQL')).toBeInTheDocument();
  });

  it('shows validation error for short queries', async () => {
    render(
      <Provider store={store}>
        <QueryInput onSubmit={mockOnSubmit} />
      </Provider>
    );

    const textarea = screen.getByPlaceholderText(
      /Ask a question about your data/
    );
    fireEvent.change(textarea, { target: { value: 'short' } });

    await waitFor(() => {
      expect(
        screen.getByText('Query must be at least 10 characters long')
      ).toBeInTheDocument();
    });
  });

  it('enables submit button for valid queries', async () => {
    render(
      <Provider store={store}>
        <QueryInput onSubmit={mockOnSubmit} />
      </Provider>
    );

    const textarea = screen.getByPlaceholderText(
      /Ask a question about your data/
    );
    const submitButton = screen.getByText('Generate SQL');

    expect(submitButton).toBeDisabled();

    fireEvent.change(textarea, {
      target: { value: 'Show me all users who signed up last month' }
    });

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('calls onSubmit with valid query', async () => {
    render(
      <Provider store={store}>
        <QueryInput onSubmit={mockOnSubmit} />
      </Provider>
    );

    const textarea = screen.getByPlaceholderText(
      /Ask a question about your data/
    );
    const submitButton = screen.getByText('Generate SQL');
    const query = 'Show me all users who signed up last month';

    fireEvent.change(textarea, { target: { value: query } });

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });

    fireEvent.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith(query);
  });

  it('shows character count', () => {
    render(
      <Provider store={store}>
        <QueryInput onSubmit={mockOnSubmit} />
      </Provider>
    );

    const textarea = screen.getByPlaceholderText(
      /Ask a question about your data/
    );
    fireEvent.change(textarea, { target: { value: 'test query' } });

    expect(screen.getByText('10 / 1000 characters')).toBeInTheDocument();
  });

  it('fills query when example is clicked', () => {
    render(
      <Provider store={store}>
        <QueryInput onSubmit={mockOnSubmit} />
      </Provider>
    );

    const exampleButton = screen.getByText(
      'Show me all users who signed up last month'
    );
    fireEvent.click(exampleButton);

    const textarea = screen.getByPlaceholderText(
      /Ask a question about your data/
    ) as HTMLTextAreaElement;
    expect(textarea.value).toBe('Show me all users who signed up last month');
  });
});
