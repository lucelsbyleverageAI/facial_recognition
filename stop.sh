#!/bin/bash
# Stop script for the facial recognition project

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
print_ok() { echo -e "${GREEN}[OK]${NC} $1"; }

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo -e "║  ${RED}STOPPING ALL SERVICES${NC}                                        ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Find and kill the backend uvicorn server
if pgrep -f "uvicorn src.server:app" > /dev/null; then
    print_info "Stopping backend API server..."
    pkill -f "uvicorn src.server:app"
    print_ok "Backend API server stopped"
else
    print_info "Backend API server is not running"
fi

# Find and kill the frontend development server
if pgrep -f "next dev" > /dev/null; then
    print_info "Stopping frontend development server..."
    pkill -f "next dev"
    print_ok "Frontend development server stopped"
else
    print_info "Frontend development server is not running"
fi

# Stop Docker containers if they're running
if command -v docker &> /dev/null && docker ps -q &> /dev/null; then
    print_info "Stopping Docker containers..."
    if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ]; then
        docker compose down
        print_ok "Docker containers stopped"
    else
        print_info "No docker-compose.yml or docker-compose.yaml found in the current directory"
    fi
else
    print_info "Docker is not running or not installed"
fi

print_ok "All services stopped successfully" 