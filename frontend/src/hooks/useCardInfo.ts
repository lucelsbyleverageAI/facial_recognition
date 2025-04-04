'use client';

import { useQuery } from '@apollo/client';
import { GET_CARD_INFO } from '@/lib/graphql/queries';

interface CardInfoData {
  projects_by_pk: {
    project_id: string;
    project_name: string;
  } | null;
  cards_by_pk: {
    card_id: string;
    card_name: string;
  } | null;
}

export function useCardInfo(projectId: string, cardId: string) {
  const { data, loading, error, refetch } = useQuery<CardInfoData>(GET_CARD_INFO, {
    variables: { projectId, cardId },
    skip: !projectId || !cardId, // Skip if either ID is missing
  });
  
  return {
    projectInfo: data?.projects_by_pk || null,
    cardInfo: data?.cards_by_pk || null,
    loading,
    error,
    refetch,
  };
} 