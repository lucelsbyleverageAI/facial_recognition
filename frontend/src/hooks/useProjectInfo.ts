'use client';

import { useQuery } from '@apollo/client';
import { GET_PROJECT_INFO } from '@/lib/graphql/queries';
import type { Project } from '@/types';

interface ProjectInfo {
  project_id: string;
  project_name: string;
}

export function useProjectInfo(projectId: string) {
  const { data, loading, error, refetch } = useQuery<{ projects_by_pk: ProjectInfo }>(GET_PROJECT_INFO, {
    variables: { projectId },
    skip: !projectId, // Skip query if projectId is not available
  });
  
  return {
    projectInfo: data?.projects_by_pk || null,
    loading,
    error,
    refetch,
  };
} 