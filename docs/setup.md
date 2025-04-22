# Local Application Setup

## Quick Start: Automated Setup

The setup process for this application is fully automated using the `setup.sh` script provided in the project root. This script will check your system, install dependencies, and prepare everything you need to run the application.

### To Run the Setup Script:

1. **Open Terminal** and navigate to the project directory:
   ```bash
   cd /path/to/your/facial_recognition
   ```
2. **Make the script executable** (first time only):
   ```bash
   chmod +x setup.sh
   ```
3. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

The script will guide you through the process and print clear instructions if anything is missing or needs your attention.

---

## Optional: Create a Double-Click Setup App (MacOS)

For MacOS users who prefer a graphical experience, you can create a double-clickable app that runs the setup script in Terminal. This is optional and intended to make onboarding even easier for non-technical users.

### Step-by-Step Instructions

1. **Open Script Editor**
   - Open the built-in "Script Editor" app (find it via Spotlight or in Applications > Utilities).

2. **Paste the Template AppleScript**
   - Copy and paste the following AppleScript into a new Script Editor window:

     ```applescript
     tell application "Terminal"
         activate
         do script "cd '/path/to/your/project' && ./setup.sh"
     end tell
     ```
   - **Important:** Replace `/path/to/your/project` with the full path to the folder where you cloned this repository.

3. **Export as an Application**
   - Go to `File > Export`.
   - Set **File Format** to `Application`.
   - Name it something like `Run Setup.app`.
   - Save it to your Desktop or project folder.

4. **Make the Setup Script Executable**
   - In Terminal, run:
     ```bash
     chmod +x setup.sh
     ```

5. **Run the App**
   - Double-click `Run Setup.app` to launch Terminal and run the setup script.
   - If you see a security warning, right-click the app and choose "Open" the first time.

### Notes
- The AppleScript app is not portable between users unless they edit the path to match their own system.
- For security, MacOS may require you to approve the app the first time you run it.
- You can customize the app icon by right-clicking the app, choosing "Get Info", and dragging a new icon onto the info window.

---

## What Does the Setup Script Do?

The `setup.sh` script automates the following steps:

1. **Checks for Required System Tools:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/): For running Postgres and Hasura containers
   - [Python 3.10](https://www.python.org/downloads/): Required for the backend (recommended: [pyenv](https://github.com/pyenv/pyenv) or [Homebrew](https://brew.sh/))
   - [Poetry](https://python-poetry.org/docs/#installation): Python dependency and environment manager
   - [Node.js (v18+) & npm](https://nodejs.org/): Required for the frontend (Next.js)
   - [FFmpeg](https://ffmpeg.org/): For video processing
   - [Hasura CLI](https://hasura.io/docs/latest/hasura-cli/install-hasura-cli/): (optional, for advanced database/GraphQL management)

2. **Checks for Configuration Files:**
   - Ensures that `.env` files exist in the root, `backend`, and `frontend` directories
   - Verifies that all required environment variables are present in each `.env` file

3. **Installs Dependencies:**
   - Installs backend dependencies using Poetry
   - Installs frontend dependencies using npm

4. **Starts Docker Containers:**
   - Launches Postgres and Hasura services using Docker Compose

5. **Final Instructions:**
   - Prints clear instructions for starting the backend and frontend servers
   - Provides URLs for the Hasura console, backend API, and frontend app

If any required tool or configuration is missing, the script will print a helpful error message and stop, so you can address the issue before continuing.

---


