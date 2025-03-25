'use client';

import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';

export default function ProjectDetailsPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  return (
    <MainLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Project Details</h1>
        <p>Project ID: {projectId}</p>
        <p>This page is under construction.</p>
      </div>
    </MainLayout>
  );
} 