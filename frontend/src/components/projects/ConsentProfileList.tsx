'use client';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { UsersRound, Copy, Check } from 'lucide-react';
import { ExpandableImage } from '@/components/ui/expandable-image';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useState } from 'react';
import type { ConsentProfile } from '@/types';

interface ConsentProfileListProps {
  profiles: ConsentProfile[];
  totalCount: number;
  onLoadMore?: () => void;
  loading?: boolean;
}

export function ConsentProfileList({
  profiles,
  totalCount,
  onLoadMore,
  loading = false,
}: ConsentProfileListProps) {  
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  const copyToClipboard = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000); // Reset after 2 seconds
  };
  
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="space-y-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  if (profiles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center">
        <UsersRound className="h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm text-muted-foreground">No consent profiles found</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-3">
      {profiles.map((profile) => (
        <div key={profile.profile_id} className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors">
          <TooltipProvider>
            {profile.consent_faces && profile.consent_faces.length > 0 ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="h-10 w-10 rounded-full overflow-hidden border">
                    <ExpandableImage
                      src={profile.consent_faces[0].face_image_path}
                      alt={profile.person_name}
                      width={40}
                      height={40}
                      className="rounded-full"
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p className="text-xs">View full image</p>
                </TooltipContent>
              </Tooltip>
            ) : (
              <Avatar className="h-10 w-10 border">
                <AvatarFallback className="bg-primary/10 text-primary">
                  {profile.person_name.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            )}
          </TooltipProvider>
          
          <div className="flex-1">
            <span className="text-sm font-medium">{profile.person_name}</span>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <span>ID: {profile.profile_id.substring(0, 6)}</span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-4 w-4 rounded-full"
                      onClick={() => copyToClipboard(profile.profile_id)}
                    >
                      {copiedId === profile.profile_id ? (
                        <Check className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3 text-muted-foreground" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p className="text-xs">
                      {copiedId === profile.profile_id ? 'Copied!' : 'Copy full ID'}
                    </p>
                    {!copiedId && (
                      <p className="text-xs font-mono mt-1 text-muted-foreground">
                        {profile.profile_id}
                      </p>
                    )}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
      ))}
      
      {profiles.length < totalCount && (
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onLoadMore}
          className="mt-2 w-full text-xs"
        >
          Show More ({profiles.length} of {totalCount})
        </Button>
      )}
    </div>
  );
} 