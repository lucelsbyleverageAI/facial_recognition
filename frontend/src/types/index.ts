export interface Project {
  project_id: string;
  project_name: string;
  created_at: string;
}

export interface ConsentProfile {
  profile_id: string;
  project_id: string;
  person_name: string;
  consent_faces?: ConsentFace[];
}

export interface ConsentFace {
  consent_face_id: string;
  profile_id: string;
  face_image_path: string;
  pose_type: 'F' | 'S';
  face_embedding?: any;
  last_updated: string;
  consent_profile?: {
    person_name: string;
  };
}

export interface Card {
  card_id: string;
  project_id: string;
  card_name: string;
  description?: string;
  created_at: string;
  status: string;
}

export interface CardConfig {
  config_id: string;
  card_id: string;
  scene_sensitivity: number;
  fallback_frame_rate: number;
  use_eq: boolean;
  lut_id?: string;
  model_name: string;
  detector_backend: string;
  align: boolean;
  enforce_detection: boolean;
  distance_metric: string;
  expand_percentage: number;
  threshold?: number;
  normalization: string;
  silent: boolean;
  refresh_database: boolean;
  anti_spoofing: boolean;
  detection_confidence_threshold: number;
}

export interface WatchFolder {
  watch_folder_id: string;
  config_id: string;
  folder_path: string;
  status: 'idle' | 'active' | 'error';
}

export interface Clip {
  clip_id: string;
  card_id: string;
  watch_folder_id?: string;
  filename: string;
  path: string;
  status: string;
  error_message?: string;
}

export interface FaceMatch {
  match_id: string;
  consent_face: {
    consent_face_id: string;
    face_image_path: string;
    consent_profile: {
      person_name: string;
    };
  };
  distance: number;
}

export interface DetectedFace {
  detection_id: string;
  confidence: number;
  facial_area: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  face_matches: FaceMatch[];
}

export interface Frame {
  frame_id: string;
  clip_id: string;
  timestamp: string;
  raw_frame_image_path: string;
  processed_frame_image_path: string | null;
  status: string;
  clip: {
    clip_id: string;
    filename: string;
    status: string;
  };
  detected_faces: DetectedFace[];
  detected_faces_aggregate: {
    aggregate: {
      count: number;
    }
  };
}

export interface ScanConsentFoldersResponse {
  status: 'success' | 'error';
  projects_found: number;
  projects_created: number;
  projects_updated: number;
  consent_profiles_found: number;
  consent_profiles_created: number;
  consent_profiles_updated: number;
  consent_images_found: number;
  consent_images_created: number;
  consent_images_updated: number;
} 