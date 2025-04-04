'use client';

import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ExpandableImage } from '@/components/ui/expandable-image';
import { ConsentProfile } from '@/types';

interface ProfileImagesModalProps {
  profile: ConsentProfile;
  trigger: React.ReactNode; // The element that opens the modal
}

export function ProfileImagesModal({ profile, trigger }: ProfileImagesModalProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        {trigger}
      </DialogTrigger>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Faces for: {profile.person_name || 'Unnamed Profile'}</DialogTitle>
        </DialogHeader>
        
        {(!profile.consent_faces || profile.consent_faces.length === 0) ? (
          <div className="py-8 text-center text-muted-foreground">
            No face images found for this profile.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 py-4">
            {profile.consent_faces.map((face) => (
              <div key={face.consent_face_id} className="flex flex-col items-center space-y-1">
                <ExpandableImage
                  src={face.face_image_path}
                  alt={`${profile.person_name} - Pose ${face.pose_type}`}
                  width={150} // Larger images inside modal
                  height={150}
                  className="rounded-lg border"
                  // isTriggerOnly={false} // Default behavior - allow expansion from modal
                />
                <Badge variant={face.pose_type === 'F' ? 'default' : 'secondary'} className="text-xs">
                  Pose: {face.pose_type}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
} 