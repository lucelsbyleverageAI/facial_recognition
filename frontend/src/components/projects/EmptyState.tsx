'use client';

import { FolderSearch, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { RefreshProjects } from './RefreshProjects';
import { CONSENT_FOLDER_PATH } from '@/lib/constants';
import type { ScanConsentFoldersResponse } from '@/types';

interface EmptyStateProps {
  onScanComplete?: (response: ScanConsentFoldersResponse) => void;
}

export function EmptyState({ onScanComplete }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 md:p-16 text-center bg-muted/10 transition-all hover:bg-muted/20">
      <div className="mb-6 rounded-full bg-primary/10 p-6">
        <FolderSearch className="h-12 w-12 text-primary" />
      </div>
      <h2 className="mb-3 text-2xl font-medium">No Projects Found</h2>
      <p className="mb-8 max-w-md text-muted-foreground">
        The system is configured to scan the following folder for consent files:
      </p>
      
      <div className="bg-card rounded-lg p-6 shadow-sm border w-full max-w-md">
        <h3 className="text-lg font-medium mb-4">Configured Folder Path</h3>
        <div className="bg-muted/10 p-3 rounded-md mb-6 font-mono text-sm break-all">
          {CONSENT_FOLDER_PATH}
        </div>
        <p className="text-sm text-muted-foreground mb-6">
          Use the refresh button to scan this folder for consent files.
        </p>
        <div className="flex justify-center">
          <RefreshProjects onScanComplete={onScanComplete} size="lg" variant="default" />
        </div>
      </div>
    </div>
  );
} 