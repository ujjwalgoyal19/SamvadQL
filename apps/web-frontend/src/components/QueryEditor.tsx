/**
 * Query Editor component with TypeScript integration
 */

import React, { useState, useCallback } from 'react';
import { QueryForm, QueryEditorProps, ValidationError } from '../types';
import { validateQueryRequest } from '../utils/validation';

type DatabaseOption = {
  id: string;
  name: string;
};

interface QueryEditorDynamicProps extends QueryEditorProps {
  databaseOptions: DatabaseOption[];
}

const QueryEditor: React.FC<QueryEditorDynamicProps> = ({
  initialQuery = '',
  onQuerySubmit,
  onQueryChange,
  isLoading = false,
  disabled = false,
  databaseOptions = []
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [databaseId, setDatabaseId] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>(
    []
  );

  const handleQueryChange = useCallback(
    (value: string) => {
      setQuery(value);
      onQueryChange?.(value);

      // Clear validation errors when user starts typing
      if (validationErrors.length > 0) {
        setValidationErrors([]);
      }
    },
    [onQueryChange, validationErrors.length]
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      const formData: QueryForm = {
        query,
        database_id: databaseId,
        selected_tables: selectedTables
      };

      // Validate the form data
      const validation = validateQueryRequest(formData);

      if (!validation.isValid) {
        setValidationErrors(validation.errors);
        return;
      }

      // Clear errors and submit
      setValidationErrors([]);
      onQuerySubmit(formData);
    },
    [query, databaseId, selectedTables, onQuerySubmit]
  );

  const getFieldError = (fieldName: string): string | undefined => {
    const error = validationErrors.find((err) => err.field === fieldName);
    return error?.message;
  };

  const hasFieldError = (fieldName: string): boolean => {
    return validationErrors.some((err) => err.field === fieldName);
  };

  return (
    <div className="query-editor">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Database Selection */}
        <div className="form-group">
          <label
            htmlFor="database-select"
            className="block text-sm font-medium text-gray-700"
          >
            Database
          </label>
          <select
            id="database-select"
            value={databaseId}
            onChange={(e) => setDatabaseId(e.target.value)}
            disabled={disabled}
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
              hasFieldError('database_id') ? 'border-red-500' : ''
            }`}
          >
            <option value="">Select a database...</option>
            {databaseOptions.map((db) => (
              <option key={db.id} value={db.id}>
                {db.name}
              </option>
            ))}
          </select>
          {hasFieldError('database_id') && (
            <p className="mt-1 text-sm text-red-600">
              {getFieldError('database_id')}
            </p>
          )}
        </div>

        {/* Query Input */}
        <div className="form-group">
          <label
            htmlFor="query-input"
            className="block text-sm font-medium text-gray-700"
          >
            Natural Language Query
          </label>
          <textarea
            id="query-input"
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            disabled={disabled}
            placeholder="Enter your question in natural language..."
            rows={4}
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
              hasFieldError('query') ? 'border-red-500' : ''
            }`}
          />
          {hasFieldError('query') && (
            <p className="mt-1 text-sm text-red-600">
              {getFieldError('query')}
            </p>
          )}
          <p className="mt-1 text-sm text-gray-500">
            {query.length}/10,000 characters
          </p>
        </div>

        {/* Table Selection */}
        <div className="form-group">
          <label className="block text-sm font-medium text-gray-700">
            Selected Tables (Optional)
          </label>
          <div className="mt-1">
            <input
              type="text"
              placeholder="Add table names separated by commas..."
              onChange={(e) => {
                const tables = e.target.value
                  .split(',')
                  .map((t) => t.trim())
                  .filter((t) => t.length > 0);
                setSelectedTables(tables);
              }}
              disabled={disabled}
              className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                hasFieldError('selected_tables') ? 'border-red-500' : ''
              }`}
            />
            {hasFieldError('selected_tables') && (
              <p className="mt-1 text-sm text-red-600">
                {getFieldError('selected_tables')}
              </p>
            )}
          </div>
          {selectedTables.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {selectedTables.map((table, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {table}
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedTables((prev) =>
                        prev.filter((_, i) => i !== index)
                      );
                    }}
                    className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full text-blue-400 hover:bg-blue-200 hover:text-blue-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="form-group">
          <button
            type="submit"
            disabled={disabled || isLoading || !query.trim() || !databaseId}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Generating SQL...
              </>
            ) : (
              'Generate SQL'
            )}
          </button>
        </div>

        {/* General Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Please fix the following errors:
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <ul className="list-disc pl-5 space-y-1">
                    {validationErrors.map((error, index) => (
                      <li key={index}>{error.message}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default QueryEditor;
