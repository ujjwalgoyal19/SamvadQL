// Deleted: moved to query/QueryExplanation.tsx
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Database,
  Filter,
  ArrowUpDown,
  Users
} from 'lucide-react';

interface QueryExplanationProps {
  explanation: string;
  queryBreakdown?: {
    tables: string[];
    joins: string[];
    filters: string[];
    aggregations: string[];
    sorting: string[];
  };
  showBreakdown?: boolean;
}

export default function QueryExplanation({
  explanation,
  queryBreakdown,
  showBreakdown = true
}: QueryExplanationProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const renderBreakdownSection = (
    title: string,
    items: string[],
    icon: React.ReactNode
  ) => {
    if (!items || items.length === 0) return null;

    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium">
          {icon}
          {title}
        </div>
        <ul className="space-y-1 ml-6">
          {items.map((item, index) => (
            <li key={index} className="text-sm text-muted-foreground">
              • {item}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Query Explanation
          </CardTitle>
          {showBreakdown && queryBreakdown && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Hide Details
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Show Details
                </>
              )}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main Explanation */}
        <div className="prose prose-sm max-w-none">
          <p className="text-muted-foreground leading-relaxed">{explanation}</p>
        </div>

        {/* Detailed Breakdown */}
        {isExpanded && queryBreakdown && (
          <div className="border-t pt-4 space-y-4">
            <div className="flex items-center gap-2 text-base font-semibold">
              <Lightbulb className="h-4 w-4" />
              Query Breakdown
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderBreakdownSection(
                'Tables Used',
                queryBreakdown.tables,
                <Database className="h-4 w-4 text-blue-500" />
              )}

              {renderBreakdownSection(
                'Joins',
                queryBreakdown.joins,
                <Users className="h-4 w-4 text-green-500" />
              )}

              {renderBreakdownSection(
                'Filters Applied',
                queryBreakdown.filters,
                <Filter className="h-4 w-4 text-orange-500" />
              )}

              {renderBreakdownSection(
                'Aggregations',
                queryBreakdown.aggregations,
                <ArrowUpDown className="h-4 w-4 text-purple-500" />
              )}

              {renderBreakdownSection(
                'Sorting',
                queryBreakdown.sorting,
                <ArrowUpDown className="h-4 w-4 text-red-500" />
              )}
            </div>
          </div>
        )}

        {/* Key Insights */}
        <div className="bg-muted/50 p-4 rounded-lg">
          <div className="flex items-start gap-2">
            <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium mb-1">Key Insights</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>
                  • This query retrieves data from{' '}
                  {queryBreakdown?.tables?.length || 1} table(s)
                </li>
                {queryBreakdown?.joins && queryBreakdown.joins.length > 0 && (
                  <li>
                    • Uses {queryBreakdown.joins.length} join(s) to combine data
                  </li>
                )}
                {queryBreakdown?.filters &&
                  queryBreakdown.filters.length > 0 && (
                    <li>
                      • Applies {queryBreakdown.filters.length} filter
                      condition(s)
                    </li>
                  )}
                {queryBreakdown?.aggregations &&
                  queryBreakdown.aggregations.length > 0 && (
                    <li>
                      • Performs {queryBreakdown.aggregations.length}{' '}
                      aggregation(s)
                    </li>
                  )}
              </ul>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
