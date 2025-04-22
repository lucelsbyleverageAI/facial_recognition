#!/bin/bash
# Facial Recognition Project Setup Script for macOS on Apple Silicon
# This script automates the setup process for the entire facial recognition project

# Set error handling
set -e

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_ok() { echo -e "${GREEN}[OK]${NC}   $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_err() { echo -e "${RED}[ERROR]${NC} $1"; }
print_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

check_env_vars() {
  local file=$1; shift; local missing=0
  echo "Checking required variables in $file..."
  for var in "$@"; do
    if grep -qE "^${var}=.+" "$file"; then
      print_ok "✓ $var found"
    else
      print_err "✗ Missing $var in $file"
      missing=1
    fi
  done
  
  if (( missing )); then
    echo -e "${YELLOW}Please update the $file file with the required variables${NC}"
    return 1
  else
    print_ok "All required variables present in $file"
    return 0
  fi
}

echo -e "${GREEN}==== Facial Recognition Project Setup ====${NC}"
echo -e "Setting up the environment for Apple Silicon (M1/M2/M3)"

# Check if Python 3.10 is installed
if ! command -v python3.10 &> /dev/null; then
    print_err "Python 3.10 is required but not found"
    echo "Please install Python 3.10 using pyenv or homebrew:"
    echo "  brew install python@3.10   or"
    echo "  pyenv install 3.10.x"
    exit 1
fi
print_ok "Python 3.10 is installed"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_info "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    print_ok "Poetry installed"
else
    print_ok "Poetry is installed"
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    print_info "ffmpeg not found. Installing ffmpeg..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
        print_ok "ffmpeg installed via Homebrew"
    else
        print_err "Homebrew not found. Please install ffmpeg manually"
        echo "Install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "Then run: brew install ffmpeg"
        exit 1
    fi
else
    print_ok "ffmpeg is installed"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_info "Docker not found. Installing Docker..."
    if command -v brew &> /dev/null; then
        brew install --cask docker
        print_warn "Docker Desktop was installed, but you need to open it manually to complete setup"
        echo "Please open Docker Desktop from your Applications folder after this script completes"
    else
        print_err "Homebrew not found. Please install Docker manually:"
        echo "Download Docker Desktop from https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
else
    print_ok "Docker is installed"
fi

# Check if Hasura CLI is installed
if ! command -v hasura &> /dev/null; then
    print_info "Hasura CLI not found. Installing Hasura CLI..."
    if command -v brew &> /dev/null; then
        brew install hasura-cli
        print_ok "Hasura CLI installed via Homebrew"
    else
        print_warn "Installing Hasura CLI using npm..."
        npm install --global hasura-cli
    fi
else
    print_ok "Hasura CLI is installed"
fi

# Check if Node.js is installed (for frontend)
if ! command -v node &> /dev/null; then
    print_info "Node.js not found. Installing Node.js..."
    if command -v brew &> /dev/null; then
        brew install node
        print_ok "Node.js installed via Homebrew"
    else
        print_err "Homebrew not found. Please install Node.js manually"
        echo "Install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "Then run: brew install node"
        exit 1
    fi
else
    print_ok "Node.js is installed"
fi

# Navigate to the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check environment files
echo -e "${GREEN}==== Checking Environment Files ====${NC}"

# Check root .env file
if [ -f .env ]; then
    check_env_vars ".env" "POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "HASURA_GRAPHQL_DATABASE_URL" "HASURA_ADMIN_SECRET" "HASURA_GRAPHQL_URL"
    
    # Check for Hasura endpoint environment variable
    if ! grep -q "HASURA_GRAPHQL_ENDPOINT" .env; then
        echo "Adding HASURA_GRAPHQL_ENDPOINT to .env..."
        echo "HASURA_GRAPHQL_ENDPOINT=http://localhost:8080" >> .env
    fi
else
    if [ -f .env.example ]; then
        print_info "Creating .env file from .env.example..."
        cp .env.example .env
        
        # Add Hasura endpoint if not present
        if ! grep -q "HASURA_GRAPHQL_ENDPOINT" .env; then
            echo "Adding HASURA_GRAPHQL_ENDPOINT to .env..."
            echo "HASURA_GRAPHQL_ENDPOINT=http://localhost:8080" >> .env
        fi
        
        print_warn "Please update the .env file with the required variables"
    else
        print_err "No .env or .env.example found in the root directory. Please create one manually."
    fi
fi

# Check backend .env file
if [ -f backend/.env ]; then
    check_env_vars "backend/.env" "POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "DATABASE_URL" "HASURA_ADMIN_SECRET" "HASURA_GRAPHQL_URL" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "AWS_REGION" "AWS_BUCKET_NAME"
else
    if [ -f backend/.env.example ]; then
        print_info "Creating backend/.env file from backend/.env.example..."
        cp backend/.env.example backend/.env
        print_warn "Please update the backend/.env file with the required variables"
    else
        print_err "No .env or .env.example found in the backend directory. Please create one manually."
    fi
fi

# Check frontend .env file
if [ -f frontend/.env ]; then
    check_env_vars "frontend/.env" "NEXT_PUBLIC_HASURA_GRAPHQL_URL" "NEXT_PUBLIC_HASURA_GRAPHQL_WS_URL" "NEXT_PUBLIC_HASURA_ADMIN_SECRET" "NEXT_PUBLIC_API_BASE_URL"
else
    if [ -f frontend/.env.example ]; then
        print_info "Creating frontend/.env file from frontend/.env.example..."
        cp frontend/.env.example frontend/.env
        print_warn "Please update the frontend/.env file with the required variables"
    else
        print_err "No .env or .env.example found in the frontend directory. Please create one manually."
    fi
fi

echo -e "${GREEN}==== Setting up Backend ====${NC}"

# Navigate to the backend directory
cd "$SCRIPT_DIR/backend"

# Create and activate a virtual environment
print_info "Creating and activating Python virtual environment..."

# Configure Poetry to use Python 3.10
echo "Configuring Poetry to use Python 3.10..."
poetry env use python3.10

# Check if virtual environment exists and create if needed
if ! poetry env info -p &> /dev/null; then
    echo "Creating new Poetry virtual environment with Python 3.10..."
    poetry env use python3.10
else
    echo "Poetry virtual environment already exists"
fi

# Get the path to the Poetry virtual environment
VENV_PATH=$(poetry env info -p)
if [ -z "$VENV_PATH" ]; then
    print_err "Failed to get Poetry virtual environment path"
    exit 1
fi

print_ok "Virtual environment created at $VENV_PATH"

# Get the Python executable from the virtual environment
PYTHON_BIN="$VENV_PATH/bin/python"
PIP_BIN="$VENV_PATH/bin/pip"

# Step 1: Install wheel package
print_info "Installing wheel package..."
$PIP_BIN install wheel

# Step 2: Build tensorflow-io-gcs-filesystem from source
print_info "Building tensorflow-io-gcs-filesystem from source..."
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

echo "Cloning tensorflow-io repository..."
git clone https://github.com/tensorflow/io.git tensorflow-io
cd tensorflow-io

echo "Building tensorflow-io-gcs-filesystem wheel..."
$PYTHON_BIN setup.py -q bdist_wheel --project tensorflow_io_gcs_filesystem

echo "Installing the built wheel..."
cd dist
WHEEL_FILE=$(ls tensorflow_io_gcs_filesystem-*.whl)
$PIP_BIN install "$WHEEL_FILE" --force-reinstall

# Return to the backend directory
cd "$SCRIPT_DIR/backend"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TMP_DIR"

# Step 3: Install TensorFlow and related packages
print_info "Installing TensorFlow and dependencies..."
# First uninstall any existing TensorFlow-related packages
$PIP_BIN uninstall -y tensorflow tensorflow-estimator tensorflow-io-gcs-filesystem keras tensorboard tf-keras 2>/dev/null || true

# Install TensorFlow and Metal support
$PIP_BIN install "tensorflow==2.19.0" "tensorflow-metal" 

# Set environment variables for TensorFlow with Metal
export TF_CPP_MIN_LOG_LEVEL=0  # Show all logs
export TF_FORCE_GPU_ALLOW_GROWTH=true

# Now use Poetry to install the rest
print_info "Installing remaining dependencies with Poetry..."
# Clean up lock file to avoid conflicts
if [ -f poetry.lock ]; then
    rm -f poetry.lock
fi
# Use --no-interaction to avoid prompts
poetry lock --no-interaction
poetry install --no-interaction

# Step 4: Verify installation
print_info "Verifying installation..."
if $PYTHON_BIN -c "import tensorflow; import deepface; import retinaface; print('Success!')" 2>/dev/null | grep -q "Success!"; then
    print_ok "Facial recognition libraries installed successfully!"
else
    print_warn "Verification failed, but installation may still have succeeded"
fi

# Setup frontend if Node.js is installed
if command -v node &> /dev/null; then
    echo -e "${GREEN}==== Setting up Frontend ====${NC}"
    cd "$SCRIPT_DIR/frontend"
    
    # Check if .env file exists, create from example if not
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            echo "Creating .env file from .env.example..."
            cp .env.example .env
            print_warn "Don't forget to update the environment variables in .env"
        else
            print_warn "No .env.example found. You'll need to create a .env file manually."
        fi
    fi
    
    # Install dependencies
    if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
        print_info "Installing frontend dependencies..."
        if [ -f "package-lock.json" ]; then
            npm ci
        else
            npm install
        fi
    else
        print_ok "Frontend dependencies are already installed"
    fi
fi

# Return to project root
cd "$SCRIPT_DIR"

# Check Docker services
if command -v docker &> /dev/null; then
    echo -e "${GREEN}==== Setting up Docker Environment ====${NC}"
    
    # Check if docker is running
    if ! docker info &>/dev/null; then
        print_warn "Docker is not running. Please start Docker Desktop first."
        echo "After starting Docker Desktop, you can run docker-compose manually:"
        echo "  docker compose up -d"
    else
        print_info "Docker is running. Starting Docker services..."
        docker compose down
        
        # Remove persistent data to ensure a clean state
        print_info "Cleaning up previous data..."
        docker volume rm facial_recognition_postgres_data 2>/dev/null || true
        
        # Start services
        docker compose up -d
        print_ok "Docker services started"
        
        # Initialize Hasura database and metadata
        echo -e "${GREEN}==== Initializing Hasura Database ====${NC}"
        print_info "Waiting for Hasura to be ready and tracking tables..."
        
        # Run the Hasura initialization script
        "$SCRIPT_DIR/hasura/init_hasura.sh"
        
        if [ $? -eq 0 ]; then
            print_ok "Hasura database initialized successfully!"
        else
            print_warn "Failed to fully initialize Hasura database. Some features may not work correctly."
        fi
    fi
else
    print_warn "Docker not found. Skipping Docker setup."
    echo "If you want to use Docker, please install Docker Desktop for Mac."
fi

echo -e "${GREEN}==== Setup Complete! Starting Servers ====${NC}"

# Return to the backend directory to start the server
cd "$SCRIPT_DIR/backend"

# Display a message about the server URL with clear formatting and borders
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo -e "║  ${GREEN}STARTING BACKEND SERVER${NC}                                      ║"
echo "║                                                                ║"
echo -e "║  Backend API:       ${YELLOW}http://localhost:8000${NC}                      ║"
echo -e "║  API Documentation: ${YELLOW}http://localhost:8000/docs${NC}                 ║"
echo "║                                                                ║"
echo -e "║  Press ${YELLOW}Ctrl+C${NC} to stop the server                               ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Start the backend server in the background
poetry run uvicorn src.server:app --reload > /tmp/backend-server.log 2>&1 &
BACKEND_PID=$!

# Add a short delay to make sure the backend server has started
sleep 3

# Now start the frontend
cd "$SCRIPT_DIR/frontend"

# Display a message about the frontend URL
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo -e "║  ${GREEN}STARTING FRONTEND SERVER${NC}                                     ║"
echo "║                                                                ║"
echo -e "║  Frontend URL:      ${YELLOW}http://localhost:3000${NC}                      ║"
echo "║                                                                ║"
echo -e "║  Press ${YELLOW}Ctrl+C${NC} to stop all servers                              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Add a short delay to make sure the message is visible
sleep 2

# Start the frontend server
npm run dev

# If we get here, the frontend server was stopped, so we should kill the backend server too
echo "Frontend server stopped, stopping backend server..."
kill $BACKEND_PID