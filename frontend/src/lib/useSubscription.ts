import { useState, useEffect } from 'react';
import { client } from './hasura';

interface SubscriptionState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export function useSubscription<T = any>(
  query: string,
  variables: Record<string, any> = {}
): SubscriptionState<T> {
  const [state, setState] = useState<SubscriptionState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let isMounted = true;
    
    console.log('Setting up subscription with variables:', variables);
    
    // Wrap in try-catch to handle potential initialization errors
    try {
      // Create a subscription with both the request and the sink/observer in a single call
      const unsubscribe = client.subscribe(
        // First argument: GraphQL request
        {
          query,
          variables,
        },
        // Second argument: Observer/Sink
        {
          next(result: any) {
            if (isMounted) {
              console.log('Subscription data received:', result);
              setState({
                data: result.data,
                loading: false,
                error: null,
              });
            }
          },
          error(error: Error) {
            if (isMounted) {
              // Enhanced error logging
              console.error('Subscription error:', error);
              
              // Log additional details about the error object
              console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack,
                constructor: error.constructor?.name,
                toString: String(error),
                keys: Object.keys(error),
                prototype: Object.getPrototypeOf(error)?.constructor?.name,
              });
              
              // Try to log the stringified error (can help with nested objects)
              try {
                console.error('Stringified error:', JSON.stringify(error));
              } catch (e) {
                console.error('Error stringifying error object:', e);
              }
              
              // Log environment variables (without sensitive values)
              console.log('Environment check:', {
                hasGraphQLUrl: !!process.env.NEXT_PUBLIC_HASURA_GRAPHQL_URL,
                hasWsUrl: !!process.env.NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL,
                hasAdminSecret: !!process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET,
                wsUrl: process.env.NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL
              });
              
              setState({
                data: null,
                loading: false,
                error,
              });
            }
          },
          complete() {
            console.log('Subscription completed');
            // Optional: Handle subscription completion
          },
        }
      );

      return () => {
        console.log('Cleaning up subscription');
        isMounted = false;
        // Call the unsubscribe function directly
        unsubscribe();
      };
    } catch (error) {
      console.error('Error setting up subscription:', error);
      if (isMounted) {
        setState({
          data: null,
          loading: false,
          error: error instanceof Error ? error : new Error(String(error)),
        });
      }
      
      // Return a no-op cleanup function
      return () => {
        isMounted = false;
      };
    }
  }, [query, JSON.stringify(variables)]);

  return state;
} 