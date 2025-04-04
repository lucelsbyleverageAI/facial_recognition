import { useState } from 'react';
import { useQuery, gql } from '@apollo/client';

// Define the GraphQL query to get clips for a card
const GET_CLIPS_BY_CARD = gql`
  query GetClipsByCard($cardId: uuid!, $limit: Int = 10, $offset: Int = 0) {
    clips(
      where: { card_id: { _eq: $cardId } }
      order_by: { filename: asc }
      limit: $limit
      offset: $offset
    ) {
      clip_id
      filename
      path
      status
      error_message
      watch_folder {
        watch_folder_id
        folder_path
        status
      }
    }
    clips_aggregate(where: { card_id: { _eq: $cardId } }) {
      aggregate {
        count
      }
    }
  }
`;

export interface Clip {
  clip_id: string;
  filename: string;
  path: string;
  status: 'pending' | 'unselected' | 'queued' | 'extracting_frames' | 'extraction_complete' | 'processing_complete' | 'error';
  error_message?: string;
  watch_folder?: {
    watch_folder_id: string;
    folder_path: string;
    status: string;
  } | null;
}

export function useClips(cardId: string, limit = 10, offset = 0) {
  const { data, loading, error, refetch, fetchMore } = useQuery(GET_CLIPS_BY_CARD, {
    variables: { cardId, limit, offset },
    skip: !cardId,
    fetchPolicy: 'cache-and-network', // Ensure we always get fresh data
  });
  
  const loadMore = () => {
    if (data?.clips?.length) {
      fetchMore({
        variables: {
          offset: data.clips.length,
          limit,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult) return prev;
          
          return {
            ...prev,
            clips: [
              ...prev.clips,
              ...fetchMoreResult.clips,
            ],
          };
        },
      });
    }
  };
  
  return {
    clips: data?.clips as Clip[] || [],
    totalCount: data?.clips_aggregate?.aggregate?.count || 0,
    loading,
    error,
    loadMore,
    refetch,
  };
} 