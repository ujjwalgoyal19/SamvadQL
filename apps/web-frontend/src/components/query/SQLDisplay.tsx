import React from 'react';

interface SQLDisplayProps {
  sql: string;
  onCopy?: () => void;
  onExecute?: () => void;
  onPreview?: () => void;
  isExecuting?: boolean;
}

const SQLDisplay: React.FC<SQLDisplayProps> = ({ sql }) => {
  return (
    <pre className="p-4 bg-gray-100 rounded-md overflow-auto text-sm">
      <code>{sql}</code>
    </pre>
  );
};

export default SQLDisplay;
