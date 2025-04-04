# Backend API Endpoints

This document describes the key backend API endpoints for the Facial Recognition Processing Pipeline application. These endpoints handle operations that require Python processing beyond simple database queries, which will be handled through GraphQL.

## Project Discovery and Consent Profile Processing

### POST /api/scan-consent-folders
Scans the pre-defined local consent folder and synchronizes the database with discovered projects, consent profiles, and images.

**Request Body:**
```json
{
  "consent_folder_path": "/path/to/consent/folders1"
}
```

**Response:**
```json
{
  "status": "success",
  "projects_found": 5,
  "projects_created": 2,
  "projects_updated": 3,
  "consent_profiles_found": 24,
  "consent_profiles_created": 10,
  "consent_profiles_updated": 14,
  "consent_images_found": 48,
  "consent_images_created": 15,
  "consent_images_updated": 33
}
```

**Logic:**
- Goes to the specified consent folder location
- Scans subfolders for project names using the format `{projectId}_{projectName}`
- Creates or updates projects in the database
- For each project, scans subfolders for consent profiles using the format `{consentProfileId}_{consentProfileName}`
- Creates or updates consent profiles in the database
- For each consent profile, scans for images using the format `{consentImageId}_{position}` or just `{position}` if there is no consent profile id
- Creates or updates consent profile images in the database
- Returns summary statistics of the scan results

### POST /api/generate-consent-embeddings
Generates face embeddings for consent profile images that don't have them.

**Request Body:**
```json
{
  "project_id": "uuid-string",
  "config": {
    "model_name": "FACENET512",
    "detector_backend": "retinaface",
    "enforce_detection": false,
    "align": true,
    "distance_metric": "euclidean_l2",
    "expand_percentage": 0.0,
    "threshold": null,
    "normalization": "base",
    "silent": true,
    "refresh_database": true,
    "anti_spoofing": false,
    "detection_confidence_threshold": 0.5
  }
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "started",
  "total_images": 10,
  "message": "Embedding generation started"
}
```

**Logic:**
- Retrieves all consent profiles and images for the specified project
- Identifies images that don't have embeddings or have been updated
- Starts a background task to generate embeddings using DeepFace
- Stores generated embeddings in the database
- Updates a pickle file for faster future matching
- Returns a task ID for status checking with the number of images to process

## Watch Folder Management

### POST /api/scan-watch-folder
Scans a watch folder for video clips and adds them to the database.

**Request Body:**
```json
{
  "watch_folder_id": "uuid-string",
  "folder_path": "/path/to/watch/folder"
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "success",
  "clips_found": 10,
  "clips_created": 8,
  "clips_updated": 2,
  "watch_folder_path": "/path/to/watch/folder"
}
```

**Logic:**
- Retrieves the card details from the database
- Scans the specified folder for video files
- Identifies video files based on supported formats and structures
- Creates or updates clip entries in the database
- Sets clip status to "pending"
- Returns summary statistics of the scan results

### POST /api/start-watch-folder-monitoring
Starts monitoring a watch folder for new video clips.

**Request Body:**
```json
{
  "card_id": "uuid-string",
  "watch_folder_id": "uuid-string",
  "inactivity_timeout_minutes": 30
}
```

**Response:**
```json
{
  "status": "success",
  "watch_folder_id": "uuid-string",
  "monitoring_status": "watching",
  "message": "Watch folder monitoring started",
  "inactivity_timeout_minutes": 30
}
```

**Logic:**
- Updates the watch folder status to "watching" in the database
- Starts a background process to monitor the folder for new files
- When new video files are detected, creates clip entries automatically
- Sets clip status to "pending" for new clips
- After predefined inactivity period (default 30 minutes), automatically stops monitoring
- Returns confirmation of monitoring start

### POST /api/stop-watch-folder-monitoring
Stops monitoring a watch folder.

**Request Body:**
```json
{
  "watch_folder_id": "uuid-string"
}
```

**Response:**
```json
{
  "status": "success",
  "watch_folder_id": "uuid-string",
  "monitoring_status": "idle",
  "message": "Watch folder monitoring stopped"
}
```

**Logic:**
- Updates the watch folder status to "idle" in the database
- Stops the background monitoring process
- Returns confirmation of monitoring stop

## Processing Management

### POST /api/start-processing
Starts processing of queued clips.

**Request Body:**
```json
{
  "card_id": "uuid-string",
  "config": {
    "model_name": "FACENET512",
    "detector_backend": "retinaface",
    "enforce_detection": false,
    "align": true,
    "distance_metric": "euclidean_l2",
    "expand_percentage": 0.0,
    "threshold": null,
    "normalization": "base",
    "silent": true,
    "refresh_database": true,
    "anti_spoofing": false,
    "detection_confidence_threshold": 0.5
  }
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "started",
  "message": "Processing started",
  "clips_count": 2
}
```

**Logic:**
- Retrieves the card configuration from the database
- Checks if the project associated with the card has any face images without any embeddings, if so, generates the embeddings and adds to the database.
- Checks all clips that have status 'queued' or 'extracting_frames'and starts the frame extraction process from the beginning. When complete, sets the status to 'extraction_complete' or 'error'. 
- Checks all frames associated with the card with the status 'queud', 'extraction_complete' or 'detecting_faces' and begins face detection process. Once complete, sets the status to 'detection_complete' or 'error'.
- Checks for all detected faces in the card with the status 'queued', or 'matching_faces' and matches them against the consent profile embeddings. Once complete, sets the status to 'matching_complete' or 'error'. If there is an error, the frame status is set to 'error'.
- Once all detected faces have been matched for a given frame, set the frame status to 'recognition_complete'.
- Once all frames have been processed for a given clip, set the clip status to 'processing_complete'. Do not set the clip status to 'error', this is only the case if frame extraction fails.
- any time a new frame, detected face or face match is created or updated, update the database.
- This all runs in the background but the API endpoint returns a task ID for status checking

### POST /api/stop-processing
Stops any active processing.

**Request Body:**
```json
{
  "task_id": "uuid-string"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Processing stopped successfully"
}
```

**Logic:**
- Stops the specified background processing task
- Returns confirmation of processing stop