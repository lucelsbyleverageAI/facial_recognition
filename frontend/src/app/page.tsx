'use client';

import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProjectsGrid } from '@/components/projects/ProjectsGrid';
import { RefreshProjects } from '@/components/projects/RefreshProjects';
import { scanConsentFolders } from '@/lib/api';
import { CONSENT_FOLDER_PATH } from '@/lib/constants';
import { ScanConsentFoldersResponse } from '@/types';
import { HardDrive, CheckCircle } from 'lucide-react';

export default function Home() {
  const [scanResult, setScanResult] = useState<ScanConsentFoldersResponse | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  
  useEffect(() => {
    const scanFolders = async () => {
      try {
        const result = await scanConsentFolders(CONSENT_FOLDER_PATH);
        handleScanComplete(result);
      } catch (err) {
        console.error('Error scanning consent folders on load:', err);
      } finally {
        setInitialLoading(false);
      }
    };

    scanFolders();
  }, []);
  
  const handleScanComplete = (result: ScanConsentFoldersResponse) => {
    setScanResult(result);
    
    // Clear the result after 10 seconds
    setTimeout(() => {
      setScanResult(null);
    }, 10000);
  };
  
  return (
    <MainLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Projects Dashboard</h1>
            <p className="text-muted-foreground">Manage your facial recognition projects and consent profiles</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground mr-2">
              Using path: <code className="text-xs bg-muted/30 p-1 rounded">{CONSENT_FOLDER_PATH}</code>
            </span>
            <RefreshProjects onScanComplete={handleScanComplete} />
          </div>
        </div>
        
        {scanResult && (
          <div className="rounded-lg bg-green-50 dark:bg-green-900/20 p-6 border border-green-200 dark:border-green-900">
            <div className="flex items-center gap-2 mb-3 text-green-700 dark:text-green-300">
              <CheckCircle className="h-5 w-5" />
              <h3 className="font-medium text-lg">Scan Completed Successfully</h3>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="bg-white dark:bg-black/20 rounded p-4">
                <div className="text-sm text-muted-foreground mb-1">Projects</div>
                <div className="flex justify-between">
                  <span className="font-medium">{scanResult.projects_found} found</span>
                  <div className="space-x-2">
                    <span className="text-green-600 dark:text-green-400">+{scanResult.projects_created}</span>
                    <span className="text-blue-600 dark:text-blue-400">↑{scanResult.projects_updated}</span>
                  </div>
                </div>
              </div>
              <div className="bg-white dark:bg-black/20 rounded p-4">
                <div className="text-sm text-muted-foreground mb-1">Consent Profiles</div>
                <div className="flex justify-between">
                  <span className="font-medium">{scanResult.consent_profiles_found} found</span>
                  <div className="space-x-2">
                    <span className="text-green-600 dark:text-green-400">+{scanResult.consent_profiles_created}</span>
                    <span className="text-blue-600 dark:text-blue-400">↑{scanResult.consent_profiles_updated}</span>
                  </div>
                </div>
              </div>
              <div className="bg-white dark:bg-black/20 rounded p-4">
                <div className="text-sm text-muted-foreground mb-1">Consent Images</div>
                <div className="flex justify-between">
                  <span className="font-medium">{scanResult.consent_images_found} found</span>
                  <div className="space-x-2">
                    <span className="text-green-600 dark:text-green-400">+{scanResult.consent_images_created}</span>
                    <span className="text-blue-600 dark:text-blue-400">↑{scanResult.consent_images_updated}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <ProjectsGrid onScanComplete={handleScanComplete} initialLoading={initialLoading} />
      </div>
    </MainLayout>
  );
}
