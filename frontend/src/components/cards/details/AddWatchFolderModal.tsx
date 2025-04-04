'use client';

import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';

interface AddWatchFolderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddFolder: (path: string) => Promise<void>;
  isLoading: boolean;
}

export function AddWatchFolderModal({ 
  open, 
  onOpenChange, 
  onAddFolder,
  isLoading
}: AddWatchFolderModalProps) {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!folderPath.trim()) {
      setError('Please enter a folder path');
      return;
    }
    
    try {
      await onAddFolder(folderPath);
      setFolderPath('');
      setError('');
      onOpenChange(false);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An error occurred while adding the folder');
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add Watch Folder</DialogTitle>
            <DialogDescription>
              Enter the path to a folder you want to monitor for media files.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="folderPath">Folder Path</Label>
              <Input
                id="folderPath"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder="e.g., C:\Videos\Project1 or /home/user/videos"
                required
              />
              {error && <p className="text-sm text-destructive">{error}</p>}
              <p className="text-xs text-muted-foreground">
                Provide an absolute path to the folder containing your media files.
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Adding...
                </>
              ) : (
                'Add Folder'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
} 