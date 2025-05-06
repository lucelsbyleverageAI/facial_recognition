#!/bin/bash
# Mini setup script for development: just runs the services

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_ok() { echo -e "${GREEN}[OK]${NC}   $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Start Docker services if Docker is running
if command -v docker &> /dev/null; then
    if docker info &>/dev/null; then
        print_ok "Docker is running. Starting Docker services..."
        docker compose up -d
    else
        print_warn "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
else
    print_warn "Docker not found. Skipping Docker setup."
fi

# Start backend server
cd "$SCRIPT_DIR/backend"
print_ok "Starting backend server at http://localhost:8000 ..."
poetry run uvicorn src.server:app --reload > /tmp/backend-server.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Start frontend server
cd "$SCRIPT_DIR/frontend"
print_ok "Starting frontend server at http://localhost:3000 ..."
npm run dev

# Cleanup: stop backend server when frontend stops
echo "Frontend server stopped, stopping backend server..."
kill $BACKEND_PID 