'use client';

import { useState } from 'react';
import Image from 'next/image';
import { 
  Dialog, 
  DialogContent, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { getImageUrl } from '@/lib/api';
import { X } from 'lucide-react';
import { Button } from './button';

// Create a VisuallyHidden component for accessibility
function VisuallyHidden({ children }: { children: React.ReactNode }) {
  return (
    <span 
      className="absolute w-[1px] h-[1px] p-0 -m-[1px] overflow-hidden clip-[rect(0,0,0,0)] whitespace-nowrap border-0"
    >
      {children}
    </span>
  );
}

interface ExpandableImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  isTriggerOnly?: boolean;
}

export function ExpandableImage({ 
  src, 
  alt, 
  width = 64, 
  height = 64, 
  className = '', 
  isTriggerOnly = false 
}: ExpandableImageProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Use the image proxy to get the URL
  const imageUrl = getImageUrl(src);
  
  // Inner content (image + overlay + skeleton)
  const imageContent = (
    <div 
      className={`relative group ${isTriggerOnly ? 'cursor-pointer' : ''} overflow-hidden rounded-md ${className}`}
      style={{ width, height }}
      // Add onClick handler only if it's NOT just a trigger, to open its own dialog
      onClick={isTriggerOnly ? undefined : () => setIsOpen(true)}
    >
      <img 
        src={imageUrl}
        alt={alt}
        width={width}
        height={height}
        className="object-cover w-full h-full transition-transform group-hover:scale-105"
        onLoad={() => setIsLoading(false)}
        onError={() => setIsLoading(false)}
      />
      <div className="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity" />
      {isLoading && (
        <Skeleton className="absolute inset-0" />
      )}
    </div>
  );
  
  // Render directly if it's only a trigger for an external modal
  if (isTriggerOnly) {
    return imageContent;
  }

  // Otherwise, wrap with its own Dialog for self-expansion
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {imageContent} 
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl max-h-[80vh] p-1">
        {/* Add DialogTitle for accessibility - visually hidden but available to screen readers */}
        <DialogTitle className="sr-only">
          {alt || "Image Preview"}
        </DialogTitle>
        
        <div className="flex justify-end p-2 absolute top-0 right-0 z-10">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => setIsOpen(false)}
            className="h-8 w-8 rounded-full bg-black/20 text-white hover:bg-black/40"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="overflow-auto p-4 h-full w-full flex items-center justify-center">
          <img 
            src={imageUrl}
            alt={alt}
            className="max-w-full max-h-[70vh] object-contain"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
} 