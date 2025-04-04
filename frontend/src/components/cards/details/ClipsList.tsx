'use client';

import React, { useState, useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Video, File, AlertCircle, ChevronDown, ChevronRight, Plus, XCircle, 
  ArrowRight, Undo, RefreshCw, Eye, Loader2, Trash2, ArrowLeft
} from 'lucide-react';
import type { Clip } from '@/hooks/useClips';
import { useMutation } from '@apollo/client';
import { UPDATE_CLIP_STATUS, DELETE_CLIP } from '@/lib/graphql/queries';
import { useToast } from '@/components/ui/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Table, 
  TableHeader, 
  TableBody, 
  TableCell, 
  TableRow,
  TableHead 
} from '@/components/ui/table';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipTrigger 
} from '@/components/ui/tooltip';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { formatStatus } from '@/lib/utils';

interface ClipsListProps {
  clips: Clip[];
  loading: boolean;
  onLoadMore?: () => void;
  totalCount: number;
  refetch?: () => Promise<any>;
}

export function ClipsList({ clips, loading, onLoadMore, totalCount, refetch }: ClipsListProps) {
  const { toast } = useToast();
  
  // State for expandable sections
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['pending', 'queued']));

  // State to track clips being updated
  const [updatingClips, setUpdatingClips] = useState<Set<string>>(new Set());

  // State for delete confirmation
  const [clipToDelete, setClipToDelete] = useState<string | null>(null);

  // GraphQL mutations
  const [updateClipStatus] = useMutation(UPDATE_CLIP_STATUS, {
    onCompleted: () => {
      if (refetch) refetch();
    }
  });

  const [deleteClip] = useMutation(DELETE_CLIP, {
    onCompleted: () => {
      if (refetch) refetch();
    }
  });

  // Toggle expanded state for a section
  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  // Update clip status
  const handleUpdateStatus = async (clipId: string, newStatus: string) => {
    setUpdatingClips(prev => new Set(prev).add(clipId));
    try {
      await updateClipStatus({
        variables: {
          clipId,
          status: newStatus
        }
      });
      
      toast({
        title: "Clip Updated",
        description: `Clip status changed to ${newStatus}`,
        duration: 2000,
      });
    } catch (error) {
      console.error('Error updating clip status:', error);
      toast({
        title: "Update Failed",
        description: error instanceof Error ? error.message : "Failed to update clip status",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setUpdatingClips(prev => {
        const next = new Set(prev);
        next.delete(clipId);
        return next;
      });
    }
  };

  // Delete clip
  const handleDeleteClip = async () => {
    if (!clipToDelete) return;
    
    setUpdatingClips(prev => new Set(prev).add(clipToDelete));
    try {
      await deleteClip({
        variables: {
          clipId: clipToDelete
        }
      });
      
      toast({
        title: "Clip Deleted",
        description: "The clip has been permanently removed",
        duration: 2000,
      });
      
      // Close the dialog
      setClipToDelete(null);
      
      // Refresh the list
      if (refetch) refetch();
    } catch (error) {
      console.error('Error deleting clip:', error);
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Failed to delete clip",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setUpdatingClips(prev => {
        const next = new Set(prev);
        next.delete(clipToDelete);
        return next;
      });
      setClipToDelete(null);
    }
  };

  const isUpdating = (clipId: string) => updatingClips.has(clipId);

  // Loading skeleton
  if (loading && clips.length === 0) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center p-2 rounded border bg-card/20">
            <Skeleton className="h-10 w-10 rounded-md mr-3" />
            <div className="space-y-1 flex-1">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-3 w-1/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (!clips || clips.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        No clips found. Use the "Scan Folder" button to find video clips.
      </div>
    );
  }

  // Group clips by status
  const groupedClips = clips.reduce((acc, clip) => {
    // Map to simplified status groups
    let statusGroup: string = clip.status;
    
    if (clip.status === 'extracting_frames' || clip.status === 'extraction_complete') {
      statusGroup = 'processing';
    } else if (clip.status === 'processing_complete') {
      statusGroup = 'completed';
    }
    
    if (!acc[statusGroup]) {
      acc[statusGroup] = [];
    }
    acc[statusGroup].push(clip);
    return acc;
  }, {} as Record<string, Clip[]>);

  // Define status order and labels
  const statusOrder = [
    { key: 'pending', label: 'Pending' },
    { key: 'queued', label: 'Queued' },
    { key: 'processing', label: 'Processing' },
    { key: 'completed', label: 'Completed' },
    { key: 'error', label: 'Error' },
    { key: 'unselected', label: 'Unselected' }
  ];

  const getStatusBadgeProps = (status: string) => {
    switch (status) {
      case 'pending':
        return { variant: 'outline' as const, className: 'bg-amber-500/10 text-amber-500', children: 'Pending' };
      case 'unselected':
        return { variant: 'outline' as const, className: 'bg-neutral-500/10 text-neutral-500', children: 'Unselected' };
      case 'queued':
        return { variant: 'outline' as const, className: 'bg-blue-500/10 text-blue-500', children: 'Queued' };
      case 'extracting_frames':
      case 'processing':
        return { variant: 'outline' as const, className: 'bg-purple-500/10 text-purple-500', children: 'Processing' };
      case 'extraction_complete':
        return { variant: 'outline' as const, className: 'bg-indigo-500/10 text-indigo-500', children: 'Extraction Complete' };
      case 'processing_complete':
      case 'completed':
        return { variant: 'outline' as const, className: 'bg-green-500/10 text-green-500', children: 'Complete' };
      case 'error':
        return { variant: 'outline' as const, className: 'bg-red-500/10 text-red-500', children: 'Error' };
      default:
        return { variant: 'outline' as const, children: status };
    }
  };

  // Get formatted status text for displaying
  const getStatusText = (status: string) => {
    return formatStatus(status);
  };

  return (
    <div className="space-y-4">
      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!clipToDelete} onOpenChange={(open) => !open && setClipToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Clip</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this clip? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteClip} className="bg-destructive hover:bg-destructive/90">
              {updatingClips.has(clipToDelete || '') ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {loading && clips.length === 0 ? (
        <div className="p-8 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : clips.length === 0 ? (
        <div className="p-8 text-center text-muted-foreground">
          No clips found. Use the "Scan Folder" button to find video clips.
        </div>
      ) : (
        <>
          {statusOrder.map(({ key: status, label }) => {
            // Skip if no clips with this status
            if (!groupedClips[status] || groupedClips[status].length === 0) {
              return null;
            }
            
            return (
              <div key={status} className="rounded-lg border shadow-sm">
                <div 
                  className="flex items-center justify-between px-4 py-3 cursor-pointer"
                  onClick={() => toggleSection(status)}
                >
                  <div className="flex items-center gap-2">
                    {expandedSections.has(status) ? (
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    )}
                    <div className="font-medium flex items-center gap-2">
                      <Badge {...getStatusBadgeProps(status as Clip['status'])}>
                        {getStatusText(status)}
                      </Badge>
                      <span className="text-muted-foreground text-sm">
                        ({groupedClips[status].length} {groupedClips[status].length === 1 ? 'clip' : 'clips'})
                      </span>
                    </div>
                  </div>
                </div>
                
                {expandedSections.has(status) && (
                  <ScrollArea className="h-[calc(100vh-400px)] border-t">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Filename</TableHead>
                          <TableHead>Folder</TableHead>
                          <TableHead className="w-[250px]">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {groupedClips[status].map((clip) => (
                          <TableRow key={clip.clip_id}>
                            <TableCell className="font-medium">
                              {clip.filename}
                            </TableCell>
                            <TableCell className="max-w-[200px] truncate">
                              {clip.watch_folder ? clip.watch_folder.folder_path : 
                                <span className="text-muted-foreground italic">
                                  (Watch folder removed)
                                </span>
                              }
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-2">
                                {/* Pending status actions */}
                                {status === 'pending' && (
                                  <>
                                    <Button 
                                      variant="outline" 
                                      size="sm"
                                      className="gap-1 bg-blue-500/10 text-blue-500 hover:bg-blue-500/20"
                                      onClick={() => handleUpdateStatus(clip.clip_id, 'queued')}
                                      disabled={isUpdating(clip.clip_id)}
                                    >
                                      {isUpdating(clip.clip_id) ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                      ) : (
                                        <ArrowRight className="h-4 w-4" />
                                      )}
                                      <span>Queue</span>
                                    </Button>
                                    <Button 
                                      variant="outline" 
                                      size="sm"
                                      className="gap-1"
                                      onClick={() => handleUpdateStatus(clip.clip_id, 'unselected')}
                                      disabled={isUpdating(clip.clip_id)}
                                    >
                                      {isUpdating(clip.clip_id) ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                      ) : (
                                        <XCircle className="h-4 w-4" />
                                      )}
                                      <span>Deselect</span>
                                    </Button>
                                  </>
                                )}

                                {/* Queued status actions */}
                                {status === 'queued' && (
                                  <>
                                    <Button 
                                      variant="outline" 
                                      size="sm"
                                      className="gap-1"
                                      onClick={() => handleUpdateStatus(clip.clip_id, 'pending')}
                                      disabled={isUpdating(clip.clip_id)}
                                    >
                                      {isUpdating(clip.clip_id) ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                      ) : (
                                        <ArrowLeft className="h-4 w-4" />
                                      )}
                                      <span>To Pending</span>
                                    </Button>
                                    <Button 
                                      variant="outline" 
                                      size="sm"
                                      className="gap-1"
                                      onClick={() => handleUpdateStatus(clip.clip_id, 'unselected')}
                                      disabled={isUpdating(clip.clip_id)}
                                    >
                                      {isUpdating(clip.clip_id) ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                      ) : (
                                        <XCircle className="h-4 w-4" />
                                      )}
                                      <span>Deselect</span>
                                    </Button>
                                  </>
                                )}

                                {/* Unselected status actions */}
                                {status === 'unselected' && (
                                  <Button 
                                    variant="outline" 
                                    size="sm"
                                    className="gap-1 bg-amber-500/10 text-amber-500 hover:bg-amber-500/20"
                                    onClick={() => handleUpdateStatus(clip.clip_id, 'pending')}
                                    disabled={isUpdating(clip.clip_id)}
                                  >
                                    {isUpdating(clip.clip_id) ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <Undo className="h-4 w-4" />
                                    )}
                                    <span>Restore</span>
                                  </Button>
                                )}

                                {/* Error status actions */}
                                {status === 'error' && clip.error_message && (
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" className="h-8 w-8">
                                        <AlertCircle className="h-4 w-4 text-destructive" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent className="max-w-xs">
                                      <p className="font-mono text-xs">{clip.error_message}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                )}

                                {/* Delete button - shown for all statuses */}
                                <Button 
                                  variant="outline" 
                                  size="sm"
                                  className="gap-1 text-destructive hover:bg-destructive/10"
                                  onClick={() => setClipToDelete(clip.clip_id)}
                                  disabled={isUpdating(clip.clip_id)}
                                >
                                  {isUpdating(clip.clip_id) ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Trash2 className="h-4 w-4" />
                                  )}
                                  <span>Delete</span>
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                )}
              </div>
            );
          })}
        </>
      )}
      
      {clips.length > 0 && totalCount > clips.length && (
        <div className="flex justify-center pt-4">
          <Button 
            variant="outline" 
            onClick={onLoadMore}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Plus className="h-4 w-4 mr-2" />
            )}
            Load More
          </Button>
        </div>
      )}
    </div>
  );
} 