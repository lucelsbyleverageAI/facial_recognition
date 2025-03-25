'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { scanConsentFolders } from '@/lib/api';
import { Loader2, FolderSearch } from 'lucide-react';
import type { ScanConsentFoldersResponse } from '@/types';
import { ChangeEvent } from 'react';

interface ScanConsentFoldersProps {
  onScanComplete?: (response: ScanConsentFoldersResponse) => void;
}

export function ScanConsentFolders({ onScanComplete }: ScanConsentFoldersProps) {
  const [open, setOpen] = useState(false);
  const [folderPath, setFolderPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleScan = async () => {
    if (!folderPath) {
      setError('Please enter a folder path');
      return;
    }
    
    setError(null);
    setLoading(true);
    
    try {
      const response = await scanConsentFolders(folderPath);
      onScanComplete?.(response);
      setOpen(false);
      setFolderPath('');
    } catch (err) {
      console.error('Error scanning consent folders:', err);
      setError(err instanceof Error ? err.message : 'Failed to scan consent folders');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="flex items-center gap-2 px-6" size="lg">
          <FolderSearch className="h-5 w-5" />
          Scan Consent Folders
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Scan Consent Folders</DialogTitle>
          <DialogDescription>
            Enter the path to your consent folders to import projects and consent profiles.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-6">
          <div className="space-y-2">
            <label htmlFor="folderPath" className="text-sm font-medium">
              Consent Folder Path
            </label>
            <Input
              id="folderPath"
              value={folderPath}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setFolderPath(e.target.value)}
              placeholder="e.g., C:/consent_folders"
              disabled={loading}
              className="font-mono"
            />
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
        </div>
        
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleScan} disabled={loading} className="gap-2">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <FolderSearch className="h-4 w-4" />
                Scan Folders
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 