# Facial Recognition Processing Pipeline - Project Wrap-up (MVP)

## Executive Summary

This document provides a comprehensive wrap-up of the Minimum Viable Product (MVP) for the Facial Recognition Processing Pipeline. It details the application's core purpose of matching faces in video footage against a consent database to aid production workflows. The overview covers its architecture (PostgreSQL, Hasura, Python/FastAPI backend, React/Next.js frontend), high-level user workflows, and project file structure. 

The database section outlines the PostgreSQL schema managed via Hasura, detailing key tables like projects, consent profiles, cards, clips, frames, and detected faces, along with the Hasura initialization process. The backend section describes the FastAPI application, its API endpoints for tasks like consent scanning and processing initiation, and the core multi-stage processing logic involving FFmpeg and DeepFace. The frontend section details the Next.js application flow, covering the Projects Dashboard, Project Details, and Card Details pages, along with its UI component strategy and state management. 

A significant portion is dedicated to local setup on macOS, explaining the rationale, the use of Docker for services (PostgreSQL, Hasura), the role of the master `setup.sh` script for full environment automation (including Apple Silicon TensorFlow specifics), and an optional AppleScript for a clickable setup. 

Finally, the document outlines key limitations of the MVP—such as the need for robust real-world data testing, setup validation on fresh machines, processing optimization, and UX/UI refinement—and proposes corresponding next steps to mature the application into a production-ready tool.

## I. Application Overview

### 1.1. Purpose and Functionality

The Facial Recognition Processing Pipeline is a locally-run application designed to process video footage to detect human faces and match them against a pre-approved database of consent profiles. Its primary purpose is to assist production teams in efficiently identifying individuals within footage for whom consent may be missing or requires verification. This streamlines the clearance and editing workflows, ensuring compliance and reducing manual review time.

### 1.2. High-Level Workflow

The typical user journey through the application follows these main stages:

1.  **Project Setup**: The application scans pre-defined consent folder locations to identify available projects (currently this includes a sandbox S3 bucket or any folders on a local machine). Consent profiles and associated images within these project folders are automatically detected and registered given they follow the relevant file and folder naming conventions agreed for this project.
2.  **Card Setup**: Within a selected project, users can create new "cards" or select existing ones. Each card represents a unit of footage (e.g., a camera card) and has an associated processing configuration.
3.  **Watch Folder Configuration**: For each card, the user defines one or more local folder paths ("watch folders") that the system will scan and monitor for video files related to that card.
4.  **Initial Scan & Monitoring**: The system performs an initial scan of the configured watch folders to identify existing video clips. After the initial scan, any identified clips are added to an approval list to allow users to select or deselect clips (important in case the card location has existing footage related to another shoot). Following this, users can activate monitoring, which allows the system to automatically detect and add new clips as they are copied into the watch folder.
5.  **Processing**: Selected clips are queued for processing. This involves:
    *   Generating embeddings for any new or updated consent images related to the project (so identified faces can be matched based on their embeddings)
    *   Extracting frames from video clips according to the card's configuration.
    *   Detecting faces in each frame.
    *   Matching detected faces against the consent profile embeddings.
6.  **Results Review**: Users can view the processing results in the web-based UI. This includes frame-by-frame breakdowns, visual indicators of matched/unmatched faces, and the ability to generate reports.

### 1.3. Technology Stack

The application is built using a combination of technologies to handle its diverse requirements:

*   **Infrastructure**:
    *   **Docker**: Used for containerizing the PostgreSQL database and Hasura GraphQL engine, ensuring a consistent environment for these services.
    *   **PostgreSQL**: Serves as the relational database for storing all application data, including project details, consent information, clip metadata, and processing results.
    *   **Hasura**: Provides a powerful GraphQL engine over the PostgreSQL database, simplifying data access and mutations for the frontend application.

*   **Backend**:
    *   **Python (3.10)**: The core programming language for the backend logic.
    *   **FastAPI**: A modern, fast web framework for building the RESTful API endpoints that handle operations requiring complex processing or direct file system interaction.
    *   **DeepFace**: The primary library used for facial recognition tasks, including face detection, embedding generation, and face matching.
    *   **FFmpeg**: A comprehensive multimedia framework used for video processing, particularly for extracting frames from video clips.

*   **Frontend**:
    *   **React**: A JavaScript library for building user interfaces.
    *   **Next.js (v14+ with App Router)**: A React framework providing a robust structure for the web application, including server-side rendering, routing, and an optimized development experience.
    *   **shadcn/ui**: A component library built on Radix UI and Tailwind CSS, used to create a modern and consistent user interface.
    *   **Tailwind CSS**: A utility-first CSS framework for styling the application.
    *   **React Query**: Used for fetching, caching, and managing server state, particularly for interacting with the Hasura GraphQL API.
    *   **React Context + Hooks**: Employed for managing global and local component state.

### 1.4. Project File Structure

The project is organized into several key directories at the root level:

*   **`backend/`**: Contains the Python FastAPI application responsible for core processing logic and API services.
*   **`frontend/`**: Contains the Next.js/React web application that provides the user interface.
*   **`hasura/`**: Holds configuration files for the Hasura GraphQL engine, including the database schema migration.
*   **`docs/`**: Contains all project documentation, including this wrap-up document, Product Requirements (PRD), Application Flow diagrams, API endpoint specifications, and Frontend Guidelines.
*   **`docker-compose.yaml`**: Defines the Docker services (PostgreSQL, Hasura) and their configurations for local deployment.
*   **`setup.sh`**: The master setup script for automating the local development environment setup, particularly for macOS.
*   **`.env` files (root, backend, frontend)**: Provides environment variable configuration.

**`backend/src/` Directory Structure:**

The backend source code is primarily located within the `backend/src/` directory:
*   `api/`: Contains FastAPI routers and endpoint definitions.
*   `config.py`: Manages application configuration and settings.
*   `schemas/`: Pydantic schemas for data validation and serialization.
*   `services/`: Business logic and service layer components (e.g., for processing, database interaction).
*   `utils/`: Utility functions and helper modules.
*   `server.py`: The main FastAPI application instance and server startup logic.
*   `__init__.py`: Marks the directory as a Python package.

**`frontend/src/` Directory Structure:**

The frontend source code is organized within `frontend/src/` following Next.js conventions:
*   `app/`: Core of the Next.js App Router, containing layouts, pages, and route definitions.
*   `components/`: Reusable UI components, often categorized further (e.g., `ui/` for shadcn components, domain-specific components).
*   `hooks/`: Custom React hooks for managing state and side effects.
*   `lib/`: Utility functions, helper scripts, and library configurations (e.g., GraphQL client setup).
*   `types/`: TypeScript type definitions and interfaces.

## II. Database

The application relies on a PostgreSQL relational database, with Hasura providing a GraphQL API layer for simplified data access and management, primarily from the frontend. The entire database schema is defined and initialized through the `hasura/full_migration.sql` script, while Hasura's metadata (table tracking and relationships) is configured via the `hasura/init_hasura.sh` script.

### 2.1. Overview

*   **PostgreSQL**: Serves as the robust, open-source relational database storing all persistent data for the application. This includes project information, consent profiles, media metadata, processing configurations, and results.
*   **Hasura GraphQL Engine**: Sits on top of the PostgreSQL database and automatically generates a comprehensive GraphQL API. This allows the frontend to query and mutate data efficiently without requiring custom backend resolvers for most data-centric operations. Hasura also manages permissions and relationships, making complex data fetching straightforward.

### 2.2. Schema Details (`hasura/full_migration.sql`)

The `full_migration.sql` script defines the structure of the database, including tables, columns, data types, constraints, and indexes. Key tables include:

*   **`projects`**:
    *   Stores core project information.
    *   `project_id` (UUID, PK): Unique identifier for the project.
    *   `project_name` (TEXT): Name of the project.
    *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of project creation.

*   **`consent_profiles`**:
    *   Manages consent profiles associated with projects.
    *   `profile_id` (UUID, PK): Unique identifier for the consent profile.
    *   `project_id` (UUID, FK to `projects`): Links the profile to a project.
    *   `person_name` (TEXT): Name of the individual in the consent profile.

*   **`consent_faces`**:
    *   Stores individual face images and their embeddings for each consent profile.
    *   `consent_face_id` (UUID, PK): Unique identifier for a consent face image.
    *   `profile_id` (UUID, FK to `consent_profiles`): Links the face to a consent profile.
    *   `face_image_path` (TEXT, UNIQUE): Path to the consent face image file.
    *   `pose_type` (TEXT): Indicates face pose (e.g., 'F' for frontal, 'S' for side).
    *   `face_embedding` (JSONB): Stores the generated facial embedding.
    *   `last_updated` (TIMESTAMP WITH TIME ZONE): Timestamp of the last update.

*   **`cards`**:
    *   Represents camera cards or batches of footage within a project.
    *   `card_id` (UUID, PK): Unique identifier for the card.
    *   `project_id` (UUID, FK to `projects`): Links the card to a project.
    *   `card_name` (TEXT): Name of the card.
    *   `description` (TEXT, Optional): Description of the card.
    *   `created_at` (TIMESTAMP WITH TIME ZONE): Timestamp of card creation.
    *   `status` (TEXT): Current status of the card (e.g., 'pending', 'processing', 'complete').

*   **`card_configs`**:
    *   Stores processing configurations specific to each card. A default configuration is automatically created when a new card is added, thanks to the `create_default_card_config` function and `trigger_create_card_config` trigger.
    *   `config_id` (UUID, PK): Unique identifier for the configuration.
    *   `card_id` (UUID, FK to `cards`, UNIQUE): Links the configuration to a card (one-to-one).
    *   Includes various parameters for video processing and face recognition, such as `scene_sensitivity`, `fallback_frame_rate`, `lut_file`, `model_name` (for DeepFace), `detector_backend`, `distance_metric`, `threshold`, etc.
    *   Constraints ensure valid parameter ranges and interdependencies (e.g., `eq_lut_constraint`).

*   **`watch_folders`**:
    *   Defines local folder paths to be monitored for video clips, associated with a card's configuration.
    *   `watch_folder_id` (UUID, PK): Unique identifier for a watch folder entry.
    *   `config_id` (UUID, FK to `card_configs`): Links the watch folder to a card's configuration.
    *   `folder_path` (TEXT): The absolute path to the local folder to be monitored.
    *   `status` (TEXT): Current status of the watch folder (e.g., 'idle', 'scanned', 'active').
    *   Unique constraint on (`config_id`, `folder_path`).

*   **`clips`**:
    *   Contains information about individual video clips discovered in watch folders.
    *   `clip_id` (UUID, PK): Unique identifier for a clip.
    *   `card_id` (UUID, FK to `cards`): Links the clip to a card.
    *   `watch_folder_id` (UUID, FK to `watch_folders`, Optional): Links to the specific watch folder it came from.
    *   `filename` (TEXT): Name of the video file.
    *   `path` (TEXT): Full path to the video file.
    *   `status` (TEXT): Processing status of the clip (e.g., 'pending', 'queued', 'processing_complete').
    *   `error_message` (TEXT, Optional): Stores error messages if processing fails.
    *   Unique constraint on (`card_id`, `filename`).

*   **`frames`**:
    *   Stores information about frames extracted from video clips.
    *   `frame_id` (UUID, PK): Unique identifier for a frame.
    *   `clip_id` (UUID, FK to `clips`): Links the frame to its parent clip.
    *   `timestamp` (TEXT): Timecode of the frame (HH:MM:SS:FF format).
    *   `raw_frame_image_path` (TEXT): Path to the saved raw (unprocessed) frame image.
    *   `processed_frame_image_path` (TEXT, Optional): Path to the saved processed frame image (e.g., with bounding boxes).
    *   `status` (TEXT): Processing status of the frame (e.g., 'queued', 'detection_complete', 'recognition_complete').

*   **`detected_faces`**:
    *   Stores information about faces detected within frames, including their embeddings.
    *   `detection_id` (UUID, PK): Unique identifier for a detected face.
    *   `frame_id` (UUID, FK to `frames`): Links the detected face to a specific frame.
    *   `confidence` (DOUBLE PRECISION): Confidence score of the face detection.
    *   `facial_area` (JSONB): Coordinates of the bounding box for the detected face.
    *   `face_embeddings` (JSONB): The generated facial embedding for this detected face.
    *   `status` (TEXT): Processing status for this specific face (e.g., 'queued', 'matching_complete').

*   **`face_matches`**:
    *   Records matches found between detected faces and consent faces.
    *   `match_id` (UUID, PK): Unique identifier for a face match.
    *   `detection_id` (UUID, FK to `detected_faces`): Links to the detected face.
    *   `consent_face_id` (UUID, FK to `consent_faces`): Links to the matched consent face.
    *   `distance` (NUMERIC): The distance score between the detected face embedding and the consent face embedding.
    *   `threshold` (NUMERIC): The threshold used for this match determination.
    *   `target_x`, `target_y`, `target_w`, `target_h` (INTEGER): Bounding box coordinates from the detected face.
    *   `source_x`, `source_y`, `source_w`, `source_h` (INTEGER): Bounding box coordinates from the consent face (if applicable, might be more conceptual).

*   **`processing_tasks`**:
    *   Tracks the status, progress, and stage of various backend processing tasks (e.g., embedding generation, full card processing).
    *   `task_id` (UUID, PK): Unique identifier for a processing task.
    *   `card_id` (UUID, FK to `cards`): Links the task to a card (if applicable).
    *   `status` (TEXT): Overall status of the task (e.g., 'pending', 'processing_clips', 'complete', 'error').
    *   `stage` (TEXT, Optional): Current stage of a multi-stage task.
    *   `progress` (NUMERIC): Progress percentage (0-1).
    *   `message` (TEXT, Optional): Informational messages related to the task.

The script also defines numerous indexes (e.g., `idx_card_project_id`, `idx_frame_clip_id`) on foreign key columns and frequently queried fields to ensure efficient database performance.

### 2.3. Hasura Integration (`hasura/init_hasura.sh`)

The `init_hasura.sh` script automates the configuration of the Hasura GraphQL engine after the database schema is in place. Its key responsibilities are:

1.  **Health Check**: It waits for the Hasura service to become fully ready and accessible via its health check endpoint.
2.  **Table Tracking**: It iterates through a predefined list of tables (matching those in `full_migration.sql`) and sends API requests to Hasura to "track" each table. Tracking a table exposes it through the GraphQL API, allowing it to be queried.
3.  **Relationship Tracking**: The script then defines and tracks foreign key relationships between tables. It specifies:
    *   **Array Relationships**: Parent-to-child relationships (e.g., a `project` can have multiple `cards`).
    *   **Object Relationships**: Child-to-parent relationships (e.g., a `card` belongs to one `project`).
    These relationships are crucial as they allow for nested GraphQL queries, making it easy for the frontend to fetch related data in a single request (e.g., querying a project and all its associated cards and consent profiles).
4.  **Special Relationships**: It includes specific handling for one-to-one relationships, such as creating the `card_config` object relationship on the `cards` table using a manual configuration for the `card_id` mapping.

By automating these steps, `init_hasura.sh` ensures that the Hasura GraphQL API is consistently configured to reflect the underlying PostgreSQL database structure, enabling seamless data interaction for the frontend application.

## III. Backend

The backend of the Facial Recognition Processing Pipeline is a Python application developed using the FastAPI framework. It serves as the engine for all complex processing tasks, file system interactions, and operations that are not suitable for direct handling by the frontend or the Hasura GraphQL layer. The backend exposes a RESTful API for these purposes.

### 3.1. Overview

The primary responsibilities of the backend include:

*   **Project and Consent Management**: Scanning local file systems (or specified S3 locations) to discover projects and consent profiles based on predefined naming conventions. It also handles the generation and storage of facial embeddings from consent images.
*   **Watch Folder and Clip Management**: Scanning user-defined local watch folders for video clips, adding them to the database, and providing functionality to monitor these folders for new additions.
*   **Core Processing Pipeline**: Orchestrating the multi-stage process of video analysis, which includes frame extraction, face detection in frames, generation of embeddings for detected faces, and matching these faces against the consent database.
*   **Task Management**: Managing and tracking the status of long-running background tasks, such as embedding generation and video processing.

### 3.2. API Endpoints (`docs/3-BackendAPIEndpoints.md`)

The backend exposes several key API endpoints to facilitate its operations. These are designed to be called by the frontend to initiate and manage various processes.

*   **Project Discovery and Consent Profile Processing**
    *   `POST /api/scan-consent-folders`
        *   **Purpose**: Scans a specified root folder (local or S3) for projects and consent profiles based on folder naming conventions (`{projectId}_{projectName}` and `{consentProfileId}_{consentProfileName}`).
        *   **Logic**: Identifies projects, consent profiles, and associated face images. Creates or updates corresponding entries in the database. Returns statistics on items found, created, and updated.
    *   `POST /api/generate-consent-embeddings`
        *   **Purpose**: Generates facial embeddings for consent images within a specified project that do not currently have embeddings or have been updated since the last generation.
        *   **Logic**: Retrieves relevant consent images, initiates a background task using DeepFace (with provided configuration) to generate embeddings, and stores these embeddings in the `consent_faces` table. Returns a task ID for status tracking.

*   **Watch Folder Management**
    *   `POST /api/scan-watch-folder`
        *   **Purpose**: Scans a specified local watch folder for video clips.
        *   **Logic**: Identifies video files, creates or updates `clips` entries in the database with a 'pending' status. Returns a task ID and statistics.
    *   `POST /api/start-watch-folder-monitoring`
        *   **Purpose**: Activates background monitoring of a specified watch folder for new video clip additions.
        *   **Logic**: Updates the watch folder status to 'active'. A background process watches the folder; new video files detected are automatically added as clips with 'pending' status. Monitoring can time out due to inactivity. Returns confirmation.
    *   `POST /api/stop-watch-folder-monitoring`
        *   **Purpose**: Deactivates monitoring for a specified watch folder.
        *   **Logic**: Updates the watch folder status to 'idle' and stops the background monitoring process. Returns confirmation.

*   **Processing Management**
    *   `POST /api/start-processing`
        *   **Purpose**: Initiates the main facial recognition processing pipeline for a given card.
        *   **Logic**: This is a multi-stage background process:
            1.  **Consent Embeddings Check**: Ensures all consent faces for the project have embeddings; generates if missing.
            2.  **Frame Extraction**: For clips with status 'queued' or 'extracting_frames', extracts frames using FFmpeg based on card configuration. Frame metadata and image paths are stored. Status updated to 'extraction_complete' or 'error'.
            3.  **Face Detection**: For frames with status 'queued' or 'detecting_faces', uses DeepFace to detect faces. Detected face data (bounding box, confidence) is stored. Status updated to 'detection_complete' or 'error'.
            4.  **Face Matching**: For detected faces with status 'queued' or 'matching_faces', generates embeddings and matches them against project consent embeddings. Match results (distance, threshold, matched consent face) are stored. Status updated to 'matching_complete' or 'error'.
            5.  **Status Updates**: As each stage completes for an item (clip, frame, detected face), its status is updated in the database. Upon completion of all stages for a frame, its status becomes 'recognition_complete'. Once all frames for a clip are processed, the clip status becomes 'processing_complete'.
        *   Returns a `task_id` for overall process tracking via the `processing_tasks` table.
    *   `POST /api/stop-processing`
        *   **Purpose**: Halts an active processing task.
        *   **Logic**: Sends a signal to the specified background processing task to terminate its operations. Returns confirmation.

### 3.3. Core Processing Logic

The backend employs a sophisticated pipeline for processing video footage:

1.  **Consent Embedding Generation**: Before any video processing for a card begins, the system ensures that all consent profiles associated with the card's project have up-to-date facial embeddings. DeepFace, configured via parameters from `card_configs` (e.g., `model_name`, `detector_backend`), is used to analyze consent images and generate these embeddings, which are stored in the `consent_faces.face_embedding` field.

2.  **Video Frame Extraction**: For each selected video clip, FFmpeg is utilized to extract individual frames at a rate determined by the `card_configs` (e.g., `fallback_frame_rate`). If a Look-Up Table (LUT) is specified (e.g., `lut_file`) and `use_eq` is false, it can be applied during this stage. Raw frame images are saved locally, and their paths and timestamps are recorded in the `frames` table.

3.  **Face Detection**: Each extracted frame is then processed by DeepFace (again, using parameters from `card_configs` like `detector_backend`, `enforce_detection`, `detection_confidence_threshold`) to detect the presence and location of human faces. Information about each detected face, including its bounding box coordinates (`facial_area`) and detection confidence, is stored in the `detected_faces` table.

4.  **Facial Embedding for Detected Faces**: For each face successfully detected in a frame, DeepFace is used once more to generate a facial embedding. This embedding is stored in `detected_faces.face_embeddings`.

5.  **Face Matching**: The embedding of each detected face is compared against all pre-computed embeddings of consent faces associated with the project. The comparison uses the `distance_metric` and `threshold` specified in `card_configs`. If a detected face's embedding is sufficiently similar (i.e., distance is below the threshold) to a consent face embedding, a match is recorded in the `face_matches` table, linking the `detected_faces` entry to the corresponding `consent_faces` entry and storing the match distance.

6.  **Status and Progress Tracking**: The entire workflow is asynchronous. The status of each entity (clip, frame, detected face) and the overall processing task is meticulously updated in the database, allowing the frontend to monitor progress in near real-time.

### 3.4. File Structure (`backend/src/`)

The backend source code is primarily organized within the `backend/src/` directory, promoting modularity and maintainability:

*   **`api/`**: Contains FastAPI routers that define the API endpoints. Each router typically groups related endpoints (e.g., `api/projects.py`, `api/cards.py`).
*   **`config.py`**: Manages application-level configurations, often loaded from environment variables (e.g., database URLs, API keys, settings for external services).
*   **`schemas/`**: Defines Pydantic models used for request and response validation, serialization, and data structure definition within the API and service layers.
*   **`services/`**: Houses the core business logic of the application. This includes services for managing projects, consent data, video clips, and orchestrating the processing pipeline (e.g., `services/processing_service.py`, `services/consent_service.py`).
*   **`utils/`**: Contains utility functions, helper classes, and common tools used across different parts of the backend (e.g., file handling utilities, database interaction helpers not part of a specific service).
*   **`server.py`**: The main entry point for the FastAPI application. It initializes the FastAPI app instance, includes the API routers, and configures middleware or application-level event handlers.
*   **`__init__.py`**: An empty file that marks the `src` directory as a Python package, allowing for relative imports between modules.

## IV. Frontend

The frontend of the Facial Recognition Processing Pipeline is a modern web application built using React and the Next.js (v14+) framework, specifically leveraging the App Router for routing and layout management. It provides the primary user interface for interacting with the system, allowing users to manage projects, configure processing cards, monitor progress, and review results.

### 4.1. Overview

The frontend is designed to be intuitive and responsive, adhering to the guidelines set out in `docs/4-FrontendGuidelines.md`. Key technologies and libraries include:

*   **React**: The core JavaScript library for building the user interface components.
*   **Next.js (App Router)**: Provides the framework for the application, including server-side rendering capabilities, optimized builds, and a structured approach to routing and page organization.
*   **shadcn/ui**: A collection of reusable UI components built on Radix UI and styled with Tailwind CSS. This ensures a consistent and modern look and feel across the application (e.g., Buttons, Cards, Tables, Dialogs, Forms).
*   **Tailwind CSS**: A utility-first CSS framework used for all styling, allowing for rapid development and a highly customizable design.
*   **React Query**: Manages server state, data fetching, and caching, particularly for interactions with the Hasura GraphQL API. It simplifies handling asynchronous operations and keeps the UI synchronized with backend data.
*   **React Context + Hooks**: Used for managing global and local component state where appropriate, complementing React Query for client-side state needs.
*   **Lucide React**: The primary icon library, providing a comprehensive set of SVG-based icons.

### 4.2. Application Flow (`docs/2-AppFlow.md`)

The user navigates through the application via a series of well-defined pages and interactions:

1.  **Projects Dashboard (`/`)**:
    *   **Landing Page**: This is the initial view when the application is launched.
    *   **Display**: Shows a grid of project cards. Each card displays the project name, ID, and creation date.
    *   **Interactions**: Each project card has a "Select" button to navigate to the Project Details page and an "Expand" toggle. Expanding a project reveals a preview of its consent profiles (names and thumbnails) and associated cards (IDs and names), with "Show More" options if the lists are extensive.
    *   **Navigation**: A header with the application name ("Facial Recognition Processing") is present.

2.  **Project Details Page (`/project/{projectId}`** - actual path may vary based on Next.js App Router structure):
    *   **Navigation**: Accessed by clicking "Select" on a project card from the dashboard. Features breadcrumb navigation (e.g., "Projects > [Project Name]") for easy return to the dashboard. A Home icon in the header also allows navigation back to the dashboard.
    *   **Layout**: Divided into two main sections:
        *   **Cards Section (Top Half)**:
            *   Displays a searchable and sortable data grid of cards associated with the project (Card ID, Card Name, Status, Last Modified Date).
            *   Each card row has a "Select" button to navigate to the Card Details Page.
            *   Includes pagination, quick status filters, and a refresh button.
            *   A prominent "Add New Card" button opens a modal allowing users to create a new card by providing a name and optional description. Submission adds the card to the database and updates the grid.
        *   **Consent Profiles Section (Bottom Half)**:
            *   Displays consent profiles in a virtualized grid with thumbnails and names.
            *   Features a search bar for filtering profiles, an alphabetical quick-jump sidebar, "Load More" for infinite scrolling, and group headers for alphabetical sections.
            *   Hovering over a profile can show additional details. Includes a refresh button.

3.  **Card Details Page (`/project/{projectId}/card/{cardId}`** - actual path may vary):
    *   **Navigation**: Accessed by clicking "Select" on a card from the Project Details page. Breadcrumbs show "Projects > [Project Name] > [Card Name]", allowing navigation back to the project or dashboard. A Home icon is also available.
    *   **Layout**: Organized into two main tabs:
        *   **Processing Dashboard Tab**:
            *   **Configuration Section**: Displays existing watch folders. Allows users to add new watch folders (by specifying a local path) or remove existing ones. Each watch folder has actions to "Run Initial Scan" or toggle monitoring status ("Activate"/"Deactivate"). If no watch folders are present, the UI encourages adding one, as processing cannot start without it.
            *   **Processing Configuration**: A button opens a modal where users can view and adjust processing parameters for the card (e.g., DeepFace model, sensitivity, frame rate), which are stored in `card_configs`.
            *   **Clips Section**: Displays clips associated with the card, showing their status (e.g., unselected, pending, queued, processing, completed). Users can cancel pending clips (moving them to "unselected").
            *   **Processing Controls**: A "Start Processing" button triggers the backend to process queued clips. Once processing starts, this button may change to a "Stop Processing" button to halt ongoing tasks.
            *   The UI reflects the current processing status of the card and its associated tasks.
        *   **Results Tab**:
            *   **Data Display**: Presents a paginated table of processing results on a frame-by-frame basis. Columns include Clip, Frame, Timestamp, Thumbnail (of the frame), Status, count of Detected Faces, and count of Matched Faces.
            *   **Controls**: Options to increase rows displayed per page and navigate through pages.
            *   **Filtering**: Pre-defined filter options for status (e.g., frames with detected faces, frames with matched faces, frames with unmatched faces).
            *   **Reporting**: A button to trigger the generation of a report (details of report content and format would be part of this feature).

### 4.3. Key UI Components and State Management (`docs/4-FrontendGuidelines.md`)

The frontend places a strong emphasis on a consistent and accessible user experience, achieved through:

*   **Component Library (shadcn/ui)**: Extensive use of pre-built and customizable components such as `<Button>`, `<Card>`, `<Table>`, `<Dialog>`, `<Input>`, `<Select>`, `<Progress>`, `<Badge>`, and `<Tabs>`. These components ensure visual consistency and come with built-in accessibility features.
*   **Data Fetching (React Query)**: All interactions with the Hasura GraphQL API (for fetching project data, card lists, consent profiles, processing status, results, etc.) and the backend REST API (for initiating actions like scans or processing) are managed through React Query. This provides caching, automatic refetching, and optimistic updates, leading to a smoother user experience.
*   **State Management (React Context + Hooks)**: For global state (like theme settings or user preferences, if any) and complex local component state, React Context and custom Hooks are employed. This keeps component logic clean and state management predictable.
*   **Forms**: Form handling leverages shadcn/ui components in conjunction with libraries like React Hook Form for validation and submission.
*   **Feedback Mechanisms**: User feedback is provided through `<Alert>` components for status messages, `<Toaster>` and `<Toast>` for temporary notifications, and `<Progress>` indicators for long-running operations.
*   **Responsive Design**: Built with Tailwind CSS, the UI is designed to be responsive across various screen sizes, ensuring usability on different devices (though primarily targeting desktop use for this type of application).

### 4.4. File Structure (`frontend/src/`)

The frontend source code is organized within the `frontend/src/` directory, adhering to common Next.js (App Router) and React project conventions:

*   **`app/`**: This is the core directory for the Next.js App Router. It contains:
    *   Route groups (e.g., `(dashboard)/` for main application routes).
    *   `layout.tsx`: Defines the root layout and potentially nested layouts for different sections of the application.
    *   `page.tsx`: Defines the UI for specific routes (e.g., `app/page.tsx` for the Projects Dashboard, `app/[projectId]/page.tsx` for Project Details).
    *   Subdirectories for nested routes (e.g., `app/[projectId]/[cardId]/page.tsx` for Card Details).
    *   Special files like `loading.tsx` for loading UI and `error.tsx` for error handling within routes.
*   **`components/`**: Contains reusable React components, often further organized by feature or type:
    *   `ui/`: Typically holds the shadcn/ui components that have been added to the project.
    *   Domain-specific components (e.g., `cards/`, `consent/`, `processing/`, `results/`, `layout/` as suggested in `docs/4-FrontendGuidelines.md`).
*   **`hooks/`**: Stores custom React hooks used throughout the application to encapsulate reusable logic and stateful behavior (e.g., `useTheme` for dark mode toggle, custom hooks for specific data fetching or state management patterns).
*   **`lib/`**: Contains utility functions, helper scripts, and configurations. This might include GraphQL client setup (e.g., Apollo Client or a lightweight fetch wrapper for React Query), date formatting functions, or other shared logic.
*   **`types/`**: Holds TypeScript type definitions, interfaces, and enums used across the frontend codebase to ensure type safety and improve developer experience.

## V. Local Setup

The Facial Recognition Processing Pipeline is designed to be run locally on a user's machine, primarily targeting macOS environments, especially those with Apple Silicon (M1/M2/M3) due to specific dependencies like TensorFlow with Metal support. This local-first approach is essential because the application needs direct access to the local file system for critical functions such as scanning consent folders and monitoring watch folders for video clips.

### 5.1. Rationale for Local Setup

The decision to keep the core backend and frontend applications running as local processes, rather than fully containerizing them, stems from the requirement to interact seamlessly with the user's local file system. Key operations include:

*   **Consent Folder Scanning**: The backend needs to read project and consent information from local directory structures (or designated S3 buckets configured with local credentials).
*   **Watch Folder Monitoring**: Users define local folder paths for camera cards/media. The backend must be able to scan these paths for video files and continuously monitor them for new additions.

While supporting services like the database and GraphQL engine are containerized for ease of setup and consistency, the main application logic runs directly on the host machine to facilitate these file system interactions.

### 5.2. Dockerized Services (`docker-compose.yaml`)

To simplify the setup of essential backing services, Docker and Docker Compose are utilized. The `docker-compose.yaml` file defines the following services:

*   **`postgres`**: 
    *   **Image**: `postgres:15`
    *   **Purpose**: Provides the PostgreSQL relational database instance where all application data is stored.
    *   **Volumes**: Mounts a named volume (`postgres_data`) for persistent data storage and crucially mounts `hasura/full_migration.sql` to `/docker-entrypoint-initdb.d/init.sql`. This ensures that the database schema is automatically created/initialized when the container starts for the first time.
    *   **Environment**: Configured with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` from the root `.env` file.

*   **`graphql-engine` (Hasura)**:
    *   **Image**: `hasura/graphql-engine:v2.42.0`
    *   **Purpose**: Runs the Hasura GraphQL engine, providing the GraphQL API layer over the PostgreSQL database.
    *   **Depends On**: `postgres`, ensuring the database is available before Hasura starts.
    *   **Environment**: Configured with essential Hasura settings, including `HASURA_GRAPHQL_DATABASE_URL` (pointing to the `postgres` service) and `HASURA_GRAPHQL_ADMIN_SECRET`, both sourced from the root `.env` file. It also enables the console and dev mode.

*   **`data-connector-agent`**:
    *   **Image**: `hasura/graphql-data-connector:v2.42.0`
    *   **Purpose**: Provides data connector capabilities for Hasura, though for this project's current scope relying on PostgreSQL, its direct usage might be minimal but is included as part of the standard Hasura setup for broader data source compatibility.

These services are orchestrated via `docker compose up -d`, typically managed by the main `setup.sh` script.

### 5.3. Master Setup Script (`setup.sh`)

The `setup.sh` script, located in the project root, is the cornerstone of the local development environment setup. It is designed primarily for macOS (with specific attention to Apple Silicon) and automates a comprehensive list of tasks:

1.  **Prerequisite Checks**: Verifies the presence of essential tools:
    *   Python 3.10
    *   Poetry (Python dependency manager)
    *   ffmpeg (for video processing)
    *   Docker (and checks if Docker Desktop is running)
    *   Hasura CLI
    *   Node.js (for the frontend)
    It attempts to install some of these via Homebrew if they are missing.

2.  **Environment File Management**: Checks for the existence of `.env` files in the root, `backend/`, and `frontend/` directories. If they are missing but corresponding `.env.example` files exist, it copies the examples to create the `.env` files, prompting the user to update them with necessary credentials and paths.

3.  **Backend Setup (Python)**:
    *   Navigates to the `backend/` directory.
    *   Configures Poetry to use Python 3.10 and creates/activates a virtual environment.
    *   **Crucially for Apple Silicon**: It includes steps to build `tensorflow-io-gcs-filesystem` from source and install `tensorflow` along with `tensorflow-metal` for GPU acceleration, addressing common setup hurdles on M1/M2/M3 Macs.
    *   Installs all other Python dependencies defined in `pyproject.toml` using `poetry install`.
    *   Includes a basic verification step to check if key libraries (TensorFlow, DeepFace, RetinaFace) can be imported.

4.  **Frontend Setup (Node.js)**:
    *   Navigates to the `frontend/` directory.
    *   Installs Node.js dependencies using `npm install` (or `npm ci` if `package-lock.json` exists).

5.  **Docker Environment Management**:
    *   Ensures Docker Desktop is running.
    *   Stops any existing Docker services (`docker compose down`).
    *   Optionally removes persistent Docker volumes (e.g., `facial_recognition_postgres_data`) to ensure a clean slate if needed.
    *   Starts the Docker services (PostgreSQL, Hasura) in detached mode (`docker compose up -d`).

6.  **Hasura Initialization**: After the Docker services are up, it executes the `hasura/init_hasura.sh` script. This script, in turn:
    *   Waits for the Hasura GraphQL engine to be healthy.
    *   Tracks all necessary tables from the PostgreSQL database (defined in `full_migration.sql`).
    *   Creates the required foreign key relationships within Hasura, enabling the full power of its GraphQL API for nested queries.

7.  **Server Startup**: Finally, the script starts:
    *   The backend FastAPI server using `poetry run uvicorn src.server:app --reload` (output logged to `/tmp/backend-server.log`).
    *   The frontend Next.js development server using `npm run dev`.

The script is designed to be idempotent where possible and provides informative logging throughout the process.

### 5.4. macOS Specific Setup (`backend/MAC_SETUP.md`)

The `backend/MAC_SETUP.md` file serves as a detailed, supplementary guide specifically for setting up the Python backend environment on macOS with Apple Silicon processors. While the main `setup.sh` script automates these steps, `MAC_SETUP.md` is invaluable for:

*   **Manual Troubleshooting**: If users encounter issues with the automated script, particularly concerning TensorFlow, `tensorflow-metal`, or the `tensorflow-io-gcs-filesystem` build, this document provides step-by-step manual instructions.
*   **Understanding Specific Steps**: It offers a clearer explanation of why certain steps are necessary for Apple Silicon, such as building `tensorflow-io-gcs-filesystem` from source.
*   **Alternative Setup**: For users who prefer a manual setup or need to integrate parts of the setup into a different workflow.

It covers virtual environment creation, the manual build process for `tensorflow-io-gcs-filesystem`, installation of TensorFlow with Metal, and other dependencies, along with a verification script.

### 5.5. Running the Application

The primary method for setting up and running the entire application locally is by executing the `setup.sh` script from the project root directory:

```bash
./setup.sh
```

This script handles all prerequisites, service initializations, and server startups. Once the script completes successfully:

*   The **PostgreSQL database** and **Hasura GraphQL engine** will be running in Docker containers.
*   The **Backend FastAPI server** will be running as a local Python process, typically accessible at `http://localhost:8000`.
*   The **Frontend Next.js development server** will be running as a local Node.js process, typically accessible at `http://localhost:3000`.

Users can then access the frontend application through their web browser at `http://localhost:3000` to interact with the system. The backend API documentation (Swagger UI) is usually available at `http://localhost:8000/docs`.

### 5.6. Creating a Clickable Setup Application (macOS - Optional)

For added convenience on macOS, users can create a clickable application that executes the main `setup.sh` script. This involves using AppleScript to tell the Terminal to run the script.

1.  **Open Script Editor**:
    *   Launch Script Editor (found in `Applications > Utilities`).

2.  **Enter the AppleScript Code**:
    *   In the new script window, enter the following AppleScript. This specific script activates Terminal, changes the directory to the project's root, and then executes `setup.sh`.

    ```applescript
    tell application "Terminal"
        activate
        do script "cd /Users/lucelsby/Documents/repos/chwarel/facial_recognition && ./setup.sh"
    end tell
    ```

3.  **Important Considerations for the Script**:
    *   **Path Specificity**: The provided script uses an absolute path (`/Users/lucelsby/Documents/repos/chwarel/facial_recognition`). If this application is set up on a different machine or the project is moved, this path **must be updated** in the AppleScript to reflect the new location of the `facial_recognition` project directory.
    *   **Permissions**: Ensure `setup.sh` is executable (`chmod +x setup.sh` in Terminal if not already done within the project's root directory).

4.  **Save as an Application**:
    *   In Script Editor, go to `File > Save...`.
    *   Provide a name for the application (e.g., "Run Facial Recognition Setup").
    *   Choose a location to save it.
    *   Crucially, change the **File Format** dropdown from `Script` to `Application`.
    *   Click `Save`.

5.  **Run the Application**:
    *   Navigate to where you saved the application in Finder.
    *   Double-click the newly created application icon. This should open a new Terminal window and automatically start executing the `setup.sh` script from the specified project directory.

This provides a user-friendly way to initiate the entire setup and server startup process without needing to manually open Terminal and type commands. If Terminal prompts for permissions (e.g., to control System Events or access files), these may need to be granted.

## VI. Limitations and Next Steps

As a Minimum Viable Product (MVP), the Facial Recognition Processing Pipeline has successfully demonstrated its core functionalities. However, to evolve into a robust, production-ready tool, several limitations need to be addressed and further development undertaken. This section outlines the key areas identified for improvement and future work.

### 6.1. Overview

The current version provides a solid foundation for local facial recognition processing. The next phases of development should focus on enhancing its reliability through rigorous testing with real-world data, optimizing performance and configurations, refining the processing workflow, and significantly improving the user experience based on end-user feedback.

### 6.2. Detailed Limitations and Corresponding Next Steps

1.  **Consent Data Integration & Testing**:
    *   **Limitation**: The MVP primarily uses a test sandbox environment (e.g., predefined consent folders uploaded to an S3 bucket or specific local structures). While this proves the concept, it doesn't reflect the diversity and potential inconsistencies of real-world consent collection systems.
    *   **Next Step**: Conduct robust testing with actual consent databases and image collections from production environments. This includes integrating with or mimicking real data sources from consent forms, testing with varying image qualities (lighting, resolution, pose), and ensuring the system can gracefully handle different consent data structures and formats. The goal is to validate and improve the reliability of consent profile ingestion and embedding generation under realistic conditions.

2.  **Watch Folder Functionality & Camera Card Compatibility**:
    *   **Limitation**: The watch folder system, which scans local folders for video files and monitors for new additions, has been tested with a limited set of video files and folder structures. Real-world camera cards from various manufacturers (Sony, RED, Arri, Canon, etc.) have diverse and often complex nested folder structures, which might not all be correctly interpreted by the current scanning logic.
    *   **Next Step**: Perform extensive testing with actual camera card copies from a wide range of professional cameras. This involves verifying that the system correctly identifies video files amidst other camera-generated files (metadata, proxies, LUTs, etc.) and accurately extracts necessary information regardless of the directory layout. The monitoring system also needs to be tested for reliability under conditions of large file transfers or intermittent connections.

3.  **Setup Script and Environment Validation**:
    *   **Limitation**: While the `setup.sh` script is comprehensive, its development involved iterative refinements. It has been tested on a developer machine but not yet validated on a completely fresh macOS system without pre-existing development tools or configurations.
    *   **Next Step**: Execute thorough end-to-end testing of the `setup.sh` script on a completely pristine macOS machine (ideally multiple versions of macOS and Apple Silicon hardware if possible). This will help identify any hidden dependencies, permission issues, or environment conflicts that might prevent a smooth first-time setup for new users. The goal is to ensure a reliable and error-free out-of-the-box experience.

4.  **Processing Configuration Optimization**:
    *   **Limitation**: Due to the limited availability of diverse, real-world test data during the MVP phase, the processing configurations (e.g., DeepFace model selection, detector backends, sensitivity thresholds, frame extraction rates, LUT application) are based on initial estimates and limited tests. It's not yet clear which configurations offer the optimal balance of speed and accuracy for various types_of footage.
    *   **Next Step**: Establish a systematic testing framework using a diverse dataset of video clips (different genres, lighting conditions, resolutions, number of faces). Experiment with various `card_configs` parameters to determine their impact on processing speed and the accuracy of face detection and matching. This includes evaluating the practical benefits and performance costs of applying LUTs during frame extraction. The outcome should be a set of recommended configurations or guidelines for users based on their specific needs.

5.  **Processing Performance Enhancements**:
    *   **Limitation**: The current processing pipeline, while functional, has several areas where performance could be improved. Operations like frame extraction, embedding generation for many faces, and matching against a large consent database can be time-consuming, especially for long clips or large projects.
    *   **Next Step**: Investigate and implement various performance optimization strategies. This could include:
        *   **Parallel Processing**: Explore parallelizing tasks at different levels (e.g., processing multiple clips concurrently, processing frames from a single clip in parallel, batching face detections/matches).
        *   **GPU Acceleration**: Ensure optimal use of GPU resources (e.g., `tensorflow-metal` on macOS) for DeepFace operations.
        *   **Algorithmic Optimizations**: Review and refine algorithms for efficiency.
        *   **Database Optimizations**: Ensure database queries for fetching embeddings and writing results are highly optimized.
        *   **Cloud-Based Processing (Optional Exploration)**: For very large-scale processing, consider exploring the feasibility of offloading computationally intensive tasks (like bulk embedding generation or large batch processing) to cloud services, while still maintaining local control and data management for other aspects.

6.  **Workflow Flexibility and Efficiency**:
    *   **Limitation**: The current workflow is largely sequential and somewhat rigid (ingest video -> extract all frames -> queue frames -> for each frame, detect all faces -> queue faces -> for each detected face, match against all consent faces). This can lead to redundant processing, especially if the same individuals appear repeatedly.
    *   **Next Step**: Refine the processing workflow to be more intelligent and efficient. Potential improvements include:
        *   **Incremental Processing/Change Detection**: Implement logic to identify and process only new or significantly changed content, rather than re-processing everything from scratch.
        *   **Duplicate Face Caching/Clustering**: For detected faces within a card or project, explore techniques to identify if a newly detected face is highly similar to one already processed (and potentially matched/unmatched). This could reduce redundant matching operations against the entire consent database for every single detected face instance.
        *   **Selective Re-processing**: Allow users more granular control to re-process specific stages (e.g., only re-run matching for a clip if consent profiles were updated, without re-extracting frames).

7.  **User Experience (UX) and User Interface (UI) Development**:
    *   **Limitation**: The web application approach and its UI/UX design were decided upon and implemented relatively late in the MVP development cycle. As such, it has not undergone rigorous user testing or detailed workflow analysis with target end-users.
    *   **Next Step**: Conduct dedicated UX research and usability testing sessions with the primary target users (e.g., Production Coordinators, Post-Production Supervisors, Assistant Editors). The goals are to:
        *   Understand their current workflows for managing footage and consent.
        *   Identify pain points in their existing processes.
        *   Gather feedback on the current application's UI, intuitiveness, and overall workflow.
        *   Use this feedback to significantly refine the UI design, navigation, information architecture, processing feedback mechanisms, and the format/content of generated reports to better suit their operational needs and improve overall efficiency and satisfaction.

## VII. Conclusion

The Facial Recognition Processing Pipeline MVP successfully establishes a functional foundation for locally managed video content analysis against consent profiles. It integrates a comprehensive technology stack, from database and backend processing to a user-facing frontend, and provides a clear setup path for macOS users. 

While the current iteration meets the core objectives of an MVP, the outlined limitations and next steps highlight the significant potential for growth. Future efforts focused on robust testing, performance optimization, workflow enhancements, and user-centric design will be critical in transforming this MVP into a polished, reliable, and indispensable tool for production teams.


