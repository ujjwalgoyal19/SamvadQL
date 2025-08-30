// @ts-nocheck
import React from 'react';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import {
  setLoading,
  setGeneratedSQL,
  setExplanation,
  addToHistory
} from '@/store/slices/querySlice';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import QueryInput from '@/components/QueryInput';
import TableSelector from '@/components/tables/TableSelector';
import QueryRefinement from './QueryRefinement';
import { Sparkles } from 'lucide-react';

export default function QueryTab() {
  const dispatch = useAppDispatch();
  const { currentQuery, isLoading, generatedSQL, explanation } = useAppSelector(
    (state) => state.query
  );
  const [activeStep, setActiveStep] = React.useState<
    'input' | 'tables' | 'results'
  >('input');

  const handleQuerySubmit = async (query: string) => {
    dispatch(setLoading(true));
    setActiveStep('tables');

    // TODO: Implement actual API call
    // Simulate API call for now
    setTimeout(() => {
      const mockSQL = `SELECT u.name, u.email, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY u.id, u.name, u.email
ORDER BY order_count DESC;`;

      const mockExplanation = `This query retrieves users who signed up in the last 30 days along with their order counts. It uses a LEFT JOIN to include users even if they haven't placed any orders, and groups the results by user to count their orders.`;

      dispatch(setGeneratedSQL(mockSQL));
      dispatch(setExplanation(mockExplanation));
      dispatch(
        addToHistory({
          id: Date.now().toString(),
          query,
          sql: mockSQL,
          timestamp: new Date().toISOString()
        })
      );
      dispatch(setLoading(false));
      setActiveStep('results');
    }, 2000);
  };

  const handleTableSelectionChange = (tables: string[]) => {
    // TODO: Update selected tables in query slice
    console.log('Selected tables:', tables);
  };

  const handleQueryRefine = (_refinementRequest: string) => {
    console.log('Refinement request:', _refinementRequest);
    dispatch(setLoading(true));

    // TODO: Implement actual refinement API call
    setTimeout(() => {
      const refinedSQL = generatedSQL + '\nLIMIT 10;';
      dispatch(setGeneratedSQL(refinedSQL));
      dispatch(setLoading(false));
    }, 1500);
  };

  // handleRegenerate removed (unused)

  const handleFeedback = (
    feedback: 'positive' | 'negative',
    comment?: string
  ) => {
    // TODO: Implement feedback submission
    console.log('Feedback:', feedback, comment);
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 'input':
        return (
          <div className="max-w-4xl mx-auto">
            <QueryInput onSubmit={handleQuerySubmit} />
          </div>
        );

      case 'tables':
        return (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">
                Select Relevant Tables
              </h2>
              <p className="text-muted-foreground">
                Choose the tables that are most relevant to your query. The AI
                will use these to generate better SQL.
              </p>
            </div>
            <TableSelector
              onSelectionChange={handleTableSelectionChange}
              maxSelections={5}
            />
            <div className="flex justify-center gap-4">
              <button
                onClick={() => setActiveStep('input')}
                className="px-4 py-2 text-sm border rounded-md hover:bg-muted"
              >
                Back to Query
              </button>
              <button
                onClick={() => setActiveStep('results')}
                disabled={isLoading}
                className="px-6 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              >
                {isLoading ? 'Generating SQL...' : 'Continue to Results'}
              </button>
            </div>
          </div>
        );

      case 'results':
        return (
          <div className="max-w-6xl mx-auto">
            {generatedSQL ? (
              <QueryRefinement
                originalQuery={currentQuery}
                generatedSQL={generatedSQL}
                explanation={explanation}
                onRefine={handleQueryRefine}
                // onRegenerate removed
                onFeedback={handleFeedback}
                isLoading={isLoading}
              />
            ) : (
              <div className="flex items-center justify-center h-64 text-center">
                <div className="text-muted-foreground">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">
                    Ready to generate SQL
                  </p>
                  <p className="text-sm">
                    Complete the previous steps to see your generated SQL query
                  </p>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* Step Indicator */}
      <div className="mb-8">
        <Tabs
          value={activeStep}
          onValueChange={(value) => setActiveStep(value as any)}
        >
          <TabsList className="grid w-full grid-cols-3 max-w-md mx-auto">
            <TabsTrigger value="input">1. Query</TabsTrigger>
            <TabsTrigger value="tables" disabled={!currentQuery}>
              2. Tables
            </TabsTrigger>
            <TabsTrigger value="results" disabled={!generatedSQL}>
              3. Results
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-auto">{renderStepContent()}</div>
    </div>
  );
}
// Deleted: moved to query/QueryTab.tsx
