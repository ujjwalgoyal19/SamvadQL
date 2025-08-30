import React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import SQLDisplay from './SQLDisplay';
import QueryExplanation from './QueryExplanation';
import OptimizationSuggestions from './OptimizationSuggestions';
import FeedbackCollection from './FeedbackCollection';
import {
  Code,
  MessageSquare,
  Zap,
  MessageCircle,
  Play,
  BarChart3
} from 'lucide-react';

interface QueryResultsProps {
  sql: string;
  explanation: string;
  queryBreakdown?: {
    tables: string[];
    joins: string[];
    filters: string[];
    aggregations: string[];
    sorting: string[];
  };
  optimizationSuggestions?: Array<{
    id: string;
    type: 'performance' | 'warning' | 'info' | 'success';
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    category:
      | 'indexing'
      | 'query-structure'
      | 'joins'
      | 'filtering'
      | 'aggregation';
    suggestion: string;
    estimatedImprovement?: string;
  }>;
  onCopySQL?: () => void;
  onExecuteSQL?: () => void;
  onPreviewSQL?: () => void;
  onApplyOptimization?: (suggestionId: string) => void;
  onSubmitFeedback?: (feedback: any) => void;
  isExecuting?: boolean;
  isFeedbackSubmitting?: boolean;
}

export default function QueryResults({
  sql,
  explanation,
  queryBreakdown,
  optimizationSuggestions = [],
  onCopySQL,
  onExecuteSQL,
  onPreviewSQL,
  onApplyOptimization,
  onSubmitFeedback,
  isExecuting = false,
  isFeedbackSubmitting = false
}: QueryResultsProps) {
  const [activeTab, setActiveTab] = React.useState('sql');

  // Mock execution results for demonstration
  const [executionResults, setExecutionResults] = React.useState<any>(null);

  const handleExecuteSQL = () => {
    onExecuteSQL?.();

    // Simulate execution results
    setTimeout(() => {
      setExecutionResults({
        rowCount: 42,
        executionTime: '0.15s',
        columns: ['name', 'email', 'order_count'],
        sampleRows: [
          { name: 'John Doe', email: 'john@example.com', order_count: 5 },
          { name: 'Jane Smith', email: 'jane@example.com', order_count: 3 },
          { name: 'Bob Johnson', email: 'bob@example.com', order_count: 8 }
        ]
      });
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="sql" className="flex items-center gap-2">
            <Code className="h-4 w-4" />
            SQL
          </TabsTrigger>
          <TabsTrigger value="explanation" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Explanation
          </TabsTrigger>
          <TabsTrigger value="optimization" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Optimize
            {optimizationSuggestions.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-500 text-white rounded-full">
                {optimizationSuggestions.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="results" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Results
          </TabsTrigger>
          <TabsTrigger value="feedback" className="flex items-center gap-2">
            <MessageCircle className="h-4 w-4" />
            Feedback
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sql" className="mt-6">
          <SQLDisplay
            sql={sql}
            onCopy={onCopySQL}
            onExecute={handleExecuteSQL}
            onPreview={onPreviewSQL}
            isExecuting={isExecuting}
          />
        </TabsContent>

        <TabsContent value="explanation" className="mt-6">
          <QueryExplanation
            explanation={explanation}
            queryBreakdown={queryBreakdown}
          />
        </TabsContent>

        <TabsContent value="optimization" className="mt-6">
          <OptimizationSuggestions
            suggestions={optimizationSuggestions}
            onApplySuggestion={onApplyOptimization}
          />
        </TabsContent>

        <TabsContent value="results" className="mt-6">
          {executionResults ? (
            <div className="space-y-4">
              {/* Execution Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card p-4 rounded-lg border">
                  <div className="text-2xl font-bold text-green-600">
                    {executionResults.rowCount}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Rows Returned
                  </div>
                </div>
                <div className="bg-card p-4 rounded-lg border">
                  <div className="text-2xl font-bold text-blue-600">
                    {executionResults.executionTime}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Execution Time
                  </div>
                </div>
                <div className="bg-card p-4 rounded-lg border">
                  <div className="text-2xl font-bold text-purple-600">
                    {executionResults.columns.length}
                  </div>
                  <div className="text-sm text-muted-foreground">Columns</div>
                </div>
              </div>

              {/* Sample Results */}
              <div className="bg-card rounded-lg border overflow-hidden">
                <div className="p-4 border-b">
                  <h3 className="font-semibold">Sample Results</h3>
                  <p className="text-sm text-muted-foreground">
                    Showing first 3 rows of {executionResults.rowCount} total
                    results
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted/50">
                      <tr>
                        {executionResults.columns.map((column: string) => (
                          <th
                            key={column}
                            className="px-4 py-2 text-left text-sm font-medium"
                          >
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {executionResults.sampleRows.map(
                        (row: any, index: number) => (
                          <tr key={index} className="border-t">
                            {executionResults.columns.map((column: string) => (
                              <td key={column} className="px-4 py-2 text-sm">
                                {row[column]}
                              </td>
                            ))}
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <Play className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">
                Execute Query to See Results
              </h3>
              <p className="text-muted-foreground mb-4">
                Click the "Execute" button in the SQL tab to run your query and
                see the results here.
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="feedback" className="mt-6">
          <FeedbackCollection
            onSubmitFeedback={onSubmitFeedback || (() => {})}
            isSubmitting={isFeedbackSubmitting}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
