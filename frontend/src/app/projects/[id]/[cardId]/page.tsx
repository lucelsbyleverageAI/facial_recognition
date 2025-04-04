'use client';

import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Skeleton } from '@/components/ui/skeleton';
import { Breadcrumb } from '@/components/layout/Breadcrumb';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useCardInfo } from '@/hooks/useCardInfo';
import ProcessingDashboardTab from '@/components/cards/details/ProcessingDashboardTab';
import ResultsTab from '@/components/cards/details/ResultsTab';

export default function CardDetailsPage() {
  const params = useParams();

  if (!params) {
    return (
      <MainLayout>
        <div className="text-muted-foreground p-8 text-center">
          Loading card parameters...
        </div>
      </MainLayout>
    );
  }

  // Extract both projectId and cardId
  const projectId = params.id as string; // Using params.id instead of params.projectId
  const cardId = params.cardId as string;

  const { projectInfo, cardInfo, loading, error } = useCardInfo(projectId, cardId);

  const breadcrumbItems = [
    { label: 'Projects', href: '/' },
    { label: projectInfo?.project_name || '...', href: `/projects/${projectId}` },
    { label: cardInfo?.card_name || '...' },
  ];

  if (loading) {
     return (
      <MainLayout>
        <div className="space-y-6">
          <Skeleton className="h-5 w-64" /> {/* Breadcrumb Skeleton */}
          <div className="flex gap-2 border-b">
             <Skeleton className="h-10 w-48" /> {/* Tab 1 Skeleton */}
             <Skeleton className="h-10 w-32" /> {/* Tab 2 Skeleton */}
          </div>
          <Skeleton className="h-[600px] w-full" /> {/* Tab Content Skeleton */}
        </div>
      </MainLayout>
    );
  }
  
  if (error) {
    return (
      <MainLayout>
         <Breadcrumb items={breadcrumbItems} />
         <div className="mt-6 text-destructive p-8 bg-destructive/10 rounded-lg border border-destructive">
          Error loading card details: {error.message}
        </div>
      </MainLayout>
    );
  }
  
  if (!projectInfo || !cardInfo) {
     return (
      <MainLayout>
        <Breadcrumb items={breadcrumbItems} />
        <div className="mt-6 text-muted-foreground p-8 text-center">
          Card or Project not found.
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <Breadcrumb items={breadcrumbItems} />
        
        <Tabs defaultValue="processing" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="processing">Processing Dashboard</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
          </TabsList>
          <TabsContent value="processing" className="mt-6">
            <ProcessingDashboardTab projectId={projectId} cardId={cardId} />
          </TabsContent>
          <TabsContent value="results" className="mt-6">
            <ResultsTab projectId={projectId} cardId={cardId} />
          </TabsContent>
        </Tabs>
        
      </div>
    </MainLayout>
  );
} 