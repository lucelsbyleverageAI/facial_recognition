import { useQuery } from '@apollo/client';
import { GET_CONSENT_PROFILES_BY_PROJECT } from '@/lib/graphql/queries';
import { ConsentProfile } from '@/types';

export function useConsentProfiles(projectId: string, limit = 5, offset = 0) {
  const { data, loading, error, fetchMore } = useQuery(GET_CONSENT_PROFILES_BY_PROJECT, {
    variables: { projectId, limit, offset },
    skip: !projectId,
  });
  
  const loadMore = () => {
    if (data?.consent_profiles?.length) {
      fetchMore({
        variables: {
          offset: data.consent_profiles.length,
          limit,
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult) return prev;
          
          return {
            ...prev,
            consent_profiles: [
              ...prev.consent_profiles,
              ...fetchMoreResult.consent_profiles,
            ],
          };
        },
      });
    }
  };
  
  return {
    consentProfiles: data?.consent_profiles as ConsentProfile[] || [],
    totalCount: data?.consent_profiles_aggregate?.aggregate?.count || 0,
    loading,
    error,
    loadMore,
  };
} 