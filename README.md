

## Backend

The backend is a FastAPI server that uses deep learning models for face analysis. It's managed using Poetry for dependencies and virtual environments.

### Prerequisites
- Python 3.10
- Poetry ([installation guide](https://python-poetry.org/docs/#installation))
- TBD for other dependencies: Docker, OpenCV, FFMPEG, etc.

### Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate Python 3.10 virtual environment:
   ```bash
   poetry env use py3.10
   poetry shell
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Run the development server:
   ```bash
   poetry run uvicorn src.server:app --reload
   ```

The API will be available at:
- API endpoint: http://localhost:8000
- API documentation: http://localhost:8000/docs

### Common Poetry Commands

- `poetry add <package>`: Add a package to the dependencies
- `poetry install`: Install the dependencies
- `poetry remove <package>`: Remove a package from the dependencies
- `poetry update`: Update the dependencies
- `poetry show`: Show the dependencies
- `poetry shell`: Activate the virtual environment
- `poetry run <command>`: Run a command with the dependencies
- `exit`: Exit the virtual environment

## Hasura

Hasura is a tool for managing the database. It's managed using Docker Compose.

### Prerequisites
- Docker Compose

### Setup

1. Start the Harura service using docker compose:
   ```bash
   docker compose up -d
   ```

2. For development, navigate to the hasura directory and start the console using Hasura CLI:
   ```bash
   cd hasura
   "C:\hasura\hasura.exe" console 
   or
   hasura console
   ```
