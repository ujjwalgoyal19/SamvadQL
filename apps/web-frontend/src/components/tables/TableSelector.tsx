import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import {
  setSearchQuery,
  toggleTableSelection,
  clearFilters,
  setFilters
} from '@/store/slices/tablesSlice';
import {
  Database,
  Search,
  Filter,
  CheckCircle,
  Circle,
  X,
  Tag,
  Info
} from 'lucide-react';

interface TableSelectorProps {
  onSelectionChange?: (selectedTables: string[]) => void;
  maxSelections?: number;
  showFilters?: boolean;
}

export default function TableSelector({
  onSelectionChange,
  maxSelections = 10,
  showFilters = true
}: TableSelectorProps) {
  const dispatch = useAppDispatch();
  const { selectedTables, searchQuery, filters } = useAppSelector(
    (state) => state.tables
  );

  const [showFilterPanel, setShowFilterPanel] = React.useState(false);

  React.useEffect(() => {
    onSelectionChange?.(selectedTables);
  }, [selectedTables, onSelectionChange]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setSearchQuery(e.target.value));
  };

  const handleTableToggle = (tableName: string) => {
    if (
      selectedTables.length >= maxSelections &&
      !selectedTables.includes(tableName)
    ) {
      // TODO: Show toast notification about max selections
      return;
    }
    dispatch(toggleTableSelection(tableName));
  };

  const handleClearSelection = () => {
    dispatch(clearFilters());
  };

  const handleFilterChange = (
    filterType: keyof typeof filters,
    value: string[]
  ) => {
    dispatch(setFilters({ [filterType]: value }));
  };

  // Mock data for demonstration
  const mockTables = [
    {
      name: 'users',
      database_id: 'main',
      description: 'User account information and profiles',
      columns: [
        { name: 'id', data_type: 'INTEGER', is_nullable: false },
        { name: 'email', data_type: 'VARCHAR(255)', is_nullable: false },
        { name: 'name', data_type: 'VARCHAR(100)', is_nullable: true },
        { name: 'created_at', data_type: 'TIMESTAMP', is_nullable: false }
      ],
      sample_queries: [
        'SELECT * FROM users WHERE created_at > NOW() - INTERVAL 30 DAY'
      ],
      tier: 'gold',
      tags: ['user-data', 'authentication']
    },
    {
      name: 'orders',
      database_id: 'main',
      description: 'Customer order transactions and details',
      columns: [
        { name: 'id', data_type: 'INTEGER', is_nullable: false },
        { name: 'user_id', data_type: 'INTEGER', is_nullable: false },
        {
          name: 'total_amount',
          data_type: 'DECIMAL(10,2)',
          is_nullable: false
        },
        { name: 'status', data_type: 'VARCHAR(50)', is_nullable: false },
        { name: 'created_at', data_type: 'TIMESTAMP', is_nullable: false }
      ],
      sample_queries: ['SELECT * FROM orders WHERE status = "completed"'],
      tier: 'gold',
      tags: ['transactions', 'revenue']
    },
    {
      name: 'products',
      database_id: 'main',
      description: 'Product catalog and inventory information',
      columns: [
        { name: 'id', data_type: 'INTEGER', is_nullable: false },
        { name: 'name', data_type: 'VARCHAR(255)', is_nullable: false },
        { name: 'price', data_type: 'DECIMAL(10,2)', is_nullable: false },
        { name: 'category_id', data_type: 'INTEGER', is_nullable: true },
        { name: 'stock_quantity', data_type: 'INTEGER', is_nullable: false }
      ],
      sample_queries: ['SELECT * FROM products WHERE stock_quantity > 0'],
      tier: 'silver',
      tags: ['inventory', 'catalog']
    },
    {
      name: 'categories',
      database_id: 'main',
      description: 'Product categories and hierarchies',
      columns: [
        { name: 'id', data_type: 'INTEGER', is_nullable: false },
        { name: 'name', data_type: 'VARCHAR(100)', is_nullable: false },
        { name: 'parent_id', data_type: 'INTEGER', is_nullable: true }
      ],
      sample_queries: ['SELECT * FROM categories WHERE parent_id IS NULL'],
      tier: 'bronze',
      tags: ['catalog', 'hierarchy']
    }
  ];

  const filteredTables = mockTables.filter((table) => {
    const matchesSearch =
      table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      table.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesDatabase =
      filters.database.length === 0 ||
      filters.database.includes(table.database_id);

    const matchesTier =
      filters.tier.length === 0 || filters.tier.includes(table.tier || '');

    const matchesTags =
      filters.tags.length === 0 ||
      filters.tags.some((tag) => table.tags.includes(tag));

    return matchesSearch && matchesDatabase && matchesTier && matchesTags;
  });

  const availableTiers = [
    ...new Set(mockTables.map((t) => t.tier).filter(Boolean))
  ];
  const availableTags = [...new Set(mockTables.flatMap((t) => t.tags))];

  return (
    <div className="space-y-4">
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Select Tables</h3>
          {selectedTables.length > 0 && (
            <span className="text-sm text-muted-foreground">
              ({selectedTables.length}/{maxSelections} selected)
            </span>
          )}
        </div>
        {selectedTables.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearSelection}
            className="flex items-center gap-1"
          >
            <X className="h-3 w-3" />
            Clear
          </Button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tables by name or description..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="pl-10"
          />
        </div>
        {showFilters && (
          <Button
            variant="outline"
            onClick={() => setShowFilterPanel(!showFilterPanel)}
            className="flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
          </Button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilterPanel && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Filters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Tier</label>
              <div className="flex flex-wrap gap-2">
                {availableTiers.map((tier) => (
                  <Button
                    key={tier}
                    variant={
                      filters.tier.includes(tier) ? 'default' : 'outline'
                    }
                    size="sm"
                    onClick={() => {
                      const newTiers = filters.tier.includes(tier)
                        ? filters.tier.filter((t) => t !== tier)
                        : [...filters.tier, tier];
                      handleFilterChange('tier', newTiers);
                    }}
                  >
                    {tier}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Tags</label>
              <div className="flex flex-wrap gap-2">
                {availableTags.map((tag) => (
                  <Button
                    key={tag}
                    variant={filters.tags.includes(tag) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => {
                      const newTags = filters.tags.includes(tag)
                        ? filters.tags.filter((t) => t !== tag)
                        : [...filters.tags, tag];
                      handleFilterChange('tags', newTags);
                    }}
                    className="flex items-center gap-1"
                  >
                    <Tag className="h-3 w-3" />
                    {tag}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selected Tables Summary */}
      {selectedTables.length > 0 && (
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium">Selected Tables:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedTables.map((tableName) => (
                <div
                  key={tableName}
                  className="flex items-center gap-1 bg-primary/10 text-primary px-2 py-1 rounded text-sm"
                >
                  {tableName}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 hover:bg-primary/20"
                    onClick={() => handleTableToggle(tableName)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tables Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
        {filteredTables.map((table) => {
          const isSelected = selectedTables.includes(table.name);
          const canSelect = selectedTables.length < maxSelections || isSelected;

          return (
            <Card
              key={table.name}
              className={`cursor-pointer transition-all hover:shadow-md ${
                isSelected ? 'ring-2 ring-primary bg-primary/5' : ''
              } ${!canSelect ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => canSelect && handleTableToggle(table.name)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    {isSelected ? (
                      <CheckCircle className="h-4 w-4 text-primary" />
                    ) : (
                      <Circle className="h-4 w-4 text-muted-foreground" />
                    )}
                    {table.name}
                  </CardTitle>
                  <div className="flex items-center gap-1">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        table.tier === 'gold'
                          ? 'bg-yellow-100 text-yellow-800'
                          : table.tier === 'silver'
                          ? 'bg-gray-100 text-gray-800'
                          : 'bg-orange-100 text-orange-800'
                      }`}
                    >
                      {table.tier}
                    </span>
                  </div>
                </div>
                {table.description && (
                  <p className="text-sm text-muted-foreground">
                    {table.description}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Info className="h-3 w-3" />
                    {table.columns.length} columns
                  </div>
                  {table.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {table.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 text-xs bg-secondary text-secondary-foreground rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {table.tags.length > 3 && (
                        <span className="text-xs text-muted-foreground">
                          +{table.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredTables.length === 0 && (
        <div className="flex items-center justify-center h-32 text-center">
          <div className="text-muted-foreground">
            <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">
              {searchQuery ||
              filters.database.length ||
              filters.tier.length ||
              filters.tags.length
                ? 'No tables match your search criteria'
                : 'No tables available'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
