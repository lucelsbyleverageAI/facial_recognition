import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

// Create the HTTP link to the Hasura GraphQL endpoint
const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_HASURA_GRAPHQL_URL || 'http://localhost:8080/v1/graphql',
});

// Add the authentication headers to requests
const authLink = setContext((_, { headers }) => {
  // Get the admin secret from environment variables
  const adminSecret = process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET;
  
  // Return the headers to the context
  return {
    headers: {
      ...headers,
      ...(adminSecret ? { 'x-hasura-admin-secret': adminSecret } : {}),
    }
  };
});

// Create the Apollo Client with the combined links
export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
}); 