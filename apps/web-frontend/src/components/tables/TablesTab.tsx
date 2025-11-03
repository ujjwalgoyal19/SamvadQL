import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import {
  setSearchQuery,
  toggleTableSelection,
  clearFilters
} from '@/store/slices/tablesSlice';
import { Database, Search, Filter, CheckCircle, Circle } from 'lucide-react';

export default function TablesTab() {
  const dispatch = useAppDispatch();
  const { selectedTables, searchQuery } = useAppSelector(
    (state) => state.tables
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setSearchQuery(e.target.value));
  };

  const handleTableToggle = (tableName: string) => {
    dispatch(toggleTableSelection(tableName));
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
    }
  ];

  const filteredTables = mockTables.filter(
    (table) =>
      table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      table.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col p-6 max-w-6xl mx-auto">
      {/* Header and Search */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database className="h-6 w-6 text-primary" />
            <h2 className="text-2xl font-bold">Database Tables</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {selectedTables.length} selected
            </span>
            {selectedTables.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => dispatch(clearFilters())}
              >
                Clear Selection
              </Button>
            )}
          </div>
        </div>

        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search tables by name or description..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </Button>
        </div>
      </div>

      {/* Tables Grid */}
      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredTables.map((table) => {
            const isSelected = selectedTables.includes(table.name);
            return (
              <Card
                key={table.name}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  isSelected ? 'ring-2 ring-primary bg-primary/5' : ''
                }`}
                onClick={() => handleTableToggle(table.name)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      {isSelected ? (
                        <CheckCircle className="h-5 w-5 text-primary" />
                      ) : (
                        <Circle className="h-5 w-5 text-muted-foreground" />
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
                            : 'bg-blue-100 text-blue-800'
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
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-sm font-medium mb-2">
                        Columns ({table.columns.length})
                      </h4>
                      <div className="space-y-1">
                        {table.columns.slice(0, 4).map((column) => (
                          <div
                            key={column.name}
                            className="flex justify-between text-xs"
                          >
                            <span className="font-mono">{column.name}</span>
                            <span className="text-muted-foreground">
                              {column.data_type}
                            </span>
                          </div>
                        ))}
                        {table.columns.length > 4 && (
                          <div className="text-xs text-muted-foreground">
                            +{table.columns.length - 4} more columns
                          </div>
                        )}
                      </div>
                    </div>

                    {table.tags.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Tags</h4>
                        <div className="flex flex-wrap gap-1">
                          {table.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 text-xs bg-secondary text-secondary-foreground rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {filteredTables.length === 0 && (
          <div className="flex items-center justify-center h-64 text-center">
            <div className="text-muted-foreground">
              <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No tables found</p>
              <p className="text-sm">
                {searchQuery
                  ? 'Try adjusting your search criteria'
                  : 'No tables are available in the current database'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
// Deleted: moved to tables/TablesTab.tsx
