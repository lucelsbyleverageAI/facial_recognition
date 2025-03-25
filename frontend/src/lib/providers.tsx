'use client';

import { ReactNode } from 'react';
import { ApolloProvider } from '@apollo/client';
import { ThemeProvider } from 'next-themes';
import { apolloClient } from './graphql/client';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ApolloProvider client={apolloClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        {children}
      </ThemeProvider>
    </ApolloProvider>
  );
} 