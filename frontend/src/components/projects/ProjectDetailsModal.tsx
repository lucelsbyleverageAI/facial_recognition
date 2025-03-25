'use client';

import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { FolderOpen, User, Calendar, X } from 'lucide-react';
import { format } from 'date-fns';
import Link from 'next/link';
import { ConsentProfileList } from './ConsentProfileList';
import { CardsList } from './CardsList';
import type { Project, ConsentProfile, Card as ProjectCard } from '@/types';

interface ProjectDetailsModalProps {
  project: Project;
  consentProfiles?: ConsentProfile[];
  cards?: ProjectCard[];
  onLoadMoreProfiles?: () => void;
  onLoadMoreCards?: () => void;
  totalProfilesCount?: number;
  totalCardsCount?: number;
  trigger: React.ReactNode;
}

export function ProjectDetailsModal({
  project,
  consentProfiles = [],
  cards = [],
  onLoadMoreProfiles,
  onLoadMoreCards,
  totalProfilesCount = 0,
  totalCardsCount = 0,
  trigger,
}: ProjectDetailsModalProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        {trigger}
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl overflow-y-auto max-h-[85vh]">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <FolderOpen className="h-5 w-5 text-primary/80" />
            <span className="text-xs text-muted-foreground font-mono">
              {project.project_id.substring(0, 6)}
            </span>
          </div>
          <DialogTitle className="text-2xl font-bold">{project.project_name}</DialogTitle>
          <DialogDescription className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4" />
            <span>Created {format(new Date(project.created_at), 'MMMM d, yyyy')}</span>
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-8 py-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-primary/70" />
                <h3 className="text-base font-medium">Consent Profiles</h3>
              </div>
              <span className="text-xs text-muted-foreground">
                {totalProfilesCount} total
              </span>
            </div>
            <div className="border rounded-lg p-4 bg-card/50">
              <ConsentProfileList 
                profiles={consentProfiles}
                totalCount={totalProfilesCount}
                onLoadMore={onLoadMoreProfiles}
              />
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderOpen className="h-4 w-4 text-primary/70" />
                <h3 className="text-base font-medium">Cards</h3>
              </div>
              <span className="text-xs text-muted-foreground">
                {totalCardsCount} total
              </span>
            </div>
            <div className="border rounded-lg p-4 bg-card/50">
              <CardsList 
                cards={cards}
                totalCount={totalCardsCount}
                onLoadMore={onLoadMoreCards}
              />
            </div>
          </div>
        </div>
        
        <DialogFooter className="gap-4">
          <Link href={`/projects/${project.project_id}`} className="w-full sm:w-auto">
            <Button variant="default" size="lg" className="w-full sm:w-auto">
              Select Project
            </Button>
          </Link>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 