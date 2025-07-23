/**
 * Root layout component for SamvadQL frontend
 */

import React from 'react';

export const metadata = {
  title: 'SamvadQL - Text-to-SQL Interface',
  description:
    'Conversational interface for database querying using natural language'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div>
          <h6>SamvadQL</h6>
        </div>
        <main>{children}</main>
      </body>
    </html>
  );
}
