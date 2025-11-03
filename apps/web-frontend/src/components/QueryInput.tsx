import React, { useState, useEffect } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
}

const exampleQueries = ['Show me all users who signed up last month'];

const QueryInput: React.FC<QueryInputProps> = ({ onSubmit }) => {
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query && query.trim().length > 0 && query.trim().length < 10) {
      setError('Query must be at least 10 characters long');
    } else {
      setError(null);
    }
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!error && query.trim().length >= 10) {
      onSubmit(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Natural Language Query
        </label>
        <textarea
          placeholder="Ask a question about your data"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={4}
          className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
            error ? 'border-red-500' : ''
          }`}
        />
        <p className="mt-1 text-sm text-gray-500">
          {query.length} / 1000 characters
        </p>
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        {exampleQueries.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => setQuery(ex)}
            className="px-3 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200"
          >
            {ex}
          </button>
        ))}
      </div>
      <button
        type="submit"
        disabled={!!error || query.trim().length < 10}
        className="mt-2 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Generate SQL
      </button>
    </form>
  );
};

export default QueryInput;
