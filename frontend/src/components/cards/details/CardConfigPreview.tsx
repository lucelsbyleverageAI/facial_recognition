'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Settings } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { type CardConfig } from '@/hooks/useCardConfig';

interface CardConfigPreviewProps {
  config: CardConfig | null;
  loading: boolean;
  onEditConfig: () => void;
}

export function CardConfigPreview({ config, loading, onEditConfig }: CardConfigPreviewProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-md font-medium">Processing Configuration</CardTitle>
          <Skeleton className="h-8 w-8 rounded-md" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!config) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-md font-medium">Processing Configuration</CardTitle>
          <Button variant="outline" size="sm" onClick={onEditConfig}>
            <Settings className="h-4 w-4 mr-1" />
            Edit Config
          </Button>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No configuration found. Click Edit to create one.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-md font-medium">Processing Configuration</CardTitle>
        <Button variant="outline" size="sm" onClick={onEditConfig}>
          <Settings className="h-4 w-4 mr-1" />
          Edit Config
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div>
              <span className="text-muted-foreground">Model:</span>{' '}
              <Badge variant="outline">{config.model_name}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Detector:</span>{' '}
              <Badge variant="outline">{config.detector_backend}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Distance Metric:</span>{' '}
              <Badge variant="outline">{config.distance_metric}</Badge>
            </div>
          </div>
          <div className="space-y-2">
            <div>
              <span className="text-muted-foreground">Frame Rate:</span>{' '}
              <span>{config.fallback_frame_rate} fps</span>
            </div>
            <div>
              <span className="text-muted-foreground">Scene Sensitivity:</span>{' '}
              <span>{config.scene_sensitivity}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Normalization:</span>{' '}
              <span>{config.normalization}</span>
            </div>
            {config.use_eq ? (
              <div>
                <Badge>Histogram EQ</Badge>
              </div>
            ) : (
              <div>
                <span className="text-muted-foreground">LUT File:</span>{' '}
                <Badge variant="outline">{config.lut_file}</Badge>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}