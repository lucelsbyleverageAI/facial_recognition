'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FolderOpen, Play, Square, Trash2, RefreshCw, Scan, Search, Eye, EyeOff } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { useCardConfig } from '@/hooks/useCardConfig';
import { useWatchFolders } from '@/hooks/useWatchFolders';
import { useClips } from '@/hooks/useClips';
import { CardConfigPreview } from './CardConfigPreview';
import { CardConfigModal } from './CardConfigModal';
import { ClipsList } from './ClipsList';
import { AddWatchFolderModal } from './AddWatchFolderModal';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { scanWatchFolder, startWatchFolderMonitoring, stopWatchFolderMonitoring } from '@/lib/api';

interface ProcessingDashboardTabProps {
  projectId: string;
  cardId: string;
}

// Update the type definition of the watch folder status
type WatchFolderStatus = 'idle' | 'scanned' | 'active' | 'error';

export default function ProcessingDashboardTab({ projectId, cardId }: ProcessingDashboardTabProps) {
  const { toast } = useToast();
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [addFolderModalOpen, setAddFolderModalOpen] = useState(false);
  const [folderToDelete, setFolderToDelete] = useState<string | null>(null);
  const [scanningFolders, setScanningFolders] = useState<Set<string>>(new Set());
  const [monitoringFolders, setMonitoringFolders] = useState<Set<string>>(new Set());

  const { 
    cardConfig, 
    loading: configLoading, 
    updateCardConfig, 
    updating: configUpdating,
    refetch: refetchCardConfig
  } = useCardConfig(cardId);

  const {
    addFolder,
    removeFolder,
    updateFolderStatus,
    adding: addingFolder,
    removing: removingFolder,
    updating: updatingFolder
  } = useWatchFolders(cardConfig?.config_id || '', cardId);

  const {
    clips,
    totalCount: clipsCount,
    loading: clipsLoading,
    loadMore: loadMoreClips,
    refetch: refetchClips
  } = useClips(cardId);

  const handleAddFolder = async (folderPath: string) => {
    if (cardConfig?.config_id) {
      await addFolder(folderPath);
    }
  };

  const handleRemoveFolder = async () => {
    if (folderToDelete) {
      await removeFolder(folderToDelete);
      setFolderToDelete(null);
    }
  };

  const confirmRemoveFolder = (watchFolderId: string) => {
    setFolderToDelete(watchFolderId);
  };

  const handleScanFolder = async (watchFolderId: string, folderPath: string) => {
    try {
      // Add to scanning set
      setScanningFolders(prev => new Set(prev).add(watchFolderId));
      
      // Call the API
      const result = await scanWatchFolder(watchFolderId, folderPath);
      
      // Show appropriate toast based on results
      if (result.clips_found === 0) {
        toast({
          title: "No Clips Found",
          description: "No video files were found in the watch folder.",
          duration: 3000,
        });
      } else {
        let description = `Found ${result.clips_found} clips, added ${result.clips_created} new clips.`;
        
        // Add information about duplicate filenames if any
        if (result.duplicate_filenames && result.duplicate_filenames.length > 0) {
          const duplicateCount = result.duplicate_filenames.length;
          const sampleNames = result.duplicate_filenames.slice(0, 3).join(', ');
          const additionalCount = duplicateCount > 3 ? ` and ${duplicateCount - 3} more` : '';
          
          description += ` Skipped ${duplicateCount} duplicate filename${duplicateCount > 1 ? 's' : ''}: ${sampleNames}${additionalCount}.`;
        }
        
        toast({
          title: "Folder Scanned",
          description,
          duration: result.duplicate_filenames?.length ? 5000 : 3000, // Show longer for duplicates
        });
      }
      
      // Refresh data
      await refetchCardConfig();
      await refetchClips();
    } catch (error) {
      console.error('Error scanning folder:', error);
      toast({
        title: "Scan Failed",
        description: error instanceof Error ? error.message : "Failed to scan folder.",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      // Remove from scanning set
      setScanningFolders(prev => {
        const next = new Set(prev);
        next.delete(watchFolderId);
        return next;
      });
    }
  };

  // Handle starting folder monitoring
  const handleStartMonitoring = async (watchFolderId: string) => {
    try {
      console.log(`Starting monitoring for watch folder: ${watchFolderId}`);
      setMonitoringFolders(prev => new Set(prev).add(watchFolderId));
      
      // First call the actual monitoring API endpoint
      console.log(`Calling startWatchFolderMonitoring with ID: ${watchFolderId}`);
      const result = await startWatchFolderMonitoring(watchFolderId);
      console.log(`Result from startWatchFolderMonitoring:`, result);
      
      // If successful, update local status
      if (result.status === 'success') {
        // Update folder status to match what the API returned
        await updateFolderStatus(watchFolderId, 'active');
        
        toast({
          title: "Monitoring Started",
          description: "Watch folder is now being monitored for new content.",
          duration: 3000,
        });
      } else {
        throw new Error(result.message || "Failed to start monitoring");
      }
      
      // Refresh data
      await refetchCardConfig();
    } catch (error) {
      console.error('Error starting monitoring:', error);
      toast({
        title: "Monitoring Failed",
        description: error instanceof Error ? error.message : "Failed to start monitoring.",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setMonitoringFolders(prev => {
        const next = new Set(prev);
        next.delete(watchFolderId);
        return next;
      });
    }
  };

  // Handle stopping folder monitoring
  const handleStopMonitoring = async (watchFolderId: string) => {
    try {
      setMonitoringFolders(prev => new Set(prev).add(watchFolderId));
      
      // First call the actual stop monitoring API endpoint
      const result = await stopWatchFolderMonitoring(watchFolderId);
      
      // If successful, update local status
      if (result.status === 'success') {
        // Update folder status to match what the API returned
        await updateFolderStatus(watchFolderId, 'scanned');
        
        toast({
          title: "Monitoring Stopped",
          description: "Watch folder is no longer being monitored.",
          duration: 3000,
        });
      } else {
        throw new Error(result.message || "Failed to stop monitoring");
      }
      
      // Refresh data
      await refetchCardConfig();
    } catch (error) {
      console.error('Error stopping monitoring:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to stop monitoring.",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setMonitoringFolders(prev => {
        const next = new Set(prev);
        next.delete(watchFolderId);
        return next;
      });
    }
  };

  const isScanning = (watchFolderId: string) => scanningFolders.has(watchFolderId);
  const isChangingMonitorState = (watchFolderId: string) => monitoringFolders.has(watchFolderId);

  // Helper to get badge variant based on status
  const getStatusBadge = (status: WatchFolderStatus) => {
    switch (status) {
      case 'idle':
        return <Badge variant="outline" className="text-xs">Idle</Badge>;
      case 'scanned':
        return <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-500">Scanned</Badge>;
      case 'active':
        return <Badge variant="outline" className="text-xs bg-green-500/10 text-green-500">Active</Badge>;
      case 'error':
        return <Badge variant="destructive" className="text-xs">Error</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Card Configuration Preview */}
      <CardConfigPreview 
        config={cardConfig} 
        loading={configLoading} 
        onEditConfig={() => setConfigModalOpen(true)} 
      />

      {/* Card Configuration Modal */}
      <CardConfigModal 
        open={configModalOpen}
        onOpenChange={setConfigModalOpen}
        config={cardConfig}
        onSave={updateCardConfig}
        isLoading={configUpdating}
      />
      
      {/* Add Watch Folder Modal */}
      <AddWatchFolderModal
        open={addFolderModalOpen}
        onOpenChange={setAddFolderModalOpen}
        onAddFolder={handleAddFolder}
        isLoading={addingFolder}
      />

      {/* Remove Folder Confirmation */}
      <AlertDialog open={!!folderToDelete} onOpenChange={(open: boolean) => !open && setFolderToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Watch Folder</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove this watch folder? The folder will no longer be monitored for new files.
              <p className="mt-2">
                <strong>Note:</strong> Any clips that were previously added from this folder will still remain in the project.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemoveFolder} className="bg-destructive hover:bg-destructive/90">
              {removingFolder ? 'Removing...' : 'Remove'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Watch Folders Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-md font-medium">Watch Folders</CardTitle>
          <Button 
            variant="outline" 
            size="sm" 
            className="h-8 gap-1" 
            onClick={() => setAddFolderModalOpen(true)}
            disabled={!cardConfig?.config_id}
          >
            <FolderOpen className="h-4 w-4" />
            <span>Add Folder</span>
          </Button>
        </CardHeader>
        <CardContent>
          {cardConfig?.watch_folders && cardConfig.watch_folders.length > 0 ? (
            <div className="space-y-2">
              {cardConfig.watch_folders.map(folder => (
                <div 
                  key={folder.watch_folder_id} 
                  className="flex justify-between items-center p-2 rounded border bg-card/50"
                >
                  <div>
                    <p className="text-sm font-medium">{folder.folder_path}</p>
                    <div className="flex items-center">
                      <p className="text-xs text-muted-foreground mr-2">
                        Status: {folder.status.charAt(0).toUpperCase() + folder.status.slice(1)}
                      </p>
                      {getStatusBadge(folder.status as WatchFolderStatus)}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {/* Scan button - shown for idle or scanned statuses */}
                    {(folder.status === 'idle' || folder.status === 'scanned') && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="gap-1"
                        disabled={isScanning(folder.watch_folder_id)}
                        onClick={() => handleScanFolder(folder.watch_folder_id, folder.folder_path)}
                      >
                        {isScanning(folder.watch_folder_id) ? (
                          <>
                            <RefreshCw className="h-4 w-4 animate-spin" />
                            Scanning...
                          </>
                        ) : (
                          <>
                            <Search className="h-4 w-4" />
                            Scan
                          </>
                        )}
                      </Button>
                    )}
                    
                    {/* Start Monitoring button - shown only when status is scanned */}
                    {folder.status === 'scanned' && (
                      <Button 
                        variant="default" 
                        size="sm"
                        className="gap-1"
                        disabled={isChangingMonitorState(folder.watch_folder_id)}
                        onClick={() => handleStartMonitoring(folder.watch_folder_id)}
                      >
                        {isChangingMonitorState(folder.watch_folder_id) ? (
                          <>
                            <RefreshCw className="h-4 w-4 animate-spin" />
                            Starting...
                          </>
                        ) : (
                          <>
                            <Eye className="h-4 w-4" />
                            Start Monitoring
                          </>
                        )}
                      </Button>
                    )}
                    
                    {/* Stop Monitoring button - shown only when status is active */}
                    {folder.status === 'active' && (
                      <Button 
                        variant="secondary" 
                        size="sm"
                        className="gap-1"
                        disabled={isChangingMonitorState(folder.watch_folder_id)}
                        onClick={() => handleStopMonitoring(folder.watch_folder_id)}
                      >
                        {isChangingMonitorState(folder.watch_folder_id) ? (
                          <>
                            <RefreshCw className="h-4 w-4 animate-spin" />
                            Stopping...
                          </>
                        ) : (
                          <>
                            <EyeOff className="h-4 w-4" />
                            Stop Monitoring
                          </>
                        )}
                      </Button>
                    )}
                    
                    {/* Remove button - always shown */}
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="text-destructive hover:bg-destructive/10"
                      onClick={() => confirmRemoveFolder(folder.watch_folder_id)}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-4 text-center text-muted-foreground">
              No watch folders configured yet.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Clips Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-md font-medium">Clips</CardTitle>
          {clips.length > 0 && (
            <Button 
              variant="outline" 
              size="sm" 
              className="gap-1"
              onClick={() => refetchClips()}
            >
              <RefreshCw className={`h-4 w-4 ${clipsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <ClipsList 
            clips={clips} 
            loading={clipsLoading} 
            totalCount={clipsCount}
            onLoadMore={loadMoreClips}
            refetch={refetchClips}
          />
        </CardContent>
      </Card>

      {/* Processing Actions */}
      <div className="flex gap-2 justify-end">
        <Button 
          variant="default" 
          className="gap-1" 
          disabled={!cardConfig?.watch_folders?.length || clips.length === 0}
        >
          <Play className="h-4 w-4" />
          <span>Start Processing</span>
        </Button>
        <Button variant="outline" className="gap-1" disabled>
          <Square className="h-4 w-4" />
          <span>Stop Processing</span>
        </Button>
      </div>
    </div>
  );
} 