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
        Use the Scan/Refresh button to scan the consent folder for consent files.
      </p>
    </div>
  );
} 