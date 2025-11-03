import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useAppDispatch } from '@/store/hooks';
import { setCurrentQuery } from '@/store/slices/querySlice';
import QueryResults from './QueryResults';
import { Edit3, MessageSquare, Wand2 } from 'lucide-react';

interface QueryRefinementProps {
  originalQuery: string;
  generatedSQL: string;
  explanation: string;
  onRefine: (refinementRequest: string) => void;
  // onRegenerate removed (unused)
  onFeedback: (feedback: 'positive' | 'negative', comment?: string) => void;
  isLoading?: boolean;
}

export default function QueryRefinement({
  originalQuery,
  generatedSQL,
  explanation,
  onRefine,
  // onRegenerate,
  onFeedback,
  isLoading = false
}: QueryRefinementProps) {
  const dispatch = useAppDispatch();
  const [refinementMode, setRefinementMode] = React.useState<'chat' | null>(
    null
  );
  const [refinementText, setRefinementText] = React.useState('');

  const handleRefinementSubmit = () => {
    if (refinementText.trim()) {
      onRefine(refinementText);
      setRefinementText('');
      setRefinementMode(null);
    }
  };

  const handleEditQuery = () => {
    dispatch(setCurrentQuery(originalQuery));
  };

  const handleCopySQL = () => {
    // TODO: Show toast notification
  };

  const handleExecuteSQL = () => {
    // TODO: Implement SQL execution
  };

  const handlePreviewSQL = () => {
    // TODO: Implement SQL preview
  };

  const handleApplyOptimization = (suggestionId: string) => {
    // TODO: Implement optimization application
    console.log('Applying optimization:', suggestionId);
  };

  const handleSubmitFeedback = (feedback: any) => {
    onFeedback(feedback.isHelpful ? 'positive' : 'negative', feedback.comment);
  };

  const refinementSuggestions = [
    'Add a WHERE clause to filter by date range',
    'Include GROUP BY to aggregate the results',
    'Add ORDER BY to sort the results',
    'Limit the results to top 10 records',
    'Join with another table for more details',
    'Add COUNT or SUM for aggregation'
  ];

  // Mock query breakdown and optimization suggestions
  const queryBreakdown = {
    tables: ['users', 'orders'],
    joins: ['LEFT JOIN orders ON users.id = orders.user_id'],
    filters: ['users.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)'],
    aggregations: ['COUNT(orders.id) as order_count'],
    sorting: ['ORDER BY order_count DESC']
  };

  const optimizationSuggestions = [
    {
      id: '1',
      type: 'performance' as const,
      title: 'Add Index on created_at Column',
      description:
        'The query filters on users.created_at which could benefit from an index.',
      impact: 'high' as const,
      category: 'indexing' as const,
      suggestion: 'CREATE INDEX idx_users_created_at ON users(created_at);',
      estimatedImprovement: '60% faster execution'
    },
    {
      id: '2',
      type: 'warning' as const,
      title: 'Consider LIMIT Clause',
      description:
        'Query may return a large number of rows without pagination.',
      impact: 'medium' as const,
      category: 'query-structure' as const,
      suggestion:
        'Add LIMIT clause to control result set size, e.g., LIMIT 100',
      estimatedImprovement: '40% less memory usage'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          onClick={() => setRefinementMode('chat')}
          className="flex items-center gap-2"
        >
          <MessageSquare className="h-4 w-4" />
          Refine with Chat
        </Button>
        <Button
          variant="outline"
          onClick={handleEditQuery}
          className="flex items-center gap-2"
        >
          <Edit3 className="h-4 w-4" />
          Edit Original Query
        </Button>
      </div>

      {/* Refinement Interface */}
      {refinementMode === 'chat' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Wand2 className="h-4 w-4" />
              Refine Your Query
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Tell me how you'd like to modify the query:
              </label>
              <Textarea
                placeholder="e.g., 'Add a filter for orders from the last 30 days' or 'Group by product category'"
                value={refinementText}
                onChange={(e) => setRefinementText(e.target.value)}
                className="min-h-[80px]"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Quick Suggestions:
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {refinementSuggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    size="sm"
                    className="justify-start text-left h-auto p-2"
                    onClick={() => setRefinementText(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setRefinementMode(null)}>
                Cancel
              </Button>
              <Button
                onClick={handleRefinementSubmit}
                disabled={!refinementText.trim() || isLoading}
                className="flex items-center gap-2"
              >
                <Wand2 className="h-4 w-4" />
                {isLoading ? 'Refining...' : 'Refine Query'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Query Results */}
      <QueryResults
        sql={generatedSQL}
        explanation={explanation}
        queryBreakdown={queryBreakdown}
        optimizationSuggestions={optimizationSuggestions}
        onCopySQL={handleCopySQL}
        onExecuteSQL={handleExecuteSQL}
        onPreviewSQL={handlePreviewSQL}
        onApplyOptimization={handleApplyOptimization}
        onSubmitFeedback={handleSubmitFeedback}
        isExecuting={isLoading}
      />
    </div>
  );
}
