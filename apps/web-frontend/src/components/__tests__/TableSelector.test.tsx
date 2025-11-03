import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import TableSelector from '../TableSelector';

describe('TableSelector', () => {
  const mockOnSelectionChange = vi.fn();

  beforeEach(() => {
    mockOnSelectionChange.mockClear();
  });

  it('renders table selector interface', () => {
    render(
      <Provider store={store}>
        <TableSelector onSelectionChange={mockOnSelectionChange} />
      </Provider>
    );

    expect(screen.getByText('Select Tables')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText('Search tables by name or description...')
    ).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('displays mock tables', () => {
    render(
      <Provider store={store}>
        <TableSelector onSelectionChange={mockOnSelectionChange} />
      </Provider>
    );

    expect(screen.getByText('users')).toBeInTheDocument();
    expect(screen.getByText('orders')).toBeInTheDocument();
    expect(screen.getByText('products')).toBeInTheDocument();
    expect(screen.getByText('categories')).toBeInTheDocument();
  });

  it('filters tables by search query', () => {
    render(
      <Provider store={store}>
        <TableSelector onSelectionChange={mockOnSelectionChange} />
      </Provider>
    );

    const searchInput = screen.getByPlaceholderText(
      'Search tables by name or description...'
    );
    fireEvent.change(searchInput, { target: { value: 'user' } });

    expect(screen.getByText('users')).toBeInTheDocument();
    expect(screen.queryByText('products')).not.toBeInTheDocument();
  });

  it('toggles table selection', () => {
    render(
      <Provider store={store}>
        <TableSelector onSelectionChange={mockOnSelectionChange} />
      </Provider>
    );

    const usersTable = screen.getByText('users').closest('.cursor-pointer');
    fireEvent.click(usersTable!);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(['users']);
  });

  it('shows selected tables count', () => {
    render(
      <Provider store={store}>
        <TableSelector onSelectionChange={mockOnSelectionChange} />
      </Provider>
    );

    const usersTable = screen.getByText('users').closest('.cursor-pointer');
    fireEvent.click(usersTable!);

    expect(screen.getByText('(1/10 selected)')).toBeInTheDocument();
  });

  it('shows clear button when tables are selected', () => {
    render(
      <Provider store={store}>
        <TableSelector onSelectionChange={mockOnSelectionChange} />
      </Provider>
    );

    const usersTable = screen.getByText('users').closest('.cursor-pointer');
    fireEvent.click(usersTable!);

    expect(screen.getByText('Clear')).toBeInTheDocument();
  });
});
