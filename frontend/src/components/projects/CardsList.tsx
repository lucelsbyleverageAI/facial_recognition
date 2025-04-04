'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { CreditCard, Copy, Check } from 'lucide-react';
import type { Card } from '@/types';
import { formatStatus } from '@/lib/utils';

interface CardsListProps {
  cards: Card[];
  totalCount: number;
  onLoadMore?: () => void;
  loading?: boolean;
}

export function CardsList({
  cards,
  totalCount,
  onLoadMore,
  loading = false,
}: CardsListProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  const copyToClipboard = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000); // Reset after 2 seconds
  };
  
  const getStatusColor = (status: Card['status']) => {
    switch (status) {
      case 'complete':
        return 'bg-green-500';
      case 'processing':
      case 'generating_embeddings':
        return 'bg-blue-500';
      case 'paused':
        return 'bg-amber-500';
      default:
        return 'bg-gray-400';
    }
  };
  
  const getStatusText = (status: Card['status']) => {
    return formatStatus(status);
  };
  
  const getBadgeVariant = (status: Card['status']) => {
    switch (status) {
      case 'complete':
        return 'default';
      case 'processing':
      case 'generating_embeddings':
        return 'secondary';
      case 'paused':
        return 'outline';
      default:
        return 'secondary';
    }
  };
  
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between p-3 border rounded-md">
            <div className="space-y-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-16" />
            </div>
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        ))}
      </div>
    );
  }
  
  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center">
        <CreditCard className="h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm text-muted-foreground">No cards found</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-3">
      {cards.map((card) => (
        <div key={card.card_id} className="flex items-center justify-between p-3 border rounded-md hover:bg-muted/50 transition-colors">
          <div>
            <div className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${getStatusColor(card.status)}`} />
              <span className="text-sm font-medium">{card.card_name}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Created {format(new Date(card.created_at), 'MMM d, yyyy')}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs font-mono">
                    {card.card_id.substring(0, 6)}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-mono">{card.card_id}</p>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-4 w-4 rounded-full"
                      onClick={() => copyToClipboard(card.card_id)}
                    >
                      {copiedId === card.card_id ? (
                        <Check className="h-3 w-3 text-green-500" />
                      ) : (
                        <Copy className="h-3 w-3 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Badge variant={getBadgeVariant(card.status)} className="text-xs">
              {getStatusText(card.status)}
            </Badge>
          </div>
        </div>
      ))}
      
      {cards.length < totalCount && (
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onLoadMore}
          className="mt-2 w-full text-xs"
        >
          Show More ({cards.length} of {totalCount})
        </Button>
      )}
    </div>
  );
} 