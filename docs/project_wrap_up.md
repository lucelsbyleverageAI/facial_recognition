# Facial Recognition Processing Pipeline - Project Wrap-up (MVP)

## Preamble

This document provides a comprehensive overview of the Minimum Viable Product (MVP) for the Facial Recognition Processing Pipeline. It details the application's purpose, architecture, core functionalities, local setup procedures, and outlines a roadmap for future development and enhancements. The goal is to offer a clear understanding of the system as it stands at the conclusion of the MVP phase.

## I. Application Overview

### 1.1. Purpose and Functionality

The Facial Recognition Processing Pipeline is a locally-run application designed to process video footage to detect human faces and match them against a pre-approved database of consent profiles. Its primary purpose is to assist production teams in efficiently identifying individuals within footage for whom consent may be missing or requires verification. This streamlines the clearance and editing workflows, ensuring compliance and reducing manual review time.

The application automates several key tasks:
-   Discovery and organization of projects and consent profiles from local folder structures.
-   Management of "cards" (representing camera media/batches of footage).
-   Monitoring of user-defined local "watch folders" for new video clips.
-   Extraction of frames from video clips.
-   Detection of faces within these frames.
-   Generation of facial embeddings for both consent images and detected faces.
-   Matching of detected faces against the consent database.
-   Presentation of processing results and generation of reports indicating matched and unmatched faces.

### 1.2. High-Level Workflow

The typical user journey through the application follows these main stages:

1.  **Project Setup**: The application scans pre-defined consent folder locations to identify available projects. Consent profiles and associated images within these project folders are automatically detected and registered.
2.  **Card Setup**: Within a selected project, users can create new "cards" or select existing ones. Each card represents a unit of footage (e.g., a camera card) and has an associated processing configuration.
3.  **Watch Folder Configuration**: For each card, the user defines one or more local folder paths ("watch folders") that the system will scan and monitor for video files related to that card.
4.  **Initial Scan & Monitoring**: The system performs an initial scan of the configured watch folders to identify existing video clips. After the initial scan, users can activate monitoring, which allows the system to automatically detect and add new clips as they are copied into the watch folder.
5.  **Processing**: Selected clips are queued for processing. This involves:
    *   Generating embeddings for any new or updated consent images.
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
*   **`.env.example` files (root, backend, frontend)**: Provide templates for environment variable configuration.

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
