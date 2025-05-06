'use client';

import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProjectsGrid } from '@/components/projects/ProjectsGrid';
import { scanConsentFolders } from '@/lib/api';
import { CONSENT_FOLDER_PATH } from '@/lib/constants';
import { ScanConsentFoldersResponse } from '@/types';
import { HardDrive, CheckCircle, Loader2, RefreshCw } from 'lucide-react';

export default function Home() {
  const [scanResult, setScanResult] = useState<ScanConsentFoldersResponse | null>(null);
  const [initialLoading, setInitialLoading] = useState(false);
  const [useS3, setUseS3] = useState(false);
  const [folderPath, setFolderPath] = useState(CONSENT_FOLDER_PATH);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectsGridKey, setProjectsGridKey] = useState(0);

  const handleScanComplete = (result: ScanConsentFoldersResponse) => {
    setScanResult(result);
    setProjectsGridKey(prev => prev + 1);
    setTimeout(() => {
      setScanResult(null);
    }, 10000);
  };

  const handleScan = async () => {
    if (!useS3 && !folderPath) {
      setError('Please enter a folder path');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const pathToSend = useS3 ? '' : folderPath;
      const result = await scanConsentFolders(pathToSend, useS3);
      handleScanComplete(result);
    } catch (err) {
      setError('Error scanning consent folders');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleS3 = (val: boolean) => {
    setUseS3(val);
    if (val) setFolderPath('');
    else setFolderPath(CONSENT_FOLDER_PATH);
  };

  return (
    <MainLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Projects Dashboard</h1>
            <p className="text-muted-foreground">Manage your facial recognition projects and consent profiles</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  name="scanType"
                  value="local"
                  checked={!useS3}
                  onChange={() => handleToggleS3(false)}
                  disabled={loading}
                />
                <span>Local</span>
              </label>
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  name="scanType"
                  value="s3"
                  checked={useS3}
                  onChange={() => handleToggleS3(true)}
                  disabled={loading}
                />
                <span>S3</span>
              </label>
            </div>
            {!useS3 && (
              <input
                type="text"
                value={folderPath}
                onChange={e => setFolderPath(e.target.value)}
                disabled={loading}
                className="font-mono border rounded px-2 py-1"
                style={{ minWidth: 200 }}
                placeholder="e.g., C:/consent_folders"
              />
            )}
            <button
              onClick={handleScan}
              disabled={loading}
              className="btn btn-primary flex items-center gap-2 border rounded px-3 py-2 bg-primary text-white"
              style={{ minWidth: 120 }}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Scan/Refresh
                </>
              )}
            </button>
          </div>
        </div>
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            <div className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-alert-circle">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              {error}
            </div>
          </div>
        )}
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
        <ProjectsGrid key={projectsGridKey} onScanComplete={handleScanComplete} initialLoading={initialLoading} />
      </div>
    </MainLayout>
  );
}
