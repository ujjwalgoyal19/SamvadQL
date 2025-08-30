// Deleted: moved to history/HistoryTab.tsx

// The rest of the code has been removed.
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAppDispatch } from '@/store/hooks';
import { setCurrentQuery } from '@/store/slices/querySlice';
import { History, Search, Clock, Copy, RotateCcw } from 'lucide-react';

export default function HistoryTab() {
  const dispatch = useAppDispatch();
  // const { queryHistory } = useAppSelector((state) => state.query);
  const [searchQuery, setSearchQuery] = React.useState('');

  const handleReuseQuery = (query: string) => {
    dispatch(setCurrentQuery(query));
    // TODO: Switch to query tab
  };

  const handleCopySQL = (sql: string) => {
    navigator.clipboard.writeText(sql);
    // TODO: Show toast notification
  };

  // Mock data for demonstration
  const mockHistory = [
    {
      id: '1',
      query: 'Show me all users who signed up last month',
      sql: 'SELECT * FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)',
      timestamp: '2024-01-15T10:30:00Z'
    },
    {
      id: '2',
      query: 'What are the top 5 products by revenue?',
      sql: 'SELECT p.name, SUM(oi.quantity * oi.price) as revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY revenue DESC LIMIT 5',
      timestamp: '2024-01-15T09:15:00Z'
    },
    {
      id: '3',
      query: 'Find customers with more than 10 orders',
      sql: 'SELECT u.name, u.email, COUNT(o.id) as order_count FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id HAVING order_count > 10',
      timestamp: '2024-01-14T16:45:00Z'
    },
    {
      id: '4',
      query: 'Show me the average order value by month',
      sql: 'SELECT DATE_FORMAT(created_at, "%Y-%m") as month, AVG(total_amount) as avg_order_value FROM orders GROUP BY month ORDER BY month DESC',
      timestamp: '2024-01-14T14:20:00Z'
    }
  ];

  const filteredHistory = mockHistory.filter(
    (item) =>
      item.query.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.sql.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    );

    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours} hours ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays} days ago`;
    }
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-6xl mx-auto">
      {/* Header and Search */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <History className="h-6 w-6 text-primary" />
          <h2 className="text-2xl font-bold">Query History</h2>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search your query history..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-4">
          {filteredHistory.map((item) => (
            <Card key={item.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-2">{item.query}</CardTitle>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      {formatTimestamp(item.timestamp)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopySQL(item.sql)}
                      className="flex items-center gap-1"
                    >
                      <Copy className="h-3 w-3" />
                      Copy SQL
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => handleReuseQuery(item.query)}
                      className="flex items-center gap-1"
                    >
                      <RotateCcw className="h-3 w-3" />
                      Reuse
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div>
                  <h4 className="text-sm font-medium mb-2">Generated SQL:</h4>
                  <pre className="bg-muted p-3 rounded-md text-sm overflow-x-auto">
                    <code>{item.sql}</code>
                  </pre>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredHistory.length === 0 && (
          <div className="flex items-center justify-center h-64 text-center">
            <div className="text-muted-foreground">
              <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">
                {searchQuery
                  ? 'No matching queries found'
                  : 'No query history yet'}
              </p>
              <p className="text-sm">
                {searchQuery
                  ? 'Try adjusting your search criteria'
                  : 'Your generated queries will appear here for easy reuse'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
