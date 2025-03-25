'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { scanConsentFolders } from '@/lib/api';
import { Loader2, RefreshCw } from 'lucide-react';
import { CONSENT_FOLDER_PATH } from '@/lib/constants';
import type { ScanConsentFoldersResponse } from '@/types';

interface RefreshProjectsProps {
  onScanComplete?: (response: ScanConsentFoldersResponse) => void;
  size?: 'default' | 'sm' | 'lg';
  variant?: 'default' | 'outline';
}

export function RefreshProjects({ 
  onScanComplete, 
  size = 'sm',
  variant = 'outline'
}: RefreshProjectsProps) {
  const [loading, setLoading] = useState(false);
  
  const handleRefresh = async () => {
    setLoading(true);
    
    try {
      const response = await scanConsentFolders(CONSENT_FOLDER_PATH);
      onScanComplete?.(response);
    } catch (err) {
      console.error('Error scanning consent folders:', err);
      // Error is handled silently, not shown to user
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Button 
      onClick={handleRefresh} 
      disabled={loading} 
      className="gap-2"
      variant={variant}
      size={size}
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Refreshing...
        </>
      ) : (
        <>
          <RefreshCw className="h-4 w-4" />
          Refresh Projects
        </>
      )}
    </Button>
  );
} 