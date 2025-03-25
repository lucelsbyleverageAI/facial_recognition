'use client';

import { ProjectCard } from './ProjectCard';
import { Skeleton } from '@/components/ui/skeleton';
import { EmptyState } from './EmptyState';
import { useProjects } from '@/hooks/useProjects';
import { useConsentProfiles } from '@/hooks/useConsentProfiles';
import { useCards } from '@/hooks/useCards';
import type { Project, ScanConsentFoldersResponse } from '@/types';

interface ProjectsGridProps {
  onScanComplete?: (response: ScanConsentFoldersResponse) => void;
  initialLoading?: boolean;
}

export function ProjectsGrid({ onScanComplete, initialLoading = false }: ProjectsGridProps) {
  const { projects, loading: projectsLoading, error, refetch } = useProjects();
  
  // If either initialLoading or projectsLoading is true, show loading state
  const loading = initialLoading || projectsLoading;
  
  if (loading) {
    return (
      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-4">
            <div className="space-y-3">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-7 w-4/5" />
              <Skeleton className="h-4 w-1/2" />
              <div className="pt-4 grid grid-cols-2 gap-2">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
              <div className="pt-4 flex justify-between">
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-8 w-24" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  if (error) {
    return <div className="text-destructive p-8 bg-destructive/10 rounded-lg border border-destructive">Error loading projects: {error.message}</div>;
  }
  
  if (projects.length === 0) {
    return <EmptyState onScanComplete={(response) => {
      onScanComplete?.(response);
      refetch();
    }} />;
  }
  
  return (
    <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <ProjectCardWithData 
          key={project.project_id} 
          project={project}
        />
      ))}
    </div>
  );
}

interface ProjectCardWithDataProps {
  project: Project;
}

function ProjectCardWithData({ project }: ProjectCardWithDataProps) {
  // Fetch related data for all cards since we need the counts
  const { consentProfiles, totalCount: totalProfilesCount, loadMore: loadMoreProfiles } = 
    useConsentProfiles(project.project_id);
    
  const { cards, totalCount: totalCardsCount, loadMore: loadMoreCards } = 
    useCards(project.project_id);
  
  return (
    <ProjectCard 
      project={project}
      consentProfiles={consentProfiles}
      cards={cards}
      onLoadMoreProfiles={loadMoreProfiles}
      onLoadMoreCards={loadMoreCards}
      totalProfilesCount={totalProfilesCount}
      totalCardsCount={totalCardsCount}
    />
  );
} 