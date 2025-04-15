import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clip } from "@/types";
import { X } from "lucide-react";

interface ResultsFiltersProps {
  clips: Clip[];
  onFilterChange: (filters: { 
    clipId?: string; 
    status?: string[]; 
    resultType?: 'all' | 'detected' | 'matched' | 'unmatched' 
  }) => void;
  currentFilters: {
    clipId?: string;
    status?: string[];
    resultType?: 'all' | 'detected' | 'matched' | 'unmatched';
  };
}

export function ResultsFilters({ 
  clips, 
  onFilterChange, 
  currentFilters 
}: ResultsFiltersProps) {
  // Available status options
  const statusOptions = [
    { value: 'queued', label: 'Queued' },
    { value: 'detecting_faces', label: 'Detecting Faces' },
    { value: 'detection_complete', label: 'Detection Complete' },
    { value: 'recognition_complete', label: 'Recognition Complete' },
    { value: 'error', label: 'Error' }
  ];

  // Handle clip selection
  const handleClipChange = (clipId: string) => {
    onFilterChange({ clipId: clipId === 'all' ? undefined : clipId });
  };

  // Handle status selection
  const handleStatusChange = (status: string) => {
    const currentStatus = currentFilters.status || [];
    const newStatus = currentStatus.includes(status)
      ? currentStatus.filter(s => s !== status)
      : [...currentStatus, status];
    
    onFilterChange({ status: newStatus.length > 0 ? newStatus : undefined });
  };

  // Handle result type selection
  const handleResultTypeChange = (resultType: 'all' | 'detected' | 'matched' | 'unmatched') => {
    onFilterChange({ resultType });
  };

  // Handle clearing all filters
  const handleClearFilters = () => {
    onFilterChange({
      clipId: undefined,
      status: undefined,
      resultType: 'all'
    });
  };

  return (
    <div className="bg-card p-6 rounded-lg border space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-lg font-semibold">Filters</h2>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleClearFilters}
          className="self-start"
        >
          <X className="h-4 w-4 mr-1" /> Clear Filters
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Clip Filter */}
        <div className="space-y-2">
          <Label htmlFor="clip-filter">Clip</Label>
          <Select 
            value={currentFilters.clipId || 'all'} 
            onValueChange={handleClipChange}
          >
            <SelectTrigger id="clip-filter" className="w-full">
              <SelectValue placeholder="All Clips" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Clips</SelectItem>
              {clips.map(clip => (
                <SelectItem key={clip.clip_id} value={clip.clip_id}>
                  {clip.filename}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Status Filter */}
        <div className="space-y-2">
          <Label>Status</Label>
          <div className="flex flex-wrap gap-2">
            {statusOptions.map(status => (
              <Badge 
                key={status.value}
                variant={currentFilters.status?.includes(status.value) ? 'default' : 'outline'} 
                className="cursor-pointer"
                onClick={() => handleStatusChange(status.value)}
              >
                {status.label}
              </Badge>
            ))}
          </div>
        </div>

        {/* Result Type Filter */}
        <div className="space-y-2">
          <Label>Results</Label>
          <RadioGroup 
            value={currentFilters.resultType || 'all'} 
            onValueChange={(value: 'all' | 'detected' | 'matched' | 'unmatched') => 
              handleResultTypeChange(value)
            }
            className="flex flex-col space-y-1"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="all" id="all" />
              <Label htmlFor="all" className="cursor-pointer">All Frames</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="detected" id="detected" />
              <Label htmlFor="detected" className="cursor-pointer">Frames with Detected Faces</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="matched" id="matched" />
              <Label htmlFor="matched" className="cursor-pointer">Frames with Matched Faces</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="unmatched" id="unmatched" />
              <Label htmlFor="unmatched" className="cursor-pointer">Frames with Unmatched Faces</Label>
            </div>
          </RadioGroup>
        </div>
      </div>
    </div>
  );
} 