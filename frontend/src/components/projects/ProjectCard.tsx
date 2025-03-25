'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { FolderOpen, Calendar, Copy, Check, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ProjectDetailsModal } from './ProjectDetailsModal';
import type { Project, ConsentProfile, Card as ProjectCard } from '@/types';

interface ProjectCardProps {
  project: Project;
  consentProfiles?: ConsentProfile[];
  cards?: ProjectCard[];
  onLoadMoreProfiles?: () => void;
  onLoadMoreCards?: () => void;
  totalProfilesCount?: number;
  totalCardsCount?: number;
}

export function ProjectCard({
  project,
  consentProfiles = [],
  cards = [],
  onLoadMoreProfiles,
  onLoadMoreCards,
  totalProfilesCount = 0,
  totalCardsCount = 0,
}: ProjectCardProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  const copyToClipboard = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000); // Reset after 2 seconds
  };
  
  return (
    <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg group border border-muted-foreground/10 hover:border-primary/20">
      <CardHeader className="bg-muted/5 group-hover:bg-muted/10 transition-colors p-4">
        <div className="flex items-center gap-2 mb-2">
          <FolderOpen className="h-5 w-5 text-primary/80" />
          <div className="flex items-center">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs font-mono">
                    {project.project_id.substring(0, 6)}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-mono">{project.project_id}</p>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-4 w-4 rounded-full"
                      onClick={() => copyToClipboard(project.project_id)}
                    >
                      {copiedId === project.project_id ? (
                        <Check className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
        <CardTitle className="text-xl font-bold">{project.project_name}</CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-4 text-sm text-muted-foreground">
          <Calendar className="h-4 w-4" />
          <span>Created {format(new Date(project.created_at), 'MMM d, yyyy')}</span>
        </div>
        
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="border rounded-lg p-3 bg-muted/5">
            <p className="text-xs text-muted-foreground mb-1">Profiles</p>
            <p className="text-lg font-medium">{totalProfilesCount}</p>
          </div>
          <div className="border rounded-lg p-3 bg-muted/5">
            <p className="text-xs text-muted-foreground mb-1">Cards</p>
            <p className="text-lg font-medium">{totalCardsCount}</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="justify-between p-4 border-t bg-muted/5 flex-wrap gap-3">
        <ProjectDetailsModal
          project={project}
          consentProfiles={consentProfiles}
          cards={cards}
          onLoadMoreProfiles={onLoadMoreProfiles}
          onLoadMoreCards={onLoadMoreCards}
          totalProfilesCount={totalProfilesCount}
          totalCardsCount={totalCardsCount}
          trigger={
            <Button 
              variant="outline" 
              size="sm"
              className="w-full sm:w-auto"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              View Details
            </Button>
          }
        />
        
        <Button 
          variant="default" 
          size="sm" 
          className="w-full sm:w-auto"
          asChild
        >
          <a href={`/projects/${project.project_id}`}>
            Select Project
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
} 