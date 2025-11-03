import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setCurrentQuery } from '@/store/slices/querySlice';
import { Send, Sparkles, AlertCircle } from 'lucide-react';

const querySchema = z.object({
  query: z
    .string()
    .min(10, 'Query must be at least 10 characters long')
    .max(1000, 'Query must be less than 1000 characters')
    .refine((value) => {
      // Basic validation for natural language queries
      const hasQuestionWords =
        /\b(what|who|when|where|why|how|show|find|get|list|count|sum|average|total)\b/i.test(
          value
        );
      const hasDataWords =
        /\b(user|customer|order|product|sale|revenue|data|table|record|row)\b/i.test(
          value
        );
      return hasQuestionWords || hasDataWords;
    }, 'Query should contain question words or data-related terms')
});

type QueryFormData = z.infer<typeof querySchema>;

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
}

export default function QueryInput({
  onSubmit,
  isLoading = false
}: QueryInputProps) {
  const dispatch = useAppDispatch();
  const { currentQuery } = useAppSelector((state) => state.query);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch
  } = useForm<QueryFormData>({
    resolver: zodResolver(querySchema),
    defaultValues: {
      query: currentQuery
    },
    mode: 'onChange'
  });

  const queryValue = watch('query');

  React.useEffect(() => {
    dispatch(setCurrentQuery(queryValue || ''));
  }, [queryValue, dispatch]);

  const handleFormSubmit = (data: QueryFormData) => {
    onSubmit(data.query);
  };

  const handleExampleClick = (example: string) => {
    setValue('query', example);
  };

  const examples = [
    'Show me all users who signed up last month',
    'What are the top 10 products by sales volume?',
    'Find all orders with a total amount greater than $1000',
    'How many customers do we have by country?',
    "What's the average order value for each product category?",
    "Show me users who haven't placed an order in the last 90 days"
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Natural Language Query
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Textarea
                {...register('query')}
                placeholder="Ask a question about your data in natural language...

Examples:
• Show me all users who signed up last month
• What are the top 5 products by revenue?
• Find customers with more than 10 orders"
                className="min-h-[120px] resize-none"
                disabled={isLoading}
              />
              {errors.query && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  {errors.query.message}
                </div>
              )}
            </div>

            <div className="flex justify-between items-center">
              <div className="text-sm text-muted-foreground">
                {queryValue?.length || 0} / 1000 characters
              </div>
              <Button
                type="submit"
                disabled={!isValid || isLoading || !queryValue?.trim()}
                className="flex items-center gap-2"
              >
                <Send className="h-4 w-4" />
                {isLoading ? 'Generating...' : 'Generate SQL'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Quick Examples */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Examples</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {examples.map((example, index) => (
              <Button
                key={index}
                variant="outline"
                className="h-auto p-3 text-left justify-start text-sm"
                onClick={() => handleExampleClick(example)}
                disabled={isLoading}
              >
                {example}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
