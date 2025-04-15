import { createClient } from 'graphql-ws';

// Log environment variables (without actual values for security)
console.log('Hasura environment check:', {
  hasWsUrl: !!process.env.NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL,
  wsUrlSet: process.env.NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL !== undefined,
  hasAdminSecret: !!process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET,
  adminSecretSet: process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET !== undefined,
  fallbackWsUrl: 'ws://localhost:8080/v1/graphql',
});

// Configure the WebSocket client for Hasura GraphQL subscriptions
export const client = createClient({
  url: process.env.NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL || 'ws://localhost:8080/v1/graphql',
  connectionParams: {
    headers: {
      'x-hasura-admin-secret': process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET || '',
    },
  },
  // Add connection status callbacks
  on: {
    connected: (socket) => console.log('GraphQL WebSocket connected'),
    
    connecting: () => console.log('GraphQL WebSocket connecting...'),
    
    closed: (event) => console.log('GraphQL WebSocket closed', event),
    
    error: (error) => {
      console.error('GraphQL WebSocket error:', error);
      console.error('Connection details:', {
        wsUrl: process.env.NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL || 'ws://localhost:8080/v1/graphql',
        hasAdminSecret: !!process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET
      });
    },
  },
  // Add retry logic
  retryAttempts: 5,
  retryWait: (retries) => new Promise((resolve) => {
    const delay = Math.min(1000 * (2 ** retries), 10000); // Exponential backoff capped at 10 seconds
    console.log(`Retrying WebSocket connection in ${delay}ms (attempt ${retries})`);
    setTimeout(resolve, delay);
  }),
  shouldRetry: (error) => {
    console.error('GraphQL WebSocket connection failed, will retry:', error);
    return true; // Always retry on error
  },
}); 