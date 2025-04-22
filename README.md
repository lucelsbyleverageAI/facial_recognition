# Facial Recognition Platform

This project is a monorepo for a facial recognition pipeline, including:
- **Backend**: FastAPI server with deep learning models (DeepFace, RetinaFace, TensorFlow, etc.)
- **Frontend**: (Optional) Next.js/React app for user interaction
- **Database**: Postgres managed by Hasura GraphQL Engine
- **Automation**: All setup and configuration is handled by a single script (`setup.sh`)

---

## Monorepo Structure

- `backend/` — FastAPI backend, Python, DeepFace, etc.
- `frontend/` — (Optional) Next.js frontend
- `hasura/` — Hasura metadata, migrations, and init scripts
- `docker-compose.yaml` — Orchestrates Postgres, Hasura, and data connector
- `.env`, `backend/.env`, `frontend/.env` — Environment configuration
- `setup.sh` — Unified setup script
- `docs/` — Additional documentation (see `docs/setup.md`)

---

## Prerequisites
- Python 3.10
- Poetry
- Docker & Docker Compose
- Node.js (if using frontend)
- Hasura CLI (optional, for advanced use)
- ffmpeg, git, etc.

---

## Environment Setup
- Copy `.env.example` files to `.env` in root, backend, and frontend directories.
- Fill in required variables: `HASURA_GRAPHQL_DATABASE_URL`, `POSTGRES_USER`, etc.

---

## Automated Setup (Recommended)

Run the following from the project root:

```bash
chmod +x setup.sh  # (first time only)
./setup.sh
```

This script will:
- Check/install all prerequisites
- Set up Python/Poetry and all dependencies
- Build TensorFlow dependencies for Apple Silicon if needed
- Install backend and frontend dependencies
- Start Docker containers (Postgres, Hasura)
- Initialize Hasura and automatically track all tables and relationships (including 1:1 relationships)
- Print URLs for backend, frontend, and Hasura console

See [`docs/setup.md`](docs/setup.md) for more details and troubleshooting.

---

## Backend Usage
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Frontend Usage
- (If present) http://localhost:3000

## Hasura Usage
- Console: http://localhost:8080
- All tables and relationships are tracked automatically by the setup script.

---

## Platform-Specific Notes
- For Apple Silicon (M1/M2/M3), see [`backend/MAC_SETUP.md`](backend/MAC_SETUP.md) for TensorFlow build instructions.
- For a graphical setup experience on Mac, see [`docs/setup.md`](docs/setup.md).

---

## Troubleshooting & Known Issues
- See [`docs/setup.md`](docs/setup.md) and [`backend/MAC_SETUP.md`](backend/MAC_SETUP.md) for common issues and solutions.

---

## Development & Contribution
- Add Python dependencies: `poetry add <package>`
- Add frontend dependencies: `npm install <package>`
- Run tests: `pytest` (backend)

---

## License
Add your license here.
