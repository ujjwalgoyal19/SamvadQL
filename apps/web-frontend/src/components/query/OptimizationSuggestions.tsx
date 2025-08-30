// React import removed (unused)
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Zap,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  Clock,
  Database,
  Target
} from 'lucide-react';

interface OptimizationSuggestion {
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
}

interface OptimizationSuggestionsProps {
  suggestions: OptimizationSuggestion[];
  onApplySuggestion?: (suggestionId: string) => void;
  showEstimates?: boolean;
}

export default function OptimizationSuggestions({
  suggestions,
  onApplySuggestion,
  showEstimates = true
}: OptimizationSuggestionsProps) {
  const getIcon = (type: OptimizationSuggestion['type']) => {
    switch (type) {
      case 'performance':
        return <TrendingUp className="h-4 w-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getImpactColor = (impact: OptimizationSuggestion['impact']) => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (category: OptimizationSuggestion['category']) => {
    switch (category) {
      case 'indexing':
        return <Database className="h-3 w-3" />;
      case 'query-structure':
        return <Target className="h-3 w-3" />;
      case 'joins':
        return <TrendingUp className="h-3 w-3" />;
      case 'filtering':
        return <AlertTriangle className="h-3 w-3" />;
      case 'aggregation':
        return <Zap className="h-3 w-3" />;
      default:
        return <Info className="h-3 w-3" />;
    }
  };

  if (suggestions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            Query Optimization
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Query Looks Good!</h3>
            <p className="text-muted-foreground">
              No optimization suggestions at this time. Your query appears to be
              well-structured.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-500" />
          Optimization Suggestions
          <span className="text-sm font-normal text-muted-foreground">
            ({suggestions.length} suggestion
            {suggestions.length !== 1 ? 's' : ''})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className="border rounded-lg p-4 space-y-3 hover:shadow-sm transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  {getIcon(suggestion.type)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{suggestion.title}</h4>
                      <span
                        className={`px-2 py-1 text-xs rounded-full border ${getImpactColor(
                          suggestion.impact
                        )}`}
                      >
                        {suggestion.impact} impact
                      </span>
                      <span className="flex items-center gap-1 px-2 py-1 text-xs bg-muted rounded-full">
                        {getCategoryIcon(suggestion.category)}
                        {suggestion.category}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {suggestion.description}
                    </p>
                  </div>
                </div>
                {onApplySuggestion && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onApplySuggestion(suggestion.id)}
                    className="flex items-center gap-1"
                  >
                    <Zap className="h-3 w-3" />
                    Apply
                  </Button>
                )}
              </div>

              {/* Suggestion Details */}
              <div className="bg-muted/50 p-3 rounded-md">
                <h5 className="text-sm font-medium mb-1">
                  Suggested Improvement:
                </h5>
                <p className="text-sm text-muted-foreground">
                  {suggestion.suggestion}
                </p>
              </div>

              {/* Estimated Improvement */}
              {showEstimates && suggestion.estimatedImprovement && (
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-green-500" />
                  <span className="text-muted-foreground">
                    Estimated improvement:
                  </span>
                  <span className="font-medium text-green-600">
                    {suggestion.estimatedImprovement}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-500 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Optimization Summary
              </h4>
              <p className="text-sm text-blue-700">
                Implementing these suggestions could improve query performance
                and reduce resource usage. Consider applying high-impact
                suggestions first for the best results.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
