-- Drop existing tables if they exist
DROP TABLE IF EXISTS face_matches CASCADE;
DROP TABLE IF EXISTS detected_faces CASCADE;
DROP TABLE IF EXISTS frames CASCADE;
DROP TABLE IF EXISTS clips CASCADE;
DROP TABLE IF EXISTS watch_folders CASCADE;
DROP TABLE IF EXISTS card_configs CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS consent_faces CASCADE;
DROP TABLE IF EXISTS consent_profiles CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS processing_tasks CASCADE;
DROP TABLE IF EXISTS processing_tasks CASCADE;

-- Create projects table
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create consent_profiles table
CREATE TABLE consent_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    person_name TEXT NOT NULL
);

-- Create consent_faces table
CREATE TABLE consent_faces (
    consent_face_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES consent_profiles(profile_id) ON DELETE CASCADE,
    face_image_path TEXT NOT NULL,
    pose_type TEXT CHECK (pose_type IN ('F', 'S')),
    face_embedding JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_face_image_path UNIQUE (face_image_path)
);

-- Create cards table
CREATE TABLE cards (
    card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    card_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT CHECK (status IN ('pending', 'paused', 'generating_embeddings', 'processing', 'complete', 'error'))
);

-- Create card_configs table
CREATE TABLE card_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    scene_sensitivity NUMERIC DEFAULT 0.2 CHECK (scene_sensitivity >= 0 AND scene_sensitivity <= 1),
    fallback_frame_rate INTEGER DEFAULT 6 CHECK (fallback_frame_rate > 0),
    use_eq BOOLEAN DEFAULT TRUE,
    lut_file TEXT CHECK (
        lut_file IS NULL OR 
        lut_file IN ('From_SLog2SGamut_To_Cine+709.cube', 
                     'From_SLog2SGamut_To_LC-709_.cube', 
                     'From_SLog2SGamut_To_LC-709TypeA.cube', 
                     'From_SLog2SGamut_To_SLog2-709_.cube', 
                     '1_SGamut3CineSLog3_To_LC-709.cube', 
                     '2_SGamut3CineSLog3_To_LC-709TypeA.cube', 
                     '3_SGamut3CineSLog3_To_SLog2-709.cube', 
                     '4_SGamut3CineSLog3_To_Cine+709.cube')
    ),
    model_name TEXT DEFAULT 'Facenet512' CHECK (model_name IN ('VGG-Face', 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 'DeepID', 'Dlib', 'ArcFace', 'SFace', 'GhostFaceNet')),
    detector_backend TEXT DEFAULT 'retinaface' CHECK (detector_backend IN ('opencv', 'retinaface', 'mtcnn', 'ssd', 'dlib', 'mediapipe', 'yolov8', 'yolov11n', 'yolov11s', 'yolov11m', 'centerface', 'skip')),
    align BOOLEAN DEFAULT FALSE,
    enforce_detection BOOLEAN DEFAULT FALSE,
    distance_metric TEXT DEFAULT 'euclidean_l2' CHECK (distance_metric IN ('cosine', 'euclidean', 'euclidean_l2')),
    expand_percentage NUMERIC DEFAULT 0.0 CHECK (expand_percentage >= 0),
    threshold NUMERIC CHECK (threshold IS NULL OR (threshold >= 0 AND threshold <= 1)),
    normalization TEXT DEFAULT 'base' CHECK (normalization IN ('base', 'raw', 'Facenet', 'Facenet2018', 'VGGFace', 'VGGFace2', 'ArcFace')),
    silent BOOLEAN DEFAULT TRUE,
    refresh_database BOOLEAN DEFAULT TRUE,
    anti_spoofing BOOLEAN DEFAULT FALSE,
    detection_confidence_threshold NUMERIC DEFAULT 0.5 CHECK (detection_confidence_threshold >= 0 AND detection_confidence_threshold <= 1),
    CONSTRAINT video_config_card_id_key UNIQUE (card_id),
    CONSTRAINT eq_lut_constraint CHECK ((use_eq = TRUE AND lut_file IS NULL) OR (use_eq = FALSE AND lut_file IS NOT NULL))
);

-- Create watch_folders table (now associated with card_config)
CREATE TABLE watch_folders (
    watch_folder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES card_configs(config_id) ON DELETE CASCADE,
    folder_path TEXT NOT NULL,
    status TEXT DEFAULT 'idle' CHECK (status IN ('idle', 'scanned', 'active', 'error')),
    CONSTRAINT watch_folder_config_id_key UNIQUE (config_id, folder_path)
);

-- Create clips table
CREATE TABLE clips (
    clip_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    watch_folder_id UUID REFERENCES watch_folders(watch_folder_id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'unselected', 'queued', 'extracting_frames', 'extraction_complete', 'processing_complete', 'error')),
    error_message TEXT,
    CONSTRAINT unique_card_filename UNIQUE (card_id, filename)
);

-- Create frame table
CREATE TABLE frames (
    frame_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID NOT NULL REFERENCES clips(clip_id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL, -- Timecode format HH:MM:SS:FF
    raw_frame_image_path TEXT NOT NULL,
    processed_frame_image_path TEXT,
    status TEXT CHECK (status IN ('queued', 'detecting_faces', 'detection_complete', 'recognition_complete', 'error'))
);

-- Create detected_face table
CREATE TABLE detected_faces (
    detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    frame_id UUID NOT NULL REFERENCES frames(frame_id) ON DELETE CASCADE,
    confidence DOUBLE PRECISION CHECK (confidence >= 0 AND confidence <= 1),
    facial_area JSONB NOT NULL,
    face_embeddings JSONB,
    status TEXT CHECK (status IN ('queued', 'matching_faces', 'matching_complete', 'error'))
);

-- Create face_match table
CREATE TABLE face_matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id UUID NOT NULL REFERENCES detected_faces(detection_id) ON DELETE CASCADE,
    consent_face_id UUID NOT NULL REFERENCES consent_faces(consent_face_id) ON DELETE CASCADE,
    distance NUMERIC NOT NULL,
    threshold NUMERIC NOT NULL,
    target_x INTEGER NOT NULL,
    target_y INTEGER NOT NULL,
    target_w INTEGER NOT NULL,
    target_h INTEGER NOT NULL,
    source_x INTEGER NOT NULL,
    source_y INTEGER NOT NULL,
    source_w INTEGER NOT NULL,
    source_h INTEGER NOT NULL
);

-- Create processing_tasks table
CREATE TABLE processing_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'generating_embeddings', 'extracting_frames', 'processing_clips', 'complete', 'error', 'cancelling', 'cancelled')) DEFAULT 'pending',
    stage TEXT,
    progress NUMERIC CHECK (progress >= 0 AND progress <= 1) DEFAULT 0,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_card_project_id ON cards(project_id);
CREATE INDEX idx_card_config_card_id ON card_configs(card_id);
CREATE INDEX idx_watch_folder_config_id ON watch_folders(config_id);
CREATE INDEX idx_clip_card_id ON clips(card_id);
CREATE INDEX idx_clip_watch_folder_id ON clips(watch_folder_id);
CREATE INDEX idx_frame_clip_id ON frames(clip_id);
CREATE INDEX idx_detected_face_frame_id ON detected_faces(frame_id);
CREATE INDEX idx_face_match_detection_id ON face_matches(detection_id);
CREATE INDEX idx_face_match_consent_face_id ON face_matches(consent_face_id);
CREATE INDEX idx_consent_face_profile_id ON consent_faces(profile_id);
CREATE INDEX idx_consent_profile_project_id ON consent_profiles(project_id);
CREATE INDEX idx_processing_tasks_card_id ON processing_tasks(card_id);
CREATE INDEX idx_processing_tasks_status ON processing_tasks(status);

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS create_default_card_config() CASCADE;

-- Create a function to insert a default card config when a new card is added
CREATE FUNCTION create_default_card_config() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO card_configs (
        config_id, card_id, scene_sensitivity, fallback_frame_rate, use_eq, lut_file,
        model_name, detector_backend, align, enforce_detection, distance_metric, 
        expand_percentage, threshold, normalization, silent, refresh_database, 
        anti_spoofing, detection_confidence_threshold
    )
    VALUES (
        gen_random_uuid(), NEW.card_id, 
        0.2, 6, TRUE, NULL,  -- Default values with use_eq=TRUE and lut_file=NULL
        'Facenet512', 'retinaface', FALSE, FALSE, 'euclidean_l2', 
        0.0, NULL, 'base', TRUE, TRUE, 
        FALSE, 0.5
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if it already exists
DROP TRIGGER IF EXISTS trigger_create_card_config ON cards;

-- Create a trigger that calls the function after inserting a new card
CREATE TRIGGER trigger_create_card_config
AFTER INSERT ON cards
FOR EACH ROW EXECUTE FUNCTION create_default_card_config();

