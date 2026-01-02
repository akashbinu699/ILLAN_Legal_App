# Ilan Legal App

This project aggregates the **Legal Manager Frontend** and the **FastAPI/MongoDB Backend** into a single repository.

## Project Structure

- `src/`: Frontend React application (based on LegalManagerFrontEnd).
- `backend/`: FastAPI backend with MongoDB and ChromaDB integration.
- `public/`: Public assets for frontend.
- `package.json`: Frontend dependencies and scripts.

## Prerequisites

- **Node.js** (v18+)
- **Python** (3.12+)
- **MongoDB** (running locally on port 27017)

## Setup

1.  **Install Frontend Dependencies**:
    ```bash
    npm install
    ```

2.  **Setup Backend**:
    ```bash
    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

## Running the Application

You need two terminals to run the full stack.

**Terminal 1: Backend**
```powershell
$env:PYTHONPATH = "C:\Users\Nannie AI\Desktop\Ilan_Legal_App"; cd backend; & ".\venv\Scripts\python.exe" -m uvicorn main:app --reload
```
*Backend runs on http://localhost:8000*

**Terminal 2: Frontend**
```powershell
npm run dev
```
*Frontend runs on http://localhost:5173* (or 5174 if busy)

## Features

- **Case Management**: View and manage legal cases.
- **RAG Pipeline**: Upload documents and query them using AI.
- **Draft Generation**: Auto-generate emails and letters based on case data.
- **MongoDB Integration**: Permanent storage for cases and drafts.
