import { useQuery } from '@apollo/client';
import { GET_CARDS_BY_PROJECT } from '@/lib/graphql/queries';
import { Card } from '@/types';

export function useCards(projectId: string, limit = 5, offset = 0) {
  const { data, loading, error, fetchMore } = useQuery(GET_CARDS_BY_PROJECT, {
    variables: { projectId, limit, offset },
    skip: !projectId,
  });
  
  const loadMore = () => {
    if (data?.cards?.length) {
      fetchMore({
        variables: {
          offset: data.cards.length,
          limit,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult) return prev;
          
          return {
            ...prev,
            cards: [
              ...prev.cards,
              ...fetchMoreResult.cards,
            ],
          };
        },
      });
    }
  };
  
  return {
    cards: data?.cards as Card[] || [],
    totalCount: data?.cards_aggregate?.aggregate?.count || 0,
    loading,
    error,
    loadMore,
  };
} 