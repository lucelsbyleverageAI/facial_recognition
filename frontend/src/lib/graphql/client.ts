import { ApolloClient, InMemoryCache, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

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

// Setup WebSocket link for subscriptions
const wsUrl = (process.env.NEXT_PUBLIC_HASURA_GRAPHQL_URL || 'http://localhost:8080/v1/graphql')
  .replace('http://', 'ws://')
  .replace('https://', 'wss://');

const wsLink = new GraphQLWsLink(createClient({
  url: wsUrl,
  connectionParams: {
    headers: {
      'x-hasura-admin-secret': process.env.NEXT_PUBLIC_HASURA_ADMIN_SECRET,
    },
  },
}));

// Split links based on operation type
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  authLink.concat(httpLink)
);

// Create the Apollo Client with the combined links
export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
}); 