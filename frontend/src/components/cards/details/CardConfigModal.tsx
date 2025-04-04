'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { type CardConfig, type CardConfigInput } from '@/hooks/useCardConfig';
import { Loader2 } from 'lucide-react';

interface CardConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: CardConfig | null;
  onSave: (configId: string, updates: Partial<CardConfigInput>) => Promise<any>;
  isLoading?: boolean;
}

// Define allowed values based on SQL constraints
const MODEL_OPTIONS = [
  'VGG-Face', 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 
  'DeepID', 'Dlib', 'ArcFace', 'SFace', 'GhostFaceNet'
];

const DETECTOR_OPTIONS = [
  'opencv', 'retinaface', 'mtcnn', 'ssd', 'dlib', 'mediapipe', 
  'yolov8', 'yolov11n', 'yolov11s', 'yolov11m', 'centerface', 'skip'
];

const DISTANCE_METRIC_OPTIONS = ['cosine', 'euclidean', 'euclidean_l2'];

const NORMALIZATION_OPTIONS = [
  'base', 'raw', 'Facenet', 'Facenet2018', 'VGGFace', 'VGGFace2', 'ArcFace'
];

const LUT_FILE_OPTIONS = [
  'From_SLog2SGamut_To_Cine+709.cube',
  'From_SLog2SGamut_To_LC-709_.cube',
  'From_SLog2SGamut_To_LC-709TypeA.cube',
  'From_SLog2SGamut_To_SLog2-709_.cube',
  '1_SGamut3CineSLog3_To_LC-709.cube',
  '2_SGamut3CineSLog3_To_LC-709TypeA.cube',
  '3_SGamut3CineSLog3_To_SLog2-709.cube',
  '4_SGamut3CineSLog3_To_Cine+709.cube'
];

export function CardConfigModal({ 
  open, 
  onOpenChange, 
  config, 
  onSave,
  isLoading = false
}: CardConfigModalProps) {
  // Create a state to track form values
  const [formValues, setFormValues] = useState<Partial<CardConfigInput>>({});
  const [activeTab, setActiveTab] = useState('model');
  const [validationError, setValidationError] = useState<string | null>(null);
  
  // Initialize form values when config changes
  useEffect(() => {
    if (config) {
      // Create a copy without the fields we don't want to edit directly
      const { config_id, watch_folders, __typename, ...configValues } = config as any;
      setFormValues(configValues);
    }
  }, [config]);
  
  // Handlers for different input types
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    
    // Convert numeric values
    if (type === 'number') {
      setFormValues({ ...formValues, [name]: parseFloat(value) });
    } else {
      setFormValues({ ...formValues, [name]: value });
    }
  };
  
  const handleSelectChange = (name: string, value: string) => {
    setFormValues({ ...formValues, [name]: value });
  };
  
  const handleSwitchChange = (name: string, checked: boolean) => {
    // Special handling for use_eq toggle
    if (name === 'use_eq') {
      if (checked) {
        // If turning on EQ, remove LUT file
        const { lut_file, ...rest } = formValues;
        setFormValues({ ...rest, [name]: checked, lut_file: null });
      } else {
        // If turning off EQ, keep other values but update the switch
        setFormValues({ ...formValues, [name]: checked });
      }
    } else {
      // Normal handling for other switches
      setFormValues({ ...formValues, [name]: checked });
    }
  };
  
  const handleSave = async () => {
    // Validate the form before saving
    if (!formValues.use_eq && !formValues.lut_file) {
      setValidationError("You must select a LUT file when Histogram Equalization is turned off");
      return;
    }
    
    setValidationError(null);
    
    if (config?.config_id) {
      await onSave(config.config_id, formValues);
      onOpenChange(false);
    }
  };
  
  // If no config yet, don't render the form
  if (!config) return null;
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Card Processing Configuration</DialogTitle>
          <DialogDescription>
            Configure the processing settings for this card. Changes will apply to all future processing.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-2 mb-4">
              <TabsTrigger value="model">Model & Detection</TabsTrigger>
              <TabsTrigger value="processing">Processing</TabsTrigger>
            </TabsList>
            
            {/* Model & Detection Tab */}
            <TabsContent value="model" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="model_name">Face Recognition Model</Label>
                  <Select 
                    value={formValues.model_name}
                    onValueChange={(value) => handleSelectChange('model_name', value)}
                  >
                    <SelectTrigger id="model_name">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {MODEL_OPTIONS.map(option => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">The model to use for face recognition</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="detector_backend">Face Detector</Label>
                  <Select 
                    value={formValues.detector_backend}
                    onValueChange={(value) => handleSelectChange('detector_backend', value)}
                  >
                    <SelectTrigger id="detector_backend">
                      <SelectValue placeholder="Select detector" />
                    </SelectTrigger>
                    <SelectContent>
                      {DETECTOR_OPTIONS.map(option => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">The backend to use for detecting faces</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="distance_metric">Distance Metric</Label>
                  <Select 
                    value={formValues.distance_metric}
                    onValueChange={(value) => handleSelectChange('distance_metric', value)}
                  >
                    <SelectTrigger id="distance_metric">
                      <SelectValue placeholder="Select metric" />
                    </SelectTrigger>
                    <SelectContent>
                      {DISTANCE_METRIC_OPTIONS.map(option => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">The metric to calculate face similarity</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="normalization">Normalization</Label>
                  <Select 
                    value={formValues.normalization}
                    onValueChange={(value) => handleSelectChange('normalization', value)}
                  >
                    <SelectTrigger id="normalization">
                      <SelectValue placeholder="Select normalization" />
                    </SelectTrigger>
                    <SelectContent>
                      {NORMALIZATION_OPTIONS.map(option => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">The normalization technique for face embedding</p>
                </div>
              </div>
            </TabsContent>
            
            {/* Processing Tab */}
            <TabsContent value="processing" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fallback_frame_rate">Fallback Frame Rate (fps)</Label>
                  <Input 
                    id="fallback_frame_rate" 
                    name="fallback_frame_rate"
                    type="number" 
                    min={1}
                    value={formValues.fallback_frame_rate || 6}
                    onChange={handleInputChange}
                  />
                  <p className="text-xs text-muted-foreground">Frame rate to use when not specified in video</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="scene_sensitivity">Scene Sensitivity</Label>
                  <Input 
                    id="scene_sensitivity" 
                    name="scene_sensitivity"
                    type="number" 
                    min={0}
                    max={1}
                    step={0.1}
                    value={formValues.scene_sensitivity || 0.2}
                    onChange={handleInputChange}
                  />
                  <p className="text-xs text-muted-foreground">
                    Higher values detect more scene changes (0-1)
                  </p>
                </div>
                
                <div className="space-y-4">
                  <Label className="block mb-2">Image Processing</Label>
                  <div className="flex items-center space-x-2">
                    <Switch 
                      id="use_eq" 
                      checked={formValues.use_eq || false}
                      onCheckedChange={(checked) => handleSwitchChange('use_eq', checked)}
                    />
                    <Label htmlFor="use_eq" className="text-sm font-normal">Use Histogram Equalization</Label>
                  </div>
                  
                  {/* Conditional LUT file selection */}
                  {formValues.use_eq === false && (
                    <div className="space-y-2 mt-4">
                      <Label htmlFor="lut_file">LUT File</Label>
                      <Select 
                        value={formValues.lut_file || ""}
                        onValueChange={(value) => handleSelectChange('lut_file', value)}
                      >
                        <SelectTrigger id="lut_file">
                          <SelectValue placeholder="Select LUT file" />
                        </SelectTrigger>
                        <SelectContent>
                          {LUT_FILE_OPTIONS.map(option => (
                            <SelectItem key={option} value={option}>{option}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">The Look-Up Table file to use for color correction</p>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
        
        {validationError && (
          <div className="text-destructive text-sm mb-4">{validationError}</div>
        )}
        
        <DialogFooter className="gap-2">
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>Save Configuration</>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 