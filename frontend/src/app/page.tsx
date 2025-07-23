/**
 * Main page component for SamvadQL frontend
 */

'use client';

import { Card, CardContent } from '@/components/ui/card';
export default function HomePage() {
  return (
    <div className="max-w-4xl">
      <div className="my-8">
        <h1 className="text-center mb-2">SamvadQL</h1>
        <h3 className="text-center text-muted-foreground mb-6">
          Text-to-SQL Conversational Interface
        </h3>

        <Card className="mt-6">
          <CardContent className="p-6">
            <p className="mb-4">
              Welcome to SamvadQL, an intelligent Text-to-SQL system that
              transforms natural language queries into precise SQL commands.
              This application is currently under development.
            </p>

            <h4 className="mt-6 mb-3">Features (Coming Soon):</h4>

            <ul className="pl-6 space-y-2">
              <li className="text-sm">
                Natural language to SQL conversion using advanced LLMs
              </li>
              <li className="text-sm">
                Real-time streaming responses with explanations
              </li>
              <li className="text-sm">
                Intelligent table and schema selection
              </li>
              <li className="text-sm">
                SQL validation and optimization suggestions
              </li>
              <li className="text-sm">
                Support for multiple database types (PostgreSQL, MySQL,
                Snowflake, BigQuery)
              </li>
              <li className="text-sm">
                Interactive query refinement and feedback collection
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
