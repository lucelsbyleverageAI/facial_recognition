import { useQuery } from '@apollo/client';
import { GET_PROJECTS } from '@/lib/graphql/queries';
import { Project } from '@/types';

export function useProjects() {
  const { data, loading, error, refetch } = useQuery(GET_PROJECTS);
  
  return {
    projects: data?.projects as Project[] || [],
    loading,
    error,
    refetch
  };
} 