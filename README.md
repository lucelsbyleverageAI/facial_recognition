# Facial Recognition Processing Pipeline

This project provides a comprehensive solution for processing video footage to detect human faces and match them against a pre-approved database of consent profiles. It's designed to run locally, primarily on macOS, to assist production teams in streamlining footage clearance and editing workflows.

The system features:
- **Automated Processing**: Handles video frame extraction, face detection, embedding generation, and matching against consent profiles.
- **Local File System Interaction**: Designed to scan local consent folders and monitor "watch folders" for new video media.
- **Web-Based UI**: A Next.js/React frontend for project management, configuration, monitoring, and results review.
- **Robust Backend**: A Python/FastAPI backend powers the core processing logic using DeepFace and FFmpeg.
- **GraphQL API**: Hasura provides a GraphQL layer over a PostgreSQL database for efficient data management.
- **Simplified Setup**: A comprehensive shell script (`setup.sh`) automates the entire environment setup on macOS.

---

## Technology Stack

- **Backend**: Python 3.10, FastAPI, DeepFace, FFmpeg, PostgreSQL, Hasura
- **Frontend**: Next.js (v14+ App Router), React, shadcn/ui, Tailwind CSS, React Query
- **Infrastructure**: Docker (for PostgreSQL & Hasura)
- **Automation**: Bash Scripting (`setup.sh`)

---

## Monorepo Structure

The project is organized as a monorepo:

- `backend/`: Contains the Python FastAPI application and related machine learning logic.
- `frontend/`: Contains the Next.js/React frontend application.
- `hasura/`: Holds Hasura configurations, including the full database migration (`full_migration.sql`) and initialization script (`init_hasura.sh`).
- `docs/`: Project documentation, including this README, the detailed MVP Wrap-up (`project_wrap_up.md`), and macOS specific setup notes.
- `docker-compose.yaml`: Defines and configures the Dockerized services (PostgreSQL, Hasura).
- `.env` (root): Main environment configuration for Docker services.
- `backend/.env`: Environment configuration for the backend application.
- `frontend/.env`: Environment configuration for the frontend application.
- `setup.sh`: The primary script for automating the complete local environment setup.

---

## Prerequisites

Before you begin, ensure you have the following installed on your macOS system:

- **Python 3.10**:
    - Check with `python3 --version`. If not 3.10.x, install via Homebrew: `brew install python@3.10` or use `pyenv`.
- **Poetry**: Python dependency manager.
    - Install if missing: `curl -sSL https://install.python-poetry.org | python3 -`
- **Docker & Docker Compose**: For running containerized services.
    - Install Docker Desktop for Mac from [docker.com](https://www.docker.com/products/docker-desktop/). Ensure Docker is running.
- **Node.js (LTS version recommended)**: For the frontend application.
    - Install if missing: `brew install node`
- **Homebrew**: macOS package manager.
    - Install if missing: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- **FFmpeg**: For video processing.
    - Install if missing: `brew install ffmpeg`
- **Git**: For cloning the repository.
    - Usually pre-installed on macOS. Check with `git --version`.
- **Hasura CLI (Optional)**: Only needed for advanced Hasura metadata management outside the automated script.
    - Install if needed: `brew install hasura-cli`

---

## Getting Started: Setup Instructions

Follow these steps to get the application running on your local machine:

### 1. Clone the Repository

If you haven't already, clone the project repository to your local machine:
```bash
git clone <repository_url> # Replace <repository_url> with the actual Git URL
cd facial_recognition # Or your project's root folder name
```

### 2. Configure Environment Variables

The application requires several environment variables for configuration. Example files are provided.

- **Root `.env` file**:
  Edit `.env` and fill in values for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `HASURA_GRAPHQL_DATABASE_URL`, and `HASURA_ADMIN_SECRET`.

- **Backend `.env` file**:
  Edit `backend/.env`. Ensure database connection details match the root `.env` and Hasura settings. You may also need to configure AWS credentials if using S3 for consent folders, though local paths are also supported.

- **Frontend `.env` file**:
  Edit `frontend/.env`. Ensure `NEXT_PUBLIC_HASURA_GRAPHQL_URL`, `NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL`, and `NEXT_PUBLIC_HASURA_ADMIN_SECRET` match your Hasura setup. `NEXT_PUBLIC_API_BASE_URL` should point to your backend (default `http://localhost:8000`).

### 3. Run the Automated Setup Script (`setup.sh`)

The `setup.sh` script is designed to automate the entire setup process.

```bash
chmod +x setup.sh  # Make the script executable (only need to do this once)
./setup.sh
```

This comprehensive script will perform the following actions:
- Verify essential prerequisites (and attempt to install some if missing via Homebrew).
- Configure Python environment using Poetry, installing all backend dependencies.
    - **Apple Silicon Note**: The script includes specific steps to build and install TensorFlow with Metal support (`tensorflow-metal`) and `tensorflow-io-gcs-filesystem` from source, which is critical for M1/M2/M3 Macs.
- Install frontend Node.js dependencies.
- Start Docker containers for PostgreSQL and Hasura using `docker-compose.yaml`.
- Initialize the Hasura GraphQL engine:
    - Waits for Hasura to be ready.
    - Runs the `hasura/full_migration.sql` to set up the database schema.
    - Runs `hasura/init_hasura.sh` to track all tables and configure relationships in Hasura.
- Start the backend FastAPI development server.
- Start the frontend Next.js development server.

The script will output logs and, upon successful completion, will display the URLs for accessing the application components.

For a detailed step-by-step explanation of what the `setup.sh` script does, refer to the "Local Setup" section in the [`docs/project_wrap_up.md`](docs/project_wrap_up.md#v-local-setup) document.

### 4. (Optional) macOS Clickable Setup Application

For a more user-friendly way to run the `setup.sh` script on macOS, you can create a clickable AppleScript application.
Refer to the instructions in [`docs/project_wrap_up.md#56-creating-a-clickable-setup-application-macos---optional`](docs/project_wrap_up.md#56-creating-a-clickable-setup-application-macos---optional) to create this. Remember to update the hardcoded project path in the AppleScript if your project is located elsewhere.

---

## Using the Application

Once the `setup.sh` script has completed successfully:

- **Frontend Application**: Access the web UI via your browser, typically at:
  `http://localhost:3000`
- **Backend API**: The FastAPI backend is usually available at:
  `http://localhost:8000`
- **Backend API Documentation (Swagger UI)**:
  `http://localhost:8000/docs`
- **Hasura Console**: Manage your database and GraphQL API via the Hasura console:
  `http://localhost:8080` (Use the `HASURA_ADMIN_SECRET` from your `.env` file to log in)

---

## Troubleshooting & Advanced Setup

- **Detailed Setup Explanation**: For an in-depth understanding of the local setup process, Docker services, and the `setup.sh` script's operations, please consult the "V. Local Setup" section within the [`docs/project_wrap_up.md`](docs/project_wrap_up.md#v-local-setup) document.
- **Apple Silicon (M1/M2/M3) TensorFlow Issues**: If you encounter specific problems with TensorFlow or related libraries on Apple Silicon that the `setup.sh` script doesn't resolve, refer to the manual build and troubleshooting guide: [`backend/MAC_SETUP.md`](backend/MAC_SETUP.md).
- **Docker Issues**: Ensure Docker Desktop is running and has sufficient resources allocated. Check Docker logs if services fail to start: `docker compose logs -f <service_name>` (e.g., `docker compose logs -f postgres`).
- **Permissions**: Ensure `setup.sh` and any scripts it calls have execute permissions (`chmod +x <script_name>`).

---

## Development & Contribution

- **Adding Python Dependencies (Backend)**:
  Navigate to the `backend/` directory and use Poetry:
  `poetry add <package_name>`
- **Adding Frontend Dependencies**:
  Navigate to the `frontend/` directory and use npm:
  `npm install <package_name>`
- **Running Backend Tests**:
  (Assuming tests are configured) Navigate to `backend/` and run:
  `pytest`
