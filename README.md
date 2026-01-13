# Ilan Legal App

This project aggregates the **Legal Manager Frontend** and the **FastAPI/MongoDB Backend** into a single repository.

## Project Structure

- `frontend/`: Frontend React application.
- `backend/`: FastAPI backend with MongoDB and ChromaDB integration.
- `docs/`: Project documentation.
- `backend/scripts/`: Utility scripts for database management and debugging.

## Prerequisites

- **Node.js** (v18+)
- **Python** (3.12+)
- **MongoDB** (running locally on port 27017)

## Setup

1.  **Install Frontend Dependencies**:
    ```bash
    cd frontend
    npm install
    cd ..
    ```

2.  **Setup Backend**:
    ```bash
    # Create valid python environment if not exists
    python3 -m venv backend/venv
    source backend/venv/bin/activate  # or .\backend\venv\Scripts\Activate on Windows
    pip install -r backend/requirements.txt
    ```

## Running the Application

You can use the provided startup script for convenience:

**Mac/Linux:**
```bash
chmod +x RUN
./RUN
```

**Windows:**
```powershell
./run_app.ps1
```

**Manual Start:**

**Terminal 1: Backend**
Make sure to run from the project root.
```bash
python3 -m backend.main
```
*Backend runs on http://localhost:8000*

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```
*Frontend runs on http://localhost:5173* (or similar)
