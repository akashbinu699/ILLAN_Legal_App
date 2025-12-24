# LegalEase CAF Manager - Legal Case Management with RAG Pipeline

<div align="center">

**A comprehensive legal case management application for handling CAF (Caisse d'Allocations Familiales) administrative appeals, featuring AI-powered document analysis, RAG (Retrieval-Augmented Generation) pipeline, and automated legal document generation.**

[![React](https://img.shields.io/badge/React-19.2.0-blue)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.2-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-green)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-teal)](https://fastapi.tiangolo.com/)

</div>

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [Application Workflow](#application-workflow)
9. [Architecture Deep Dive](#architecture-deep-dive)
10. [Testing](#testing)
11. [Project Structure](#project-structure)
12. [Troubleshooting](#troubleshooting)
13. [Documentation](#documentation)

---

## 🎯 Overview

### What is LegalEase CAF Manager?

LegalEase CAF Manager is a full-stack web application designed specifically for lawyers handling administrative appeals against the CAF (French Family Allowance Fund). The application streamlines the entire case management process from initial client intake through document generation and case review.

### Who is it for?

- **Lawyers**: Manage cases, review AI-generated documents, query case documents using RAG, and export professional legal documents
- **Clients**: Submit cases through a user-friendly form with document uploads

### Key Capabilities

- **Intelligent Case Analysis**: AI automatically detects legal stage (CONTROL, RAPO, LITIGATION) and identifies relevant benefits
- **Document Processing**: Automated PDF extraction, text cleaning, and vectorization
- **RAG Pipeline**: Advanced retrieval-augmented generation for querying case documents with citations
- **Document Generation**: AI-powered email and appeal draft generation
- **Case Management**: Professional dashboard for lawyers to review, edit, and manage cases

---

## ✨ Features

### For Clients
- ✅ Simple, intuitive form interface
- ✅ Drag-and-drop file upload (PDFs, images)
- ✅ Real-time form validation
- ✅ Secure submission with consent management
- ✅ Immediate confirmation of submission

### For Lawyers
- ✅ **Case Dashboard**: View all cases with status indicators
- ✅ **Case Details**: Complete case information with prestation tags
- ✅ **Document Viewing**: View uploaded files directly in browser
- ✅ **AI-Generated Drafts**: 
  - Email drafts for client communication
  - Appeal documents (RAPO, Tribunal submissions)
- ✅ **Editable Prompts**: Customize AI generation instructions
- ✅ **Document Export**: 
  - Email drafts as Outlook (.eml) files
  - Appeal documents as Word (.doc) files
- ✅ **RAG Query Interface**: Ask questions about case documents with AI-powered answers and citations
- ✅ **Stage Management**: Change legal stages with automatic draft regeneration

### Technical Features
- ✅ **Dual-Mode Operation**: Backend API mode (with RAG) or direct Gemini API mode
- ✅ **Persistent Storage**: SQLite for metadata, ChromaDB for vector embeddings
- ✅ **Async Processing**: Background document processing pipeline
- ✅ **Error Handling**: Graceful degradation and user-friendly error messages

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         React Frontend (Port 3000)                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ Client Form  │  │ Lawyer Dash  │  │ Query UI    │   │   │
│  │  └──────┬───────┘  └──────┬──────┘  └──────┬───────┘   │   │
│  └─────────┼──────────────────┼─────────────────┼──────────┘   │
│            │                  │                 │              │
│            │ HTTP/REST        │                 │              │
└────────────┼──────────────────┼─────────────────┼──────────────┘
             │                  │                 │
             ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Python Backend (Port 8000)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI REST API                             │  │
│  │  POST /api/submit  │  GET /api/cases  │  POST /api/query │  │
│  └──────────┬──────────────────┬──────────────────┬──────────┘  │
│             │                  │                  │             │
│  ┌──────────▼──────────┐  ┌────▼─────┐  ┌────────▼─────────┐ │
│  │ Processing Pipeline │  │ SQLite   │  │  RAG Pipeline     │ │
│  │  - Document Extract  │  │ Database │  │  - Retrieval     │ │
│  │  - Text Cleaning    │  │          │  │  - Generation     │ │
│  │  - Vectorization    │  │          │  │  - Critique       │ │
│  └──────────┬──────────┘  └───────────┘  └────────┬──────────┘ │
│             │                                      │            │
│  ┌──────────▼──────────┐              ┌───────────▼──────────┐ │
│  │     ChromaDB        │              │   LLM Services       │ │
│  │  (Vector Store)     │              │  - Groq/OpenAI       │ │
│  └─────────────────────┘              └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

**Frontend (React/TypeScript)**
- **App.tsx**: Main orchestrator, view management, state management
- **ClientForm.tsx**: Client intake form with validation
- **LawyerDashboard.tsx**: Case management interface
- **QueryInterface.tsx**: RAG query interface
- **FormInput.tsx**: Reusable form component

**Backend (Python/FastAPI)**
- **main.py**: FastAPI server and routing
- **api/routes.py**: REST API endpoints
- **services/**: Business logic services
  - `processing_pipeline.py`: Document processing orchestration
  - `rag_pipeline.py`: LangGraph RAG workflow
  - `document_processor.py`: PDF/image extraction
  - `embedding_service.py`: Vector embeddings
  - `retrieval_service.py`: Hybrid search & re-ranking
  - `llm_service.py`: LLM inference
  - And more...

**Data Layer**
- **SQLite**: Case metadata, submissions, documents, chunks, queries
- **ChromaDB**: Vector embeddings for semantic search

---

## 🛠️ Technology Stack

### Frontend
- **React 19.2.0**: UI framework
- **TypeScript 5.8.2**: Type safety
- **Vite 6.2.0**: Build tool and dev server
- **Tailwind CSS**: Styling (via CDN)
- **Font Awesome 6.0.0**: Icons

### Backend
- **Python 3.12+**: Runtime
- **FastAPI 0.109.0**: Web framework
- **Uvicorn**: ASGI server
- **SQLAlchemy 2.0.25**: ORM
- **SQLite**: Relational database
- **ChromaDB 0.4.22**: Vector database

### AI & ML Services
- **Google Gemini 2.5 Flash**: Frontend AI (case analysis, draft generation)
- **Groq API**: Backend LLM (fast inference)
- **OpenAI API**: Fallback LLM
- **Nomic Embed Text v1.5**: Embeddings (32k context)
- **Cohere**: Re-ranking service

### Document Processing
- **Unstructured.io**: PDF extraction and OCR
- **MarkItDown**: Text cleaning and standardization

### Orchestration
- **LangGraph 0.0.26**: RAG pipeline orchestration
- **LangChain 0.1.6**: LLM framework

### Utilities
- **RapidFuzz**: Duplicate detection
- **Pydantic**: Data validation

---

## 📦 Installation & Setup

### Prerequisites

1. **Node.js** (v18 or higher)
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version`

2. **Python** (3.12 or higher)
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python3 --version`

3. **API Keys** (see [Configuration](#configuration) section)
   - Google Gemini API key
   - Gmail API credentials (optional, for email collection)
   - Groq API key (for backend LLM)
   - Cohere API key (for re-ranking, optional)

### Step 1: Clone or Navigate to Project

```bash
cd "/Users/artemprokhorov/Desktop/Jobs : Work/Nanny AI/Ilan_Legal_App"
```

### Step 2: Install Frontend Dependencies

```bash
npm install
```

This installs:
- React and React DOM
- TypeScript
- Vite and plugins
- Google Gemini SDK

### Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs all Python packages including:
- FastAPI and Uvicorn
- SQLAlchemy and database drivers
- AI/ML libraries (LangChain, LangGraph, ChromaDB, etc.)
- Document processing tools

**Note**: Some dependencies may require additional system libraries. If you encounter errors:
- **ChromaDB**: May need `libsqlite3-dev` (Linux) or Xcode Command Line Tools (Mac)
- **Unstructured.io**: May need additional system dependencies

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini AI (Required for frontend)
GEMINI_API_KEY=AIzaSyYourKeyHere

# Gmail API (Optional - for email collection)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Database Paths (Defaults - usually no changes needed)
DATABASE_PATH=./data/database.db
CHROMA_DB_PATH=./data/chroma_db

# LLM (Required for backend RAG pipeline)
GROQ_API_KEY=gsk_your_groq_key_here
# OR use OpenAI as fallback:
# OPENAI_API_KEY=sk-your_openai_key_here

# Embedding Model (Default - usually no changes needed)
EMBEDDING_MODEL=nomic-embed-text-v1.5

# Re-ranker (Optional - improves search quality)
RERANKER_API_KEY=your_cohere_key_here
```

**📖 For detailed API key setup instructions, see:**
- [`documentation/now/API_KEYS_SETUP_GUIDE.md`](documentation/now/API_KEYS_SETUP_GUIDE.md)

### Step 5: Verify Installation

**Test Frontend:**
```bash
npm run dev
# Should start on http://localhost:3000
```

**Test Backend:**
```bash
cd backend
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Should start on http://localhost:8000
# Visit http://localhost:8000/docs for API documentation
```

---

## ⚙️ Configuration

### Environment Variables Explained

| Variable | Required | Description | Where to Get It |
|----------|----------|-------------|-----------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini AI for frontend features | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GROQ_API_KEY` | ✅ Yes* | Backend LLM for RAG pipeline | [Groq Console](https://console.groq.com/keys) |
| `OPENAI_API_KEY` | ⚠️ Fallback | Alternative LLM if Groq unavailable | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `RERANKER_API_KEY` | ⚠️ Optional | Cohere API for search re-ranking | [Cohere Dashboard](https://dashboard.cohere.com/api-keys) |
| `GMAIL_CLIENT_ID` | ⚠️ Optional | Gmail API OAuth client ID | [Google Cloud Console](https://console.cloud.google.com/) |
| `GMAIL_CLIENT_SECRET` | ⚠️ Optional | Gmail API OAuth client secret | [Google Cloud Console](https://console.cloud.google.com/) |
| `GMAIL_REFRESH_TOKEN` | ⚠️ Optional | Gmail API refresh token | Via authentication flow |
| `DATABASE_PATH` | ❌ No | SQLite database file path | Default: `./data/database.db` |
| `CHROMA_DB_PATH` | ❌ No | ChromaDB storage directory | Default: `./data/chroma_db` |
| `EMBEDDING_MODEL` | ❌ No | Embedding model identifier | Default: `nomic-embed-text-v1.5` |

*Required if using backend RAG features. Frontend can work with just GEMINI_API_KEY.

### Frontend Environment Variables

The frontend also needs to know where the backend is:

Create `.env.local` in project root (optional, defaults to localhost:8000):
```env
VITE_API_URL=http://localhost:8000/api
```

---

## 🚀 Running the Application

### Development Mode

#### Terminal 1: Start Backend

```bash
cd backend
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
✓ Database initialized
INFO:     Application startup complete.
```

**Verify Backend:**
- Visit http://localhost:8000 - Should see API info
- Visit http://localhost:8000/health - Should return `{"status":"healthy"}`
- Visit http://localhost:8000/docs - FastAPI interactive documentation

#### Terminal 2: Start Frontend

```bash
npm run dev
```

**Expected Output:**
```
  VITE v6.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
```

**Verify Frontend:**
- Visit http://localhost:3000 - Should see the application

### Production Build

**Build Frontend:**
```bash
npm run build
# Output in dist/ directory
```

**Run Backend (Production):**
```bash
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 🔄 Application Workflow

### Complete User Journey

#### 1. Client Submission Workflow

```
┌─────────────┐
│   Client    │
│  Fills Form │
└──────┬──────┘
       │
       │ 1. Enters email, phone, description
       │ 2. Uploads CAF documents (PDF/images)
       │ 3. Checks consent boxes
       │ 4. Clicks "Connaître mes chances de succès"
       ▼
┌─────────────────┐
│  Frontend       │
│  Validation     │
└──────┬──────────┘
       │
       │ ✓ Validates required fields
       │ ✓ Converts files to base64
       │ ✓ Sends to backend API
       ▼
┌─────────────────┐
│  Backend API    │
│  /api/submit    │
└──────┬──────────┘
       │
       │ 1. Generates case ID (CAS-YYYY-XXX)
       │ 2. Creates submission record
       │ 3. Stores in SQLite
       │ 4. Triggers background processing
       │ 5. Returns case info
       ▼
┌─────────────────┐
│  Frontend       │
│  Success View   │
└─────────────────┘
```

**What Happens Behind the Scenes:**

1. **Immediate Response**: Client sees success screen
2. **Background Processing** (async):
   - Document extraction (PDF → text)
   - Text cleaning and standardization
   - Vectorization with Late Chunking
   - Storage in ChromaDB
   - Status updated to "PROCESSING" → "REVIEWED"

#### 2. Backend Processing Pipeline (RAG)

When a case is submitted, the backend automatically processes it:

```
Submission Received
       │
       ▼
┌──────────────────────┐
│ Step 1: Extract Text │
│ - PDF → Text         │
│ - Images → OCR       │
│ - Tables → JSON      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Step 2: Clean Text   │
│ - Remove artifacts   │
│ - Normalize format   │
│ - Preserve structure │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Step 3: Chunk        │
│ - Split into chunks  │
│ - Preserve context   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Step 4: Embed        │
│ - Late Chunking      │
│ - Full doc context   │
│ - Chunk embeddings   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Step 5: Store        │
│ - ChromaDB vectors   │
│ - Metadata tracking  │
│ - SQLite references  │
└──────────────────────┘
```

#### 3. Lawyer Dashboard Workflow

```
┌─────────────┐
│   Lawyer    │
│  Opens App  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Lawyer View    │
│  - Case List    │
│  - Case Details │
└──────┬──────────┘
       │
       ├─→ View Cases
       │   - See all submissions
       │   - Filter by status
       │   - Click to select
       │
       ├─→ Review Case
       │   - Read description
       │   - View documents
       │   - Check prestations
       │
       ├─→ Edit Drafts
       │   - Email draft (A4 editor)
       │   - Appeal draft (A4 editor)
       │   - Auto-save on blur
       │
       ├─→ Regenerate
       │   - Edit prompts
       │   - Click "Régénérer"
       │   - New AI-generated content
       │
       ├─→ Export Documents
       │   - Email → .eml file
       │   - Appeal → .doc file
       │
       └─→ RAG Query
           - Ask questions
           - Get AI answers
           - See citations
```

#### 4. RAG Query Workflow

When a lawyer asks a question using the RAG Query interface:

```
┌─────────────┐
│   Query     │
│  "What is   │
│  the case   │
│  about?"    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Retrieval      │
│  - Embed query   │
│  - Vector search │
│  - Get top 10    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Re-ranking     │
│  - Cohere API   │
│  - Top 10 → 3   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Generation     │
│  - LLM creates  │
│    answer        │
│  - With citations│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Critique       │
│  - Second LLM    │
│    validates     │
│  - Checks cites  │
└──────┬──────────┘
       │
       ├─→ Accept → Return Answer
       │
       └─→ Revise → Loop back (max 3x)
```

---

## 🏛️ Architecture Deep Dive

### Frontend Architecture

#### Component Hierarchy

```
App.tsx (Root)
├── Navigation Bar
│   ├── View Switcher (Client/Lawyer)
│   └── Case Count Badge
│
├── Client View
│   └── ClientForm
│       ├── Contact Section (FormInput x2)
│       ├── File Upload (drag-and-drop)
│       ├── Description Textarea
│       ├── Consent Checkboxes
│       └── Submit Button
│
├── Success View
│   └── Confirmation Screen
│
└── Lawyer View
    └── LawyerDashboard
        ├── Case List Sidebar
        ├── Case Detail View
        │   ├── Header (info, files, prestations)
        │   ├── Stage Selector
        │   ├── Tab Navigation
        │   ├── Details Tab
        │   ├── Email Tab (with QueryInterface)
        │   ├── Appeal Tab
        │   └── RAG Query Tab
        └── Export Controls
```

#### State Management

**Global State (App.tsx)**
- `currentView`: Current view (CLIENT, LAWYER, SUCCESS)
- `cases`: Array of all cases
- `useBackend`: Toggle for backend vs direct Gemini mode

**Local State (Components)**
- Form data, validation errors, file lists
- Selected case, active tab, editing states
- Query input and responses

**Data Flow:**
```
User Action
    │
    ▼
Component Handler
    │
    ▼
API Call (if useBackend)
    │
    ▼
State Update (setCases)
    │
    ▼
Re-render Components
```

### Backend Architecture

#### Service Layer Structure

```
backend/services/
├── processing_pipeline.py    # Main orchestrator
│   └── process_submission()  # Entry point
│
├── document_processor.py     # PDF/image extraction
│   └── process_document()    # Unstructured.io
│
├── cleaning_service.py       # Text standardization
│   └── clean_text()         # MarkItDown
│
├── embedding_service.py      # Vector generation
│   ├── embed_document()      # Full doc embedding
│   └── embed_chunks_with_context()  # Late Chunking
│
├── vector_store.py          # ChromaDB operations
│   ├── add_document_chunks()
│   └── search()
│
├── retrieval_service.py     # Search & re-rank
│   ├── hybrid_search()      # Vector + keyword
│   └── rerank()             # Cohere API
│
├── llm_service.py          # LLM inference
│   ├── generate()           # Groq/OpenAI
│   └── generate_with_citations()
│
├── rag_pipeline.py         # LangGraph workflow
│   └── run()                # Complete RAG flow
│
├── gmail_service.py        # Email collection
└── duplicate_detection.py  # Fuzzy matching
```

#### Database Schema

**SQLite Tables:**

1. **submissions**
   - `id` (PK): Auto-increment integer
   - `case_id` (Unique): CAS-YYYY-XXX format
   - `email`, `phone`, `description`
   - `submitted_at`: Timestamp
   - `status`: NEW, PROCESSING, REVIEWED, SENT
   - `stage`: CONTROL, RAPO, LITIGATION

2. **documents**
   - `id` (PK)
   - `submission_id` (FK → submissions.id)
   - `filename`, `mime_type`
   - `original_text`: Raw extracted text
   - `cleaned_text`: MarkItDown cleaned text
   - `structured_data`: JSON (tables, financial data)
   - `page_count`
   - `version`: For handling amendments

3. **chunks**
   - `id` (PK)
   - `document_id` (FK → documents.id)
   - `chunk_index`: Position in document
   - `content`: Chunk text
   - `page_number`, `section_title`, `clause_number`
   - `embedding_id`: Reference to ChromaDB

4. **queries**
   - `id` (PK)
   - `query_text`: User's question
   - `response_text`: AI-generated answer
   - `citations`: JSON array
   - `retrieved_chunk_ids`: JSON array
   - `created_at`: Timestamp

**Relationships:**
```
Submission (1) ──→ (many) Document
Document (1) ──→ (many) Chunk
```

#### RAG Pipeline Stages (Detailed)

**Stage 1: Retrieval Node**
```python
Input: User query string
Process:
  1. Embed query using Nomic-embed-text
  2. Search ChromaDB for similar chunks (vector search)
  3. Get top 10 results
Output: List of 10 candidate chunks with metadata
```

**Stage 2: Re-ranking**
```python
Input: 10 candidate chunks
Process:
  1. Send to Cohere reranker API
  2. Score each chunk against query
  3. Select top 3 most relevant
Output: 3 best chunks with relevance scores
```

**Stage 3: Drafting Node**
```python
Input: Query + 3 retrieved chunks
Process:
  1. Build context from chunks
  2. Create prompt with citation requirements
  3. Call LLM (Groq/OpenAI)
  4. Extract citations from response
Output: Draft answer with citations
```

**Stage 4: Critique Node**
```python
Input: Draft answer + citations
Process:
  1. Second LLM pass reviews answer
  2. Checks for:
     - Proper citations
     - Conflicts between sources
     - Hallucinations
     - Completeness
Output: Critique (ACCEPT or REVISE)
```

**Stage 5: Revision Node (if needed)**
```python
Input: Critique + original query
Process:
  1. Refine query based on critique
  2. Increment revision counter
  3. Clear previous results
Output: Refined query (loops back to Stage 1)
```

**Maximum 3 revisions** to prevent infinite loops.

### API Endpoints

#### POST /api/submit
**Purpose**: Receive client form submission

**Request Body:**
```json
{
  "email": "client@example.com",
  "phone": "0612345678",
  "description": "Case description...",
  "files": [
    {
      "name": "document.pdf",
      "mimeType": "application/pdf",
      "base64": "base64_encoded_content..."
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "case_id": "CAS-2025-001",
  "email": "client@example.com",
  "phone": "0612345678",
  "description": "Case description...",
  "submitted_at": "2025-01-15T10:30:00",
  "status": "NEW",
  "stage": "RAPO"
}
```

**What Happens:**
1. Case ID generated (CAS-YYYY-XXX)
2. Submission saved to database
3. Background processing triggered (async)
4. Response returned immediately

#### GET /api/cases
**Purpose**: Retrieve all cases for lawyer dashboard

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Max results (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "case_id": "CAS-2025-001",
    "email": "client@example.com",
    "status": "REVIEWED",
    "stage": "RAPO",
    "prestations": [
      {"name": "RSA", "isAccepted": true}
    ],
    "generatedEmailDraft": "...",
    "generatedAppealDraft": "..."
  }
]
```

#### GET /api/case/{case_id}
**Purpose**: Get specific case by case_id

**Response:** Same format as single case in `/api/cases`

#### POST /api/query
**Purpose**: RAG query endpoint for asking questions about cases

**Request Body:**
```json
{
  "query": "What is the main issue in this case?",
  "case_id": "CAS-2025-001"  // Optional: filter by case
}
```

**Response:**
```json
{
  "response": "Based on the documents, the main issue is...",
  "citations": [
    {
      "document_id": 1,
      "page_number": 2,
      "section_title": "Decision",
      "chunk_id": 42
    }
  ],
  "retrieved_chunks": 3,
  "query_id": 5
}
```

**What Happens:**
1. Query embedded
2. Hybrid search in ChromaDB
3. Re-ranking with Cohere
4. LLM generates answer with citations
5. Critique validates answer
6. Revision if needed (max 3x)
7. Response returned with citations

---

## 🧪 Testing

### Quick Test

1. **Start both servers** (see [Running the Application](#running-the-application))

2. **Test Client Submission:**
   - Go to http://localhost:3000
   - Fill out form with test data
   - Upload a test PDF or image
   - Submit
   - Should see success screen

3. **Test Lawyer Dashboard:**
   - Click "Espace Avocat"
   - Should see your test case
   - Click on case to view details
   - Try editing drafts
   - Try exporting documents

4. **Test RAG Query:**
   - Select a case
   - Go to "RAG Query" tab
   - Ask a question about the case
   - Should see answer with citations

### Comprehensive Testing

See detailed testing guide:
- [`documentation/before/TESTING_GUIDE.txt`](documentation/before/TESTING_GUIDE.txt)

### API Testing

Use FastAPI's interactive docs:
- Visit http://localhost:8000/docs
- Try each endpoint
- See request/response schemas
- Test with sample data

---

## 📁 Project Structure

```
Ilan_Legal_App/
├── App.tsx                    # Main React component
├── index.tsx                  # React entry point
├── index.html                 # HTML template
├── types.ts                   # TypeScript type definitions
├── vite.config.ts             # Vite configuration
├── tsconfig.json              # TypeScript configuration
├── package.json               # Frontend dependencies
├── .env                       # Environment variables (create this)
├── .gitignore                 # Git ignore rules
│
├── components/                # React components
│   ├── ClientForm.tsx         # Client intake form
│   ├── LawyerDashboard.tsx    # Lawyer case management
│   ├── QueryInterface.tsx     # RAG query UI
│   └── FormInput.tsx          # Reusable form input
│
├── services/                  # Frontend services
│   ├── apiClient.ts           # Backend API client
│   ├── geminiService.ts       # Gemini AI service (fallback mode)
│   └── knowledgeBase.ts       # Legal knowledge base
│
├── backend/                   # Python backend
│   ├── main.py                # FastAPI application
│   ├── config.py              # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── start.sh               # Startup script
│   │
│   ├── api/                   # API layer
│   │   ├── routes.py          # API endpoints
│   │   └── schemas.py         # Pydantic models
│   │
│   ├── database/              # Database layer
│   │   ├── db.py              # Database connection
│   │   └── models.py          # SQLAlchemy models
│   │
│   └── services/              # Business logic
│       ├── processing_pipeline.py    # Main orchestrator
│       ├── document_processor.py    # PDF extraction
│       ├── cleaning_service.py      # Text cleaning
│       ├── embedding_service.py     # Vector embeddings
│       ├── vector_store.py          # ChromaDB operations
│       ├── retrieval_service.py     # Search & re-rank
│       ├── llm_service.py           # LLM inference
│       ├── rag_pipeline.py          # LangGraph RAG
│       ├── gmail_service.py         # Gmail API
│       └── duplicate_detection.py   # Fuzzy matching
│
├── data/                      # Data storage (auto-created)
│   ├── database.db            # SQLite database
│   └── chroma_db/             # ChromaDB vector store
│
├── documentation/             # Documentation
│   ├── before/                # Original documentation
│   │   ├── Initial_app_documentation.txt
│   │   └── TESTING_GUIDE.txt
│   └── now/                   # Current documentation
│       ├── API_KEYS_SETUP_GUIDE.md
│       └── RAG_IMPLEMENTATION_SUMMARY.md
│
└── helper scripts/            # Utility scripts
    ├── get_gmail_token.py     # Gmail OAuth helper
    └── verify_env.py          # Environment verification
```

### Key Files Explained

**Frontend:**
- `App.tsx`: Main application logic, view switching, case management
- `components/ClientForm.tsx`: Client-facing form with validation
- `components/LawyerDashboard.tsx`: Professional case management interface
- `services/apiClient.ts`: HTTP client for backend API communication

**Backend:**
- `backend/main.py`: FastAPI server setup and routing
- `backend/api/routes.py`: REST API endpoint definitions
- `backend/services/processing_pipeline.py`: Orchestrates document processing
- `backend/services/rag_pipeline.py`: LangGraph-based RAG workflow

**Configuration:**
- `.env`: All API keys and configuration (not in git)
- `backend/config.py`: Settings class that loads from .env
- `vite.config.ts`: Frontend build configuration

---

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start

**Error: "ModuleNotFoundError"**
```bash
# Solution: Install missing dependencies
cd backend
pip install -r requirements.txt
```

**Error: "Database initialization error"**
- Check that `data/` directory exists and is writable
- Check database path in `.env`
- Server will still start, but database features won't work

**Error: "Port 8000 already in use"**
```bash
# Kill existing process
kill $(lsof -ti:8000)

# Or use a different port
uvicorn backend.main:app --port 8001
```

#### Frontend Won't Start

**Error: "vite: command not found"**
- Already fixed in package.json (uses direct path)
- If still fails: `npm install` again

**Error: "Cannot connect to backend"**
- Verify backend is running: `curl http://localhost:8000/health`
- Check `VITE_API_URL` in `.env.local` (if set)
- Check CORS settings in `backend/main.py`

#### API Errors

**"API Key is missing"**
- Check `.env` file exists in project root
- Verify key name matches exactly (case-sensitive in some cases)
- Restart server after adding keys

**"Failed to load cases from backend"**
- Check backend is running
- Check browser console for CORS errors
- Verify API endpoint: `curl http://localhost:8000/api/cases`

#### RAG Query Not Working

**"RAG query endpoint not yet implemented"**
- This means optional dependencies aren't installed
- Install: `pip install chromadb langgraph langchain nomic`
- Restart backend

**"No chunks found"**
- Documents may not be processed yet
- Check case status (should be "REVIEWED")
- Check backend logs for processing errors

### Debug Tips

1. **Check Backend Logs**: Look at terminal where backend is running
2. **Check Browser Console**: F12 → Console tab for frontend errors
3. **Use FastAPI Docs**: http://localhost:8000/docs to test API directly
4. **Verify Environment**: Run `python verify_env.py` (if available)

---

## 📚 Documentation

### Available Documentation

1. **This README**: Comprehensive overview and setup
2. **API Keys Setup Guide**: [`documentation/now/API_KEYS_SETUP_GUIDE.md`](documentation/now/API_KEYS_SETUP_GUIDE.md)
   - Step-by-step instructions for all API keys
   - Gmail API setup
   - Troubleshooting

3. **RAG Implementation Summary**: [`documentation/now/RAG_IMPLEMENTATION_SUMMARY.md`](documentation/now/RAG_IMPLEMENTATION_SUMMARY.md)
   - Technical implementation details
   - Pipeline stages
   - Configuration requirements

4. **Testing Guide**: [`documentation/before/TESTING_GUIDE.txt`](documentation/before/TESTING_GUIDE.txt)
   - Step-by-step testing instructions
   - Feature testing checklist

5. **Backend README**: [`backend/README.md`](backend/README.md)
   - Backend-specific setup
   - API endpoints
   - Service descriptions

### Helper Scripts

**get_gmail_token.py**: Get Gmail API refresh token
```bash
python helper\ scripts/get_gmail_token.py
```

**verify_env.py**: Verify all environment variables are set
```bash
python helper\ scripts/verify_env.py
```

---

## 🎓 Understanding the Application (For Non-Technical Users)

### What Does This App Do?

Imagine you're a lawyer helping people appeal decisions from the CAF (French social security). This app helps you:

1. **Collect Cases**: Clients fill out a form on your website with their information and documents
2. **Organize Everything**: All cases appear in one dashboard, sorted by date
3. **AI Assistance**: The app reads the documents and:
   - Figures out what stage the case is at (early stage, appeal stage, or court stage)
   - Identifies which benefits are involved (RSA, APL, etc.)
   - Writes draft emails to send to clients
   - Writes draft appeal documents
4. **Smart Search**: You can ask questions like "What's the main issue in this case?" and the app finds the relevant information from the documents
5. **Edit & Export**: You can edit the AI-generated documents and export them as Word files or emails

### How It Works (Simple Explanation)

**When a Client Submits:**
1. Client fills form → App saves information
2. App reads the documents (PDFs, images)
3. App converts documents to searchable text
4. App stores everything in a database
5. App analyzes the case and generates drafts

**When You (Lawyer) Use It:**
1. You see all cases in a list
2. You click on a case to see details
3. You can read/edit the AI-generated documents
4. You can ask questions about the case
5. You can export documents to send to clients

**The "RAG" Feature:**
- Think of it like a smart search engine for your case documents
- You ask a question
- The app searches through all the documents
- The app finds the most relevant parts
- The app writes an answer based on what it found
- The app tells you which documents and pages it used (citations)

---

## 🔬 Understanding the Application (For Technical Users)

### Architecture Patterns

**Frontend:**
- **Component-Based**: React functional components with hooks
- **State Management**: React useState (no Redux needed for this scale)
- **API Communication**: Fetch API via apiClient service
- **Type Safety**: TypeScript interfaces for all data structures

**Backend:**
- **RESTful API**: FastAPI with async/await
- **Service Layer**: Business logic separated from API routes
- **ORM**: SQLAlchemy for database operations
- **Async Processing**: Background tasks for document processing

**RAG Pipeline:**
- **Late Chunking**: Embed full document first, then chunk (preserves context)
- **Hybrid Search**: Vector (semantic) + Keyword (BM25-ready)
- **Re-ranking**: Cohere API for relevance scoring
- **LangGraph**: State machine for critique/revision loop

### Data Flow (Technical)

```
Client Form Submit
    │
    ├─→ Frontend: Convert files to base64
    │
    ├─→ POST /api/submit
    │   │
    │   ├─→ Generate case_id
    │   ├─→ Save to SQLite (submissions table)
    │   └─→ Trigger async task
    │       │
    │       └─→ Processing Pipeline
    │           │
    │           ├─→ DocumentProcessor.process_document()
    │           │   └─→ Unstructured.io: PDF → Text
    │           │
    │           ├─→ CleaningService.clean_text()
    │           │   └─→ MarkItDown: Standardize
    │           │
    │           ├─→ EmbeddingService.embed_chunks_with_context()
    │           │   └─→ Nomic: Late Chunking
    │           │
    │           └─→ VectorStore.add_document_chunks()
    │               └─→ ChromaDB: Store vectors
    │
    └─→ Response: Case created

Lawyer Query
    │
    ├─→ POST /api/query
    │   │
    │   └─→ RAGPipeline.run()
    │       │
    │       ├─→ RetrievalService.retrieve()
    │       │   ├─→ EmbeddingService.embed_query()
    │       │   ├─→ VectorStore.search() → Top 10
    │       │   └─→ RetrievalService.rerank() → Top 3
    │       │
    │       ├─→ LLMService.generate_with_citations()
    │       │   └─→ Groq/OpenAI: Generate answer
    │       │
    │       ├─→ LLMService.generate() (critique)
    │       │   └─→ Validate answer
    │       │
    │       └─→ Return or revise (max 3x)
    │
    └─→ Response: Answer + Citations
```

### Extension Points

**Adding New Features:**
- **New API Endpoint**: Add to `backend/api/routes.py`
- **New Service**: Add to `backend/services/`
- **New Component**: Add to `components/`
- **New Database Table**: Add model to `backend/database/models.py`

**Customizing AI Behavior:**
- **Prompts**: Edit `services/geminiService.ts` (frontend) or modify LLM prompts in services
- **Knowledge Base**: Edit `services/knowledgeBase.ts`
- **RAG Pipeline**: Modify `backend/services/rag_pipeline.py`

---

## 🚦 Quick Start Checklist

- [ ] Node.js installed (`node --version`)
- [ ] Python 3.12+ installed (`python3 --version`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend dependencies installed (`pip install -r backend/requirements.txt`)
- [ ] `.env` file created with API keys
- [ ] GEMINI_API_KEY set (required)
- [ ] GROQ_API_KEY set (required for RAG)
- [ ] Backend server running (`python3 -m uvicorn backend.main:app --port 8000`)
- [ ] Frontend server running (`npm run dev`)
- [ ] Both accessible (http://localhost:8000 and http://localhost:3000)

---

## 📞 Support & Resources

### API Documentation
- **FastAPI Docs**: http://localhost:8000/docs (when backend is running)
- **API Health**: http://localhost:8000/health

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

### Getting Help
1. Check this README's Troubleshooting section
2. Review error messages in browser console (F12)
3. Check backend server logs
4. Verify all API keys are set correctly
5. Use FastAPI docs to test API endpoints directly

---

## 📝 License & Credits

This application is developed for Maître Ilan BRUN-VARGAS's legal practice.

**Technologies Used:**
- React, TypeScript, Vite
- FastAPI, Python
- Google Gemini AI, Groq, Cohere
- ChromaDB, SQLite
- LangGraph, LangChain
- And many more open-source libraries

---

## 🎯 Next Steps

After setup:
1. ✅ Test the complete workflow
2. ✅ Configure Gmail API (if using email collection)
3. ✅ Customize prompts for your use case
4. ✅ Add more legal knowledge to knowledge base
5. ✅ Test RAG queries with real cases
6. ✅ Set up production deployment (if needed)

---

**Happy case managing! 🎉**

For detailed API key setup, see: [`documentation/now/API_KEYS_SETUP_GUIDE.md`](documentation/now/API_KEYS_SETUP_GUIDE.md)
