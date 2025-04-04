'use client';

import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Breadcrumb } from '@/components/layout/Breadcrumb';
import { useProjectInfo } from '@/hooks/useProjectInfo';
import { Skeleton } from '@/components/ui/skeleton';
// Import the new sections
import { ProjectCardsSection } from '@/components/projects/details/ProjectCardsSection';
import { ProjectConsentProfilesSection } from '@/components/projects/details/ProjectConsentProfilesSection';

export default function ProjectDetailsPage() {
  const params = useParams();
  
  // Handle case where params might be null
  if (!params) {
    return (
      <MainLayout>
        <div className="text-muted-foreground p-8 text-center">
          Loading project parameters...
        </div>
      </MainLayout>
    );
  }
  
  const projectId = params.id as string;
  
  const { projectInfo, loading: projectInfoLoading, error: projectInfoError } = useProjectInfo(projectId);
  
  const breadcrumbItems = [
    { label: 'Projects', href: '/' },
    { label: projectInfo?.project_name || 'Loading...' },
  ];
  
  if (projectInfoLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <Skeleton className="h-5 w-48" /> {/* Breadcrumb Skeleton */}
          <Skeleton className="h-10 w-64" /> {/* Title Skeleton */}
          
          {/* Updated Skeletons for Sections */}
          <div className="space-y-4">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-10 w-1/3" /> 
            <Skeleton className="h-[400px] w-full" /> 
            <div className="flex justify-between items-center">
              <Skeleton className="h-8 w-24" /> 
              <div className="flex gap-2">
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-8 w-16" />
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-10 w-1/3" />
            <div className="flex gap-4 h-[600px]">
              <Skeleton className="flex-1" />
              <Skeleton className="w-8" />
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }
  
  if (projectInfoError) {
    return (
      <MainLayout>
        <div className="text-destructive p-8 bg-destructive/10 rounded-lg border border-destructive">
          Error loading project details: {projectInfoError.message}
        </div>
      </MainLayout>
    );
  }
  
  if (!projectInfo) {
    return (
      <MainLayout>
        <div className="text-muted-foreground p-8 text-center">
          Project not found.
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-8">
        <Breadcrumb items={breadcrumbItems} />
        
        <h1 className="text-3xl font-bold">{projectInfo.project_name}</h1>
        
        {/* Render Cards Section */}
        <ProjectCardsSection projectId={projectId} />
        
        {/* Render Consent Profiles Section */}
        <ProjectConsentProfilesSection projectId={projectId} />
        
      </div>
    </MainLayout>
  );
} 