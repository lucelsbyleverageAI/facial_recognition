# Facial Recognition Application Requirements

## 1. App Overview
The Facial Recognition Processing Pipeline is a cross-platform application that processes video footage to detect faces and match them against pre-approved consent profiles. The primary purpose is to identify faces in video footage that do not have corresponding consent, allowing production teams to easily identify which footage may require additional clearance or editing.

Key aspects:

- Python-based application running locally on Windows/Mac/Linux via Docker
- Local database storage for projects, consent profiles, videos, and processing results
- Automated video frame extraction, face detection, and consent matching
- Web-based UI for configuring and monitoring the processing pipeline
- Report generation for identifying non-consented faces in footage

## 2. User Flows

### 2.1 Project Setup
1. User launches application
2. System scans consent folders (pre-defined location) to identify available projects based on folder and subfolder names & contents
3. System scans for consent profiles and images within the project folder
4. System adds any new consent profiles to the database
5. User sees list of projects available and can expand to see the consent profiles and images within the project
6. User can select a project to work in (user cannot create new projects)

### 2.2 Card Setup
1. User opens a project page which shows a list of cards available for that project from the database (cards represent camera cards)
2. User can select existing cards to go to the respective card page or create a new card
3. Each card has a configuration for the processing parameters and the watchfolder location (used to scan and monitor local folder paths for footage related to the card)
4. When each card is created, the system automatically creates a default configuration for the card, but the user must set a watch folder
5. When entering a card page, the configuration and watch folder must be set if not already set (though they can be edited in the card page)

### 2.3 Watch Folder Initial Scan
1. Once the card configuration and watch folder are set, the user can select to scan the watch folder for clips
2. The system will scan the watch folders for footage and, if found, add video files to the database as clips (or update existing clips)
3. The user can select or deselect clips to be processed (to prevent existing files from being processed again)
4. After the user has selected the initial clips, the card is ready to process

### 2.4 Watch Folder Monitoring
1. After the initial scan, the user can select to start the watch folder monitoring
2. The system will monitor the watch folder for new clips and add them to the database as clips (or update existing clips)
3. The user can turn off the watch folder monitoring at any time
4. There will also be a default inactivity timeout (after a period of no new clips being detected) which will turn off the watch folder monitoring

### 2.5 Processing
1. Once the use has selected initial clips and the watch folder monitoring is set up, clips will be added to the database
2. The user can then select to start processing the clips
3. The processing will run in the background, using the card configuration, and add updated results to the database which can be viewed in the UI
4. Processing consists of the following steps:
    - Gather all consent profiles from the project
    - For any face images that haven't got embeddings, or have been updated since embeddings were last generated, generate embeddings and add to the database
    - For each clip, extract frames at the configured frame rate
    - For each frame, detect faces and match against consent profiles
    - Update database with results as frames are processed

### 2.6 Results Review
1. User can view processing results in the UI
2. User can change views to see different aspects of the results
3. User can generate reports identifying non-consented faces


# Technical Stack & Core Features

## 3. Tech Stack and APIs

### 3.1 Infrastructure
- **Docker**: Containerization for consistent environment across platforms
- **PostgreSQL**: Relational database for storing all application data
- **Hasura**: GraphQL engine for database access and management

### 3.2 Backend
- **Python**: Core programming language
- **FastAPI**: RESTful API framework for backend endpoints
- **DeepFace**: Facial recognition library
- **FFmpeg**: Video processing and frame extraction

### 3.3 Frontend
- **React**: Frontend UI library
- **Next.js**: React framework for web application

### 3.4 Key APIs and Libraries
- **DeepFace API**: Face detection, embedding generation, and face matching
- **FFmpeg**: Video frame extraction and processing
- **Hasura GraphQL API**: Database interactions

## 4. Core Features

### 4.1 Project and Consent Management
- Create and manage projects
- Import and organize consent profiles
- Generate face embeddings from consent images
- Support for both frontal and side facial images

### 4.2 Video Processing
- Watch folder monitoring for new camera cards
- Video clip detection and extraction
- Frame extraction with configurable parameters
- Optional LUT application during extraction

### 4.3 Face Processing
- Face detection in extracted frames
- Face matching against consent profiles
- Visual identification of matched vs. unmatched faces
- Storage of face embeddings and match results

### 4.4 User Interface
- Project selection and management
- Processing configuration
- Real-time processing status monitoring
- Results visualization with highlighted faces

### 4.5 Reporting
- Summary reports of processing results
- Detailed reports of non-consented faces
- Frame thumbnails with highlighted faces for each clip
- Frame thumbnails highlighting faces with bounding boxes for each clip

