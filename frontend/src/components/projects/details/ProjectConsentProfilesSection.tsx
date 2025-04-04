'use client';

import React, { useState, useMemo, useCallback, useRef } from 'react';
import { VirtuosoGrid } from 'react-virtuoso';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ExpandableImage } from '@/components/ui/expandable-image';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { RefreshCw, Search, User } from 'lucide-react';
import { ConsentProfile } from '@/types';
import { useQuery } from '@apollo/client';
import { GET_CONSENT_PROFILES_BY_PROJECT } from '@/lib/graphql/queries';
import { GridComponents } from 'react-virtuoso';
import { ProfileImagesModal } from './ProfileImagesModal';

interface ProjectConsentProfilesSectionProps {
  projectId: string;
}

// Adapt useConsentProfiles hook for potential infinite loading/fetching all
const useProjectConsentProfiles = (projectId: string) => {
  // Fetch a large number initially for client-side filtering/grouping
  const { data, loading, error, refetch, fetchMore } = useQuery(GET_CONSENT_PROFILES_BY_PROJECT, {
    variables: { projectId, limit: 1000, offset: 0 }, // Fetch up to 1000 initially
    skip: !projectId,
    fetchPolicy: 'cache-and-network', // Ensure we get updates
  });

  // Basic loadMore implementation if needed later for true infinite scroll
  const loadMoreProfiles = useCallback(() => {
    if (data?.consent_profiles?.length < (data?.consent_profiles_aggregate?.aggregate?.count || 0)) {
      fetchMore({
        variables: {
          offset: data.consent_profiles.length,
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
  }, [data, fetchMore]);

  return {
    profiles: (data?.consent_profiles as ConsentProfile[]) || [],
    totalCount: data?.consent_profiles_aggregate?.aggregate?.count || 0,
    loading,
    error,
    refetch,
    loadMoreProfiles, // Expose loadMore if we implement infinite scroll later
  };
};

// Typed List component for VirtuosoGrid
const GridList: GridComponents['List'] = React.forwardRef(({ style, children, ...props }, ref) => (
  <div
    ref={ref}
    {...props}
    style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
      gap: '1rem',
      padding: '1rem',
      border: '1px solid hsl(var(--border))', // Add border directly
      borderRadius: 'var(--radius)', // Use theme radius
      ...style,
    }}
  >
    {children}
  </div>
));
GridList.displayName = 'GridList'; // Add display name

// Typed Item component for VirtuosoGrid
const GridItem: GridComponents['Item'] = ({ children, ...props }) => (
  <div {...props}>{children}</div>
);

export function ProjectConsentProfilesSection({ projectId }: ProjectConsentProfilesSectionProps) {
  const { profiles, loading, error, refetch } = useProjectConsentProfiles(projectId);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter profiles based on search term
  const filteredProfiles = useMemo(() => {
    if (!searchTerm) return profiles;
    // Ensure person_name exists before filtering
    return profiles.filter(profile => 
      profile.person_name && profile.person_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [profiles, searchTerm]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" /> {/* Title */}
          <Skeleton className="h-8 w-8 rounded-full" /> {/* Refresh button */}
        </div>
        <Skeleton className="h-10 w-1/3" /> {/* Search input */}
        {/* Updated Skeleton - just the grid */}
        <Skeleton className="h-[600px] w-full" /> 
      </div>
    );
  }

  if (error) {
    return <div className="text-destructive">Error loading consent profiles: {error.message}</div>;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Consent Profiles</h2>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" onClick={() => refetch()} disabled={loading}>
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Refresh Profiles</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      
      {/* Search Input */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Filter by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Grid container */}
      <div style={{ height: '600px' }}> {/* Set a fixed height for Virtuoso */}
        {filteredProfiles.length === 0 && !loading ? (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground border rounded-lg bg-muted/20">
            <User className="h-12 w-12 mb-4" />
            <p>No consent profiles found{searchTerm ? ' matching your search' : ' for this project'}.</p>
          </div>
        ) : (
          <VirtuosoGrid
            style={{ height: '100%' }} // Use height 100% of the container
            totalCount={filteredProfiles.length}
            overscan={200} // Adjust overscan as needed
            components={{
              List: GridList, // Use typed component
              Item: GridItem, // Use typed component
            }}
            itemContent={(index) => {
              const profile = filteredProfiles[index];
              if (!profile) return null;
              
              // Thumbnail selection logic
              let bestFace = profile.consent_faces?.[0]; // Default to first face
              const frontalFace = profile.consent_faces?.find(face => face.pose_type === 'F');
              if (frontalFace) {
                bestFace = frontalFace;
              }

              // Wrap the item content with the modal trigger
              return (
                <ProfileImagesModal 
                  key={profile.profile_id} 
                  profile={profile} 
                  trigger={
                    <div className="flex flex-col items-center space-y-1 text-center cursor-pointer group">
                      <ExpandableImage
                        src={bestFace?.face_image_path || ''}
                        alt={profile.person_name || 'Unknown Profile'}
                        width={80}
                        height={80}
                        className="rounded-lg border group-hover:ring-2 group-hover:ring-primary transition-all"
                        isTriggerOnly={true} // Prevent double dialog
                      />
                      <span className="text-xs font-medium truncate w-full px-1 group-hover:text-primary transition-colors">
                        {profile.person_name || 'Unnamed Profile'}
                      </span>
                    </div>
                  }
                />
              );
            }}
          />
        )}
      </div>
    </div>
  );
} 