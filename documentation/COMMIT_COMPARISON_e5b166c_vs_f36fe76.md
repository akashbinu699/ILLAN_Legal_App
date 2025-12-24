# Comprehensive Comparison: Commit e5b166c vs f36fe76

**Document Version**: 1.0  
**Date**: December 24, 2025  
**Comparison**: Old Version (e5b166c) → New Version (f36fe76)

---

## Executive Summary

The application has been transformed from a **client-side-only React application** to a **full-stack application with a Python FastAPI backend**. The old version (e5b166c) was a simple frontend that called Google Gemini API directly from the browser. The new version (f36fe76) introduces a complete backend infrastructure with database persistence, document processing, vector search, and a RAG (Retrieval-Augmented Generation) pipeline.

**Key Transformation**: Client-only SPA → Client-Server Architecture with RAG Pipeline

**Impact**: This represents a complete architectural overhaul, moving from a simple frontend prototype to a sophisticated legal case management system with AI-powered document search and retrieval capabilities.

---

## 1. ARCHITECTURE CHANGES

### Old Version (e5b166c)
- **Type**: Single Page Application (SPA) - client-side only
- **Backend**: None - all processing in browser
- **Data Storage**: In-memory only (React state) - lost on page refresh
- **AI Integration**: Direct calls to Google Gemini API from browser
- **File Processing**: Handled by Gemini API directly (no preprocessing)
- **API Keys**: Exposed in browser (security risk)
- **Scalability**: Limited by browser capabilities

### New Version (f36fe76)
- **Type**: Full-stack application (client-server architecture)
- **Backend**: Python FastAPI server running on port 8000
- **Data Storage**: SQLite database with persistent storage
- **AI Integration**: Backend orchestrates multiple AI services (LLM, embeddings, re-ranking)
- **File Processing**: Complete document processing pipeline before AI
- **API Keys**: Secured in backend only
- **Scalability**: Server-side processing, background tasks, better resource management

**Architecture Diagram**:
```
OLD ARCHITECTURE:
┌─────────┐
│ Browser │ ──────→ Google Gemini API
│ (React) │         (Direct call)
└─────────┘
   ↓
In-memory state
(Data lost on refresh)

NEW ARCHITECTURE:
┌─────────┐         ┌─────────────────────────────────────┐
│ Browser │ ──────→ │  FastAPI Backend (Port 8000)      │
│ (React) │         │  ┌───────────────────────────────┐ │
└─────────┘         │  │ SQLite Database             │ │
                     │  │ - Submissions               │ │
                     │  │ - Documents                 │ │
                     │  │ - Chunks                    │ │
                     │  │ - Queries                   │ │
                     │  └───────────────────────────────┘ │
                     │  ┌───────────────────────────────┐ │
                     │  │ Document Processing Pipeline   │ │
                     │  │ - PDF Extraction              │ │
                     │  │ - Text Cleaning               │ │
                     │  │ - Embedding Generation        │ │
                     │  └───────────────────────────────┘ │
                     │  ┌───────────────────────────────┐ │
                     │  │ ChromaDB Vector Store          │ │
                     │  │ - Document Embeddings         │ │
                     │  │ - Metadata Tracking           │ │
                     │  └───────────────────────────────┘ │
                     │  ┌───────────────────────────────┐ │
                     │  │ RAG Pipeline (LangGraph)      │ │
                     │  │ - Retrieval                    │ │
                     │  │ - Drafting                    │ │
                     │  │ - Critique                    │ │
                     │  │ - Revision Loop               │ │
                     │  └───────────────────────────────┘ │
                     │  ┌───────────────────────────────┐ │
                     │  │ LLM Services                   │ │
                     │  │ - OpenAI/Groq                 │ │
                     │  │ - Local LLM (optional)         │ │
                     │  └───────────────────────────────┘ │
                     └─────────────────────────────────────┘
```

---

## 2. DATABASE CHANGES

### Old Version (e5b166c)
- **Database**: None
- **Data Persistence**: None - all data in React component state
- **Data Loss**: All case data lost on page refresh
- **Case Management**: Sequential IDs generated client-side
- **No History**: No query history, no document versioning

### New Version (f36fe76)
- **Database**: SQLite database (`./data/database.db`)
- **ORM**: SQLAlchemy with async support
- **Connection**: AsyncSQLite engine with session management
- **Auto-initialization**: Database tables created automatically on startup

### Database Schema

#### Table 1: `submissions`
Stores client form submissions.

**Columns**:
- `id` (Integer, Primary Key) - Auto-incrementing database ID
- `case_id` (String, Unique, Indexed) - Human-readable case ID in format `CAS-YYYY-XXX` (e.g., CAS-2025-001)
- `email` (String, Indexed) - Client email address
- `phone` (String) - Client phone number
- `description` (Text) - Case description from client
- `submitted_at` (DateTime) - Timestamp of submission (UTC)
- `status` (String) - Case status: `NEW`, `PROCESSING`, `REVIEWED`, `SENT`
- `stage` (String) - Legal stage: `CONTROL`, `RAPO`, `LITIGATION`

**Relationships**:
- One-to-many with `documents` table

#### Table 2: `documents`
Stores processed documents from submissions.

**Columns**:
- `id` (Integer, Primary Key) - Auto-incrementing database ID
- `submission_id` (Integer, Foreign Key) - Links to submission
- `filename` (String) - Original filename
- `mime_type` (String) - MIME type (e.g., application/pdf, image/jpeg)
- `original_text` (Text) - Raw extracted text from document
- `cleaned_text` (Text) - MarkItDown cleaned and standardized text
- `structured_data` (JSON) - Extracted tables and financial data as JSON
- `page_count` (Integer) - Number of pages in document
- `processed_at` (DateTime) - Timestamp of processing
- `version` (Integer, Default: 1) - Document version for handling amendments

**Relationships**:
- Many-to-one with `submissions` table
- One-to-many with `chunks` table

#### Table 3: `chunks`
Stores document chunks with embedding metadata.

**Columns**:
- `id` (Integer, Primary Key) - Auto-incrementing database ID
- `document_id` (Integer, Foreign Key) - Links to document
- `chunk_index` (Integer) - Position of chunk in document (0-based)
- `content` (Text) - Chunk text content
- `page_number` (Integer) - Page number where chunk appears
- `section_title` (String, Nullable) - Section title if available
- `clause_number` (String, Nullable) - Clause number if applicable
- `embedding_id` (String, Indexed) - Reference to ChromaDB embedding ID
- `created_at` (DateTime) - Timestamp of chunk creation

**Relationships**:
- Many-to-one with `documents` table

#### Table 4: `queries`
Stores query history and responses for RAG queries.

**Columns**:
- `id` (Integer, Primary Key) - Auto-incrementing database ID
- `query_text` (Text) - Original query text
- `response_text` (Text) - Generated response
- `citations` (JSON) - List of citations with metadata
- `retrieved_chunk_ids` (JSON) - Array of chunk IDs used in response
- `created_at` (DateTime) - Timestamp of query

**Relationships**:
- Standalone table (no foreign keys)

### Database Features

1. **Automatic Case ID Generation**:
   - Format: `CAS-{YEAR}-{SEQUENCE}`
   - Example: `CAS-2025-001`, `CAS-2025-002`
   - Sequence numbers reset each year
   - Generated server-side, ensuring uniqueness

2. **Status Tracking**:
   - `NEW` → Initial state when case is submitted
   - `PROCESSING` → Document processing in progress
   - `REVIEWED` → Processing complete, ready for lawyer review
   - `SENT` → Case documents sent to client

3. **Document Versioning**:
   - `version` field supports document amendments
   - Allows tracking of document updates over time

4. **Query History**:
   - All RAG queries are saved to database
   - Enables analysis of query patterns
   - Supports query replay and debugging

5. **Cascade Deletes**:
   - Deleting a submission deletes all associated documents
   - Deleting a document deletes all associated chunks
   - Maintains referential integrity

### Database Initialization

- **Location**: `backend/database/db.py`
- **Initialization**: Automatic on FastAPI startup
- **Method**: `init_db()` function creates all tables using SQLAlchemy metadata
- **Error Handling**: Server continues even if database initialization fails (with warning)

---

## 3. BACKEND INFRASTRUCTURE (NEW)

### Completely New Backend System

All backend files are new additions. The backend is built with Python 3.12+ and FastAPI.

### Backend Structure

```
backend/
├── main.py                    # FastAPI server entry point
├── config.py                  # Configuration management (.env)
├── requirements.txt           # Python dependencies (41 packages)
├── start.sh                   # Startup script
├── __init__.py                # Python package marker
├── api/
│   ├── __init__.py
│   ├── routes.py             # REST API endpoints
│   └── schemas.py            # Pydantic request/response models
├── database/
│   ├── __init__.py
│   ├── db.py                 # Database connection & session management
│   └── models.py             # SQLAlchemy ORM models
└── services/
    ├── __init__.py
    ├── gmail_service.py      # Gmail API integration
    ├── document_processor.py # PDF/image processing (Unstructured.io)
    ├── cleaning_service.py   # Text cleaning (MarkItDown)
    ├── duplicate_detection.py # Fuzzy matching for duplicates
    ├── embedding_service.py  # Late Chunking embeddings (Nomic)
    ├── vector_store.py        # ChromaDB vector database
    ├── retrieval_service.py   # Hybrid search + re-ranking
    ├── llm_service.py         # LLM inference (OpenAI/Groq/local)
    ├── rag_pipeline.py        # LangGraph RAG orchestration
    └── processing_pipeline.py # Complete processing orchestration
```

### FastAPI Server (`backend/main.py`)

**Features**:
- FastAPI application with automatic API documentation
- CORS middleware configured for `localhost:3000`
- Database initialization on startup
- Health check endpoint (`/health`)
- Root endpoint with API information

**Configuration**:
- Host: `0.0.0.0` (configurable via settings)
- Port: `8000` (configurable via settings)
- Reload: Enabled for development

### API Endpoints

#### 1. POST `/api/submit`
Submit a new case from the client form.

**Request Body** (`SubmissionCreate`):
```json
{
  "email": "client@example.com",
  "phone": "+33123456789",
  "description": "Case description text",
  "files": [
    {
      "name": "document.pdf",
      "mimeType": "application/pdf",
      "base64": "base64-encoded-file-content"
    }
  ]
}
```

**Response** (`SubmissionResponse`):
```json
{
  "id": 1,
  "case_id": "CAS-2025-001",
  "email": "client@example.com",
  "phone": "+33123456789",
  "description": "Case description text",
  "submitted_at": "2025-12-24T10:00:00",
  "status": "NEW",
  "stage": "RAPO"
}
```

**Behavior**:
- Creates submission record in database
- Generates unique case_id
- Triggers background document processing pipeline
- Returns immediately (non-blocking)

#### 2. GET `/api/cases`
Retrieve all cases for the lawyer dashboard.

**Query Parameters**:
- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100) - Maximum number of results

**Response**: Array of `CaseResponse` objects

**Features**:
- Ordered by `submitted_at` descending (newest first)
- Includes document relationships
- Supports pagination

#### 3. GET `/api/case/{case_id}`
Get a specific case by case_id.

**Path Parameter**: `case_id` (string, e.g., "CAS-2025-001")

**Response**: Single `CaseResponse` object

**Error**: 404 if case not found

#### 4. POST `/api/query`
RAG query endpoint for querying case documents.

**Request Body** (`QueryRequest`):
```json
{
  "query": "What is the decision date mentioned in the documents?",
  "case_id": "CAS-2025-001"  // Optional: filter by case
}
```

**Response** (`QueryResponse`):
```json
{
  "response": "The decision date is...",
  "citations": [
    {
      "document_id": 1,
      "page_number": 2,
      "section_title": "Decision",
      "clause_number": null,
      "chunk_id": 42
    }
  ],
  "retrieved_chunks": 3,
  "query_id": 1
}
```

**Behavior**:
- Runs complete RAG pipeline
- Saves query to database
- Returns answer with citations

#### 5. GET `/health`
Health check endpoint.

**Response**: `{"status": "healthy"}`

#### 6. GET `/`
API information endpoint.

**Response**: API metadata (name, version, status)

### API Schemas (`backend/api/schemas.py`)

Pydantic models for request/response validation:

- `AttachedFileSchema` - File metadata (name, mimeType, base64)
- `SubmissionCreate` - Request schema for case submission
- `SubmissionResponse` - Response schema for submission
- `QueryRequest` - Request schema for RAG queries
- `QueryResponse` - Response schema for RAG queries
- `CaseResponse` - Response schema for case details
- `PrestationSchema` - Schema for benefits/prestations
- `Citation` - Schema for document citations

### Configuration System (`backend/config.py`)

**Environment Variables** (loaded from `.env` file):

- **Gmail API**:
  - `GMAIL_CLIENT_ID`
  - `GMAIL_CLIENT_SECRET`
  - `GMAIL_REFRESH_TOKEN`

- **Database**:
  - `DATABASE_PATH` (default: `./data/database.db`)
  - `CHROMA_DB_PATH` (default: `./data/chroma_db`)

- **LLM**:
  - `LOCAL_LLM_PATH` (optional, for local models)
  - `OPENAI_API_KEY` (for OpenAI API)
  - `GROQ_API_KEY` (for Groq API, preferred)

- **Embeddings**:
  - `EMBEDDING_MODEL` (default: `nomic-embed-text-v1.5`)

- **Re-ranker**:
  - `RERANKER_API_KEY` or `COHERE_API_KEY` (for Cohere re-ranking)

- **API Server**:
  - `API_HOST` (default: `0.0.0.0`)
  - `API_PORT` (default: `8000`)
  - `CORS_ORIGINS` (default: `["http://localhost:3000", "http://127.0.0.1:3000"]`)

**Features**:
- Automatic directory creation for data paths
- Type-safe configuration with Pydantic Settings
- Environment variable loading with `.env` file support

### Backend Services

#### 1. Gmail Service (`backend/services/gmail_service.py`)
- OAuth2 authentication with refresh token support
- Email collection from Gmail inbox
- Attachment extraction
- Duplicate detection integration
- **Status**: Implemented, requires Gmail API credentials

#### 2. Document Processor (`backend/services/document_processor.py`)
- PDF text extraction using Unstructured.io
- Image OCR support
- Table extraction to structured JSON
- Page count detection
- MIME type handling

#### 3. Cleaning Service (`backend/services/cleaning_service.py`)
- MarkItDown text cleaning and standardization
- Structured data preservation (tables, financial data)
- Text normalization
- Removes formatting artifacts

#### 4. Duplicate Detection (`backend/services/duplicate_detection.py`)
- Fuzzy matching using rapidfuzz
- Detects duplicate documents
- Similarity scoring
- Configurable threshold

#### 5. Embedding Service (`backend/services/embedding_service.py`)
- **Late Chunking strategy** implementation
- Nomic-embed-text-v1.5 model
- Full document context encoding
- Chunk embedding with surrounding context
- Mean pooling over chunk spans

#### 6. Vector Store (`backend/services/vector_store.py`)
- ChromaDB integration
- Persistent vector storage
- Metadata tracking
- Search functionality
- Document chunk management

#### 7. Retrieval Service (`backend/services/retrieval_service.py`)
- Hybrid search (vector + keyword ready)
- Vector search using ChromaDB
- Re-ranking with Cohere API
- Fallback to distance-based ranking
- Top-k result selection

#### 8. LLM Service (`backend/services/llm_service.py`)
- Multiple LLM support:
  - Groq API (preferred, fast)
  - OpenAI API (fallback)
  - Local LLM (placeholder, not yet implemented)
- Citation-required generation
- Configurable temperature and max tokens
- System prompt for legal context

#### 9. RAG Pipeline (`backend/services/rag_pipeline.py`)
- LangGraph state machine orchestration
- Retrieval → Drafting → Critique → Revision loop
- Maximum 3 revision iterations
- State management with TypedDict
- Citation extraction

#### 10. Processing Pipeline (`backend/services/processing_pipeline.py`)
- Complete orchestration of document processing
- Coordinates all services
- Background task execution
- Status updates
- Error handling and recovery

### Startup Script (`backend/start.sh`)

Bash script for easy backend startup:
- Checks Python installation
- Creates virtual environment if needed
- Installs dependencies
- Checks for `.env` file
- Starts FastAPI server

---

## 4. FRONTEND CHANGES

### App.tsx - Major Changes

#### Old Behavior (e5b166c)
- Direct Gemini API calls from browser
- In-memory state management only
- Immediate AI processing on form submit
- No backend communication
- Case IDs generated client-side

#### New Behavior (f36fe76)
- **Dual-mode support**: `useBackend` toggle (defaults to `true`)
- Backend API integration via `apiClient`
- Loads cases from backend on component mount
- Form submission sends to `/api/submit` endpoint
- Falls back to old direct Gemini flow if `useBackend = false`
- Automatic case reload after submission

#### Key Code Changes

1. **New State Variable**:
   ```typescript
   const [useBackend, setUseBackend] = useState<boolean>(true);
   ```

2. **New useEffect Hook**:
   ```typescript
   useEffect(() => {
       if (useBackend) {
           loadCasesFromBackend();
       }
   }, [useBackend]);
   ```

3. **New Function**: `loadCasesFromBackend()`
   - Fetches all cases from `/api/cases`
   - Converts API response format to `ClientSubmission` format
   - Handles errors gracefully (falls back to empty array)

4. **Modified Function**: `handleClientSubmit()`
   - Now has two execution paths:
     - **Backend path** (when `useBackend = true`):
       - Sends submission to `/api/submit`
       - Receives case_id from backend
       - Updates local state
       - Triggers case reload after 2 seconds
     - **Direct Gemini path** (when `useBackend = false`):
       - Original behavior preserved
       - Direct Gemini API calls
       - Client-side processing

5. **Error Handling**:
   - Improved error messages
   - Network error detection
   - User-friendly alerts in French
   - Console logging for debugging

### New Components

#### 1. QueryInterface.tsx (NEW)

**Purpose**: RAG query interface for lawyers to query case documents.

**Location**: `components/QueryInterface.tsx`

**Features**:
- Natural language query input
- Loading states with spinner
- Error display
- Response display with formatting
- Citation display with metadata
- Query statistics (retrieved chunks, query ID)
- Optional case_id filtering

**Props**:
- `caseId?: string` - Optional case ID to filter queries

**UI Elements**:
- Search input field
- Query button with loading state
- Response area with citations
- Error messages
- Statistics display

**Integration**: Added as new tab in LawyerDashboard

### Modified Components

#### 1. LawyerDashboard.tsx

**Changes**:
- Added new "RAG Query" tab
- Imported `QueryInterface` component
- Updated tab navigation: `'details' | 'email' | 'appeal' | 'query'`
- Added QueryInterface rendering in query tab

**Tab Structure** (before → after):
- Before: Details | Email | Appeal
- After: Details | Email | Appeal | **Query** (new)

**Code Changes**:
```typescript
// New tab state type
const [activeTab, setActiveTab] = useState<'details' | 'email' | 'appeal' | 'query'>('email');

// New tab button
<button onClick={() => setActiveTab('query')}>
  <i className="fas fa-search"></i> RAG Query
</button>

// New tab content
{activeTab === 'query' && (
  <QueryInterface caseId={selectedCase.id} />
)}
```

### New Services

#### 1. apiClient.ts (NEW)

**Purpose**: TypeScript API client for backend communication.

**Location**: `services/apiClient.ts`

**Features**:
- Type-safe API methods
- Error handling for network issues
- Configurable base URL (via `VITE_API_URL` env var)
- Default URL: `http://localhost:8000/api`

**Methods**:

1. **`submitCase(submission: ApiSubmission): Promise<ApiCase>`**
   - Submits new case to backend
   - Returns case with generated case_id

2. **`getCases(): Promise<ApiCase[]>`**
   - Retrieves all cases
   - Returns array of case objects

3. **`getCase(caseId: string): Promise<ApiCase>`**
   - Retrieves specific case by case_id
   - Returns single case object

4. **`queryRAG(query: ApiQuery): Promise<ApiQueryResponse>`**
   - Sends RAG query to backend
   - Returns answer with citations

**Error Handling**:
- Network errors (backend not running)
- HTTP errors (4xx, 5xx)
- JSON parsing errors
- User-friendly error messages

**Interfaces**:
- `ApiSubmission` - Submission request format
- `ApiCase` - Case response format
- `ApiQuery` - Query request format
- `ApiQueryResponse` - Query response format

### Unchanged Components

- **ClientForm.tsx**: No changes - still works the same way
- **FormInput.tsx**: No changes
- **geminiService.ts**: Still exists, used when `useBackend = false`
- **knowledgeBase.ts**: Unchanged

---

## 5. DOCUMENT PROCESSING PIPELINE (NEW)

### Old Version
- Files sent directly to Gemini API
- No preprocessing or extraction
- No structured data extraction
- No text cleaning
- No chunking or embedding

### New Version - Complete Processing Pipeline

The document processing pipeline is a multi-stage process that transforms raw document files into searchable, embedded content.

#### Pipeline Overview

```
Raw Files (Base64)
  ↓
Document Reception & Decoding
  ↓
Document Processing (Unstructured.io)
  ↓
Text Cleaning (MarkItDown)
  ↓
Chunking
  ↓
Embedding Generation (Late Chunking)
  ↓
Vector Storage (ChromaDB)
  ↓
Database Storage (SQLite)
```

#### Stage 1: Document Reception

**Location**: `backend/services/processing_pipeline.py`

**Process**:
- Receives base64-encoded files from API
- Decodes base64 to binary
- Extracts file metadata (name, MIME type)

#### Stage 2: Document Processing

**Location**: `backend/services/document_processor.py`

**Service**: `DocumentProcessor.process_document()`

**Capabilities**:
- **PDF Processing**: Text extraction from PDF files using Unstructured.io
- **Image OCR**: Optical Character Recognition for image files (JPEG, PNG)
- **Table Extraction**: Extracts tables to structured JSON format
- **Page Count**: Detects number of pages in document
- **MIME Type Handling**: Supports multiple file formats

**Output**:
```python
{
    "text": "Extracted text content...",
    "tables": [
        {
            "type": "table",
            "text": "Table content...",
            "metadata": {...}
        }
    ],
    "page_count": 5
}
```

#### Stage 3: Text Cleaning

**Location**: `backend/services/cleaning_service.py`

**Service**: `CleaningService.process_document()`

**Process**:
- **MarkItDown Processing**: Standardizes text format
- **Structured Data Preservation**: Maintains tables and financial data
- **Text Normalization**: Removes formatting artifacts
- **Whitespace Cleanup**: Normalizes spacing

**Output**:
```python
{
    "cleaned_text": "Standardized text...",
    "structured_data": {
        "tables": [...],
        "financial_data": [...]
    }
}
```

#### Stage 4: Chunking

**Location**: `backend/services/processing_pipeline.py`

**Method**: `ProcessingPipeline._chunk_document()`

**Strategy**:
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters (for context preservation)
- **Method**: Sliding window approach

**Purpose**: Break large documents into smaller, manageable pieces for embedding and search.

#### Stage 5: Embedding Generation

**Location**: `backend/services/embedding_service.py`

**Service**: `EmbeddingService.embed_chunks_with_context()`

**Strategy**: **Late Chunking**

**Process**:
1. **Full Document Embedding**: Embed entire document for context
2. **Context Window**: For each chunk, create context window around it
3. **Mean Pooling**: Apply mean pooling over chunk span
4. **Model**: Nomic-embed-text-v1.5 (768 dimensions)

**Why Late Chunking?**:
- Preserves document-level context
- Better semantic understanding
- Improved search relevance

**Output**: List of embeddings with metadata

#### Stage 6: Vector Storage

**Location**: `backend/services/vector_store.py`

**Service**: `VectorStore.add_document_chunks()`

**Storage**: ChromaDB (persistent vector database)

**Metadata Tracked**:
- `document_id`: Database document ID
- `submission_id`: Related submission ID
- `chunk_index`: Position in document
- `page_number`: Page where chunk appears
- `section_title`: Section title if available
- `clause_number`: Clause number if applicable
- `filename`: Original filename

**Features**:
- Persistent storage (survives restarts)
- Fast similarity search
- Metadata filtering support

#### Stage 7: Database Storage

**Location**: `backend/services/processing_pipeline.py`

**Process**:
- Creates `Document` record in SQLite
- Creates `Chunk` records for each chunk
- Links chunks to documents via foreign keys
- Stores embedding references (ChromaDB IDs)

**Status Updates**:
- Submission status: `NEW` → `PROCESSING` → `REVIEWED`

### Background Processing

**Implementation**: Async background task

**Location**: `backend/api/routes.py` (submit_case endpoint)

**Process**:
1. Submission created in database
2. API returns immediately with case_id
3. Background task starts processing
4. Separate database session created for processing
5. Status updated as processing progresses

**Benefits**:
- Non-blocking API responses
- Better user experience
- Error isolation (processing errors don't affect submission)

**Error Handling**:
- Processing errors logged
- Submission status reset to `NEW` on error
- Errors don't crash the server

---

## 6. RAG (RETRIEVAL-AUGMENTED GENERATION) PIPELINE (NEW)

### Completely New Feature

The RAG pipeline enables lawyers to query case documents using natural language and receive answers with citations.

### RAG Pipeline Components

#### 1. Retrieval Service

**Location**: `backend/services/retrieval_service.py`

**Service**: `RetrievalService`

**Methods**:

1. **`hybrid_search(query, n_results, filter_metadata)`**
   - Embeds query using embedding service
   - Performs vector search in ChromaDB
   - Returns top `n_results * 2` chunks (for re-ranking)
   - **Future**: BM25 keyword search can be added

2. **`rerank(query, chunks, top_k)`**
   - Re-ranks chunks using Cohere API
   - Falls back to distance-based ranking if Cohere unavailable
   - Returns top `top_k` most relevant chunks

3. **`retrieve(query, n_results, top_k, filter_metadata)`**
   - Complete retrieval pipeline
   - Combines hybrid search + re-ranking
   - Returns final top-k results

**Re-ranking Strategy**:
- **Primary**: Cohere reranker API (rerank-english-v3.0)
- **Fallback**: Distance-based ranking (cosine distance)

#### 2. RAG Pipeline (LangGraph)

**Location**: `backend/services/rag_pipeline.py`

**Service**: `RAGPipeline`

**Architecture**: LangGraph state machine

**State Schema** (`RAGState`):
```python
{
    "query": str,              # Original or refined query
    "retrieved_chunks": list,  # Retrieved document chunks
    "draft_answer": str,      # LLM-generated answer
    "critique": str,          # Critique of the answer
    "citations": list,        # Extracted citations
    "revision_count": int,    # Number of revisions
    "final_answer": str       # Final answer
}
```

**Graph Structure**:
```
┌──────────┐
│ Retrieval│ ───→ Find relevant chunks
└──────────┘
     ↓
┌──────────┐
│ Drafting │ ───→ Generate answer with citations
└──────────┘
     ↓
┌──────────┐
│ Critique │ ───→ Validate answer quality
└──────────┘
     ↓
    / \
   /   \
  /     \
REVISE  ACCEPT
  ↓       ↓
┌─────┐  END
│Loop │
└─────┘
(max 3 times)
```

**Nodes**:

1. **Retrieval Node** (`_retrieval_node`)
   - Executes hybrid search
   - Re-ranks results
   - Returns top 3 chunks

2. **Drafting Node** (`_drafting_node`)
   - Generates answer using LLM
   - Requires citations in response
   - Extracts citations from answer

3. **Critique Node** (`_critique_node`)
   - Second LLM pass validates answer
   - Checks for:
     - Proper citations
     - Contradictions
     - Accuracy
     - Completeness
     - Hallucinations

4. **Revision Node** (`_revision_node`)
   - Refines query based on critique
   - Increments revision count
   - Clears previous results
   - Loops back to retrieval

**Conditional Logic** (`_should_revise`):
- Returns `"revise"` if critique indicates issues
- Returns `"accept"` if critique is positive
- Maximum 3 revisions to prevent infinite loops

**Execution**:
- Invoked via `rag_pipeline.run(query)`
- Returns final answer with citations and metadata

#### 3. LLM Service

**Location**: `backend/services/llm_service.py`

**Service**: `LLMService`

**Methods**:

1. **`generate(prompt, max_tokens, temperature)`**
   - Generates text using LLM
   - Supports multiple providers:
     - **Groq** (preferred, fast)
     - **OpenAI** (fallback)
     - **Local LLM** (placeholder, not implemented)

2. **`generate_with_citations(query, retrieved_chunks, require_citations)`**
   - Generates answer with citation requirements
   - Builds context from retrieved chunks
   - Extracts citations using regex
   - Returns response with citations array

**Citation Format**:
- Required format: `[Document ID, Page Number, Section Title]`
- Example: `[Doc-123, Page 2, Section: Decision]`
- Extracted using regex pattern matching

### RAG Query Flow

**Complete Flow**:

1. **User submits query** via QueryInterface component
2. **Frontend sends** POST request to `/api/query`
3. **Backend receives** query in `query_rag()` endpoint
4. **RAG Pipeline executes**:
   - Retrieval finds relevant chunks
   - Drafting generates answer
   - Critique validates answer
   - Revision loop if needed (max 3 times)
5. **Query saved** to database
6. **Response returned** with:
   - Answer text
   - Citations array
   - Retrieved chunk count
   - Query ID
7. **Frontend displays** answer and citations

**Example Query**:
```
Query: "What is the decision date mentioned in the documents?"

Response: "The decision date is March 15, 2025, as stated in the notification letter [Doc-1, Page 2, Section: Decision]."

Citations: [
  {
    "document_id": 1,
    "page_number": 2,
    "section_title": "Decision",
    "chunk_id": 42
  }
]
```

### Benefits of RAG Pipeline

1. **Accurate Answers**: Grounded in actual documents
2. **Citations**: Traceability to source documents
3. **Quality Control**: Critique loop ensures answer quality
4. **Iterative Improvement**: Revision loop refines queries
5. **History Tracking**: All queries saved for analysis

---

## 7. WORKFLOW CHANGES

### Old Workflow (e5b166c)

```
┌─────────────────┐
│ Client submits  │
│ form in browser │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Browser generates│
│ case ID locally  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Direct Gemini   │
│ API call:       │
│ detect stage    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Update stage in │
│ React state     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Direct Gemini   │
│ API call:       │
│ generate prompts│
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Direct Gemini   │
│ API calls:      │
│ generate drafts │
│ (parallel)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Update React    │
│ state with      │
│ drafts          │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Lawyer reviews  │
│ in dashboard    │
└─────────────────┘
```

**Issues with Old Workflow**:
- ❌ No persistence (data lost on refresh)
- ❌ No document processing
- ❌ No search capability
- ❌ All processing in browser (slower)
- ❌ API key exposed in browser
- ❌ No error recovery
- ❌ No query history

### New Workflow (f36fe76)

```
┌─────────────────┐
│ Client submits  │
│ form in browser │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Frontend sends   │
│ to /api/submit   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Backend creates  │
│ submission in    │
│ database        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Returns case_id  │
│ immediately     │
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ↓                                 ↓
┌─────────────────┐            ┌─────────────────┐
│ Frontend shows   │            │ [Background]    │
│ success message  │            │ Document         │
│                  │            │ Processing:      │
└─────────────────┘            │ - Extract text   │
                                │ - Clean text     │
                                │ - Generate       │
                                │   embeddings     │
                                │ - Store in       │
                                │   ChromaDB       │
                                │ - Update status  │
                                │   to REVIEWED     │
                                └─────────────────┘
                                         │
                                         ↓
                                ┌─────────────────┐
                                │ Lawyer can query │
                                │ documents via    │
                                │ RAG              │
                                └────────┬────────┘
                                         │
                                         ↓
                                ┌─────────────────┐
                                │ Lawyer reviews   │
                                │ in dashboard     │
                                └─────────────────┘
```

**Improvements in New Workflow**:
- ✅ Persistent storage (survives restarts)
- ✅ Background processing (non-blocking)
- ✅ Document search capability (RAG)
- ✅ Server-side processing (faster, more secure)
- ✅ API keys secured in backend
- ✅ Error recovery and logging
- ✅ Query history tracking
- ✅ Better scalability

### Workflow Comparison Table

| Aspect | Old Workflow | New Workflow |
|--------|-------------|--------------|
| **Data Storage** | In-memory only | SQLite database |
| **Processing** | Browser (blocking) | Server (background) |
| **Document Handling** | Direct to Gemini | Full processing pipeline |
| **Search** | None | RAG with vector search |
| **Error Handling** | Basic | Comprehensive |
| **API Security** | Keys in browser | Keys in backend |
| **Query History** | None | Saved to database |
| **Scalability** | Limited | Better |

---

## 8. DEPENDENCIES & CONFIGURATION

### Old Version Dependencies

**Frontend Only**:
- `react` (19.2.0)
- `typescript` (5.8.2)
- `vite` (6.2.0)
- `@google/genai` (1.30.0) - Gemini API client
- `@vitejs/plugin-react` - React plugin for Vite
- `@types/node` - Node.js type definitions

**No Backend Dependencies**

### New Version Dependencies

#### Frontend Dependencies (Unchanged)
- Same as old version
- No new frontend packages added
- Optional: `VITE_API_URL` environment variable

#### Backend Dependencies (41 New Packages)

**Web Framework**:
- `fastapi` (0.109.0) - Modern Python web framework
- `uvicorn[standard]` (0.27.0) - ASGI server
- `python-multipart` (0.0.6) - File upload support

**Database**:
- `sqlalchemy` (2.0.25) - SQL toolkit and ORM
- `aiosqlite` (0.19.0) - Async SQLite driver
- `greenlet` (>=3.0.0) - Lightweight coroutines

**Gmail API**:
- `google-api-python-client` (2.108.0) - Google API client
- `google-auth-httplib2` (0.2.0) - HTTP transport for auth
- `google-auth-oauthlib` (1.2.0) - OAuth2 flow

**Document Processing**:
- `unstructured` (0.11.8) - Document parsing and extraction
- `markitdown` (0.1.4) - Text cleaning and standardization

**Fuzzy Matching**:
- `rapidfuzz` (3.6.1) - Fast string matching

**Embeddings**:
- `nomic` (1.1.9) - Nomic embedding models

**Vector Database**:
- `chromadb` (0.4.22) - Vector database

**LLM and Orchestration**:
- `langchain` (0.1.6) - LLM application framework
- `langgraph` (0.0.26) - State machine for LLM workflows
- `langchain-community` (0.0.20) - Community integrations

**Re-ranking**:
- `cohere` (4.47) - Cohere API client

**Utilities**:
- `python-dotenv` (1.0.0) - Environment variable management
- `pydantic` (2.5.3) - Data validation
- `pydantic-settings` (2.1.0) - Settings management

### Configuration Files

#### 1. `.env` File (Project Root)

**Purpose**: Environment variable configuration

**Required Variables**:
```env
# Gmail API (Optional)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Database Paths (Optional, defaults provided)
DATABASE_PATH=./data/database.db
CHROMA_DB_PATH=./data/chroma_db

# LLM API Keys (Required for RAG)
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key  # Preferred, faster

# Local LLM (Optional)
LOCAL_LLM_PATH=./models/gpt-oss-20b

# Embedding Model (Optional, default provided)
EMBEDDING_MODEL=nomic-embed-text-v1.5

# Re-ranker (Optional but recommended)
RERANKER_API_KEY=your_cohere_key
# Or use COHERE_API_KEY (alias)

# API Server (Optional, defaults provided)
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### 2. `backend/requirements.txt`

**Purpose**: Python package dependencies

**Content**: List of 41 Python packages with version pins

**Usage**: `pip install -r requirements.txt`

#### 3. `backend/start.sh`

**Purpose**: Backend startup script

**Features**:
- Checks Python installation
- Creates virtual environment
- Installs dependencies
- Checks for `.env` file
- Starts FastAPI server

#### 4. Frontend Environment (Optional)

**File**: `.env.local` or `.env`

**Variable**:
```env
VITE_API_URL=http://localhost:8000/api
```

**Purpose**: Override backend API URL (defaults to `http://localhost:8000/api`)

---

## 9. NEW FEATURES

### 1. RAG Query Interface

**What it is**: Natural language query system for case documents

**Location**: `components/QueryInterface.tsx`

**Features**:
- Natural language queries (e.g., "What is the decision date?")
- Answers with citations
- Query history tracking
- Integration in lawyer dashboard
- Loading states and error handling

**Use Case**: Lawyers can quickly find information in case documents without manually reading through them

### 2. Document Processing

**What it is**: Complete pipeline for processing uploaded documents

**Features**:
- PDF text extraction
- Image OCR
- Table extraction to JSON
- Text cleaning and standardization
- Automatic chunking
- Embedding generation

**Use Case**: Converts raw documents into searchable, structured data

### 3. Vector Search

**What it is**: Semantic search over document content

**Features**:
- Hybrid search (vector + keyword ready)
- Re-ranking for better results
- Metadata filtering
- Fast similarity search

**Use Case**: Find relevant document sections based on meaning, not just keywords

### 4. Gmail Integration (Ready)

**What it is**: Gmail API service for email collection

**Location**: `backend/services/gmail_service.py`

**Features**:
- OAuth2 authentication
- Email collection from inbox
- Attachment extraction
- Duplicate detection

**Status**: Implemented, requires Gmail API credentials

**Use Case**: Automatically collect case submissions from email

### 5. Persistent Storage

**What it is**: Database storage for all application data

**Features**:
- All cases saved to database
- Document storage with versioning
- Query history
- No data loss on refresh

**Use Case**: Data persists across sessions and server restarts

### 6. Background Processing

**What it is**: Async document processing that doesn't block API responses

**Features**:
- Non-blocking API responses
- Status tracking (NEW → PROCESSING → REVIEWED)
- Error isolation
- Separate database sessions

**Use Case**: Fast API responses while processing happens in background

### 7. Error Handling & Logging

**What it is**: Comprehensive error handling throughout the system

**Features**:
- User-friendly error messages
- Backend error logging
- Network error detection
- Graceful degradation

**Use Case**: Better debugging and user experience

---

## 10. TECHNICAL IMPROVEMENTS

### Error Handling

**Old Version**:
- Basic try-catch blocks
- Console errors only
- No user feedback
- Errors crash the app

**New Version**:
- Comprehensive error handling
- User-friendly error messages (in French)
- Backend error logging with stack traces
- Network error detection
- Graceful error recovery
- Error isolation (processing errors don't affect submissions)

### API Security

**Old Version**:
- API keys in browser code
- Keys exposed in client-side JavaScript
- Security risk

**New Version**:
- API keys in backend only
- Environment variable management
- Keys never sent to frontend
- Secure configuration

### Performance

**Old Version**:
- All processing in browser (blocking)
- Limited by browser capabilities
- No background processing
- Slow for large documents

**New Version**:
- Server-side processing
- Background tasks (non-blocking)
- Async operations
- Better resource management
- Scalable architecture

### Data Management

**Old Version**:
- In-memory only
- Data lost on refresh
- No relationships
- No history

**New Version**:
- Persistent database
- Proper data relationships (foreign keys)
- Query history
- Document versioning
- Status tracking

### Code Organization

**Old Version**:
- Frontend-only
- Simple structure
- All logic in components
- No separation of concerns

**New Version**:
- Full-stack architecture
- Modular services
- Clear separation of concerns
- Reusable components
- Well-organized file structure

### Scalability

**Old Version**:
- Limited by browser
- No horizontal scaling
- Single user focus

**New Version**:
- Server-side processing
- Database-backed
- Can scale horizontally
- Multi-user support ready

---

## 11. FILES ADDED/MODIFIED

### Added Files (37 new files)

#### Backend Core Files
- `backend/__init__.py`
- `backend/main.py` - FastAPI server
- `backend/config.py` - Configuration management
- `backend/requirements.txt` - Python dependencies
- `backend/start.sh` - Startup script
- `backend/README.md` - Backend documentation

#### Backend API Files
- `backend/api/__init__.py`
- `backend/api/routes.py` - API endpoints
- `backend/api/schemas.py` - Pydantic models

#### Backend Database Files
- `backend/database/__init__.py`
- `backend/database/db.py` - Database connection
- `backend/database/models.py` - SQLAlchemy models

#### Backend Service Files
- `backend/services/__init__.py`
- `backend/services/gmail_service.py` - Gmail integration
- `backend/services/document_processor.py` - PDF processing
- `backend/services/cleaning_service.py` - Text cleaning
- `backend/services/duplicate_detection.py` - Duplicate detection
- `backend/services/embedding_service.py` - Embeddings
- `backend/services/vector_store.py` - ChromaDB
- `backend/services/retrieval_service.py` - Search & re-ranking
- `backend/services/llm_service.py` - LLM inference
- `backend/services/rag_pipeline.py` - RAG orchestration
- `backend/services/processing_pipeline.py` - Processing orchestration

#### Frontend New Files
- `components/QueryInterface.tsx` - RAG query UI
- `services/apiClient.ts` - Backend API client

#### Documentation Files
- `documentation/before/Initial_app_documentation.txt` - Moved from root
- `documentation/before/TESTING_GUIDE.txt` - Testing documentation
- `documentation/now/API_KEYS_SETUP_GUIDE.md` - API setup guide
- `documentation/now/RAG_IMPLEMENTATION_SUMMARY.md` - RAG documentation

#### Helper Scripts
- `helper scripts/get_gmail_token.py` - Gmail OAuth helper
- `helper scripts/verify_env.py` - Environment verification

#### Configuration Files
- `.gitignore` - Git ignore rules

### Modified Files

#### Frontend
- `App.tsx` - Backend integration, dual-mode support
- `components/LawyerDashboard.tsx` - Added RAG Query tab
- `package.json` - Minor updates (if any)

#### Documentation
- `README.md` - Extensive updates with new architecture

### Moved Files
- `Initial_app_documentation.txt` → `documentation/before/Initial_app_documentation.txt`

### File Statistics

- **Total Files Added**: 37
- **Total Files Modified**: 3-4
- **Total Files Moved**: 1
- **Lines of Code Added**: ~5,265 lines
- **Lines of Code Removed**: ~66 lines
- **Net Change**: +5,199 lines

---

## 12. MIGRATION NOTES

### For End Users

#### Old Version Usage
- Just open HTML file or run `npm run dev`
- Works immediately
- No setup required
- Data lost on refresh

#### New Version Usage
1. **Start Backend First**:
   ```bash
   cd backend
   python main.py
   # Or use startup script:
   ./start.sh
   ```
2. **Start Frontend**:
   ```bash
   npm run dev
   ```
3. **Access Application**:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

**Important**: Backend must be running before using the frontend.

#### Data Migration
- Old version had no persistent data
- New version starts with empty database
- No migration needed (fresh start)

### For Developers

#### Setup Requirements

1. **Python Environment**:
   - Python 3.12+ required
   - Virtual environment recommended
   - Install dependencies: `pip install -r backend/requirements.txt`

2. **Environment Variables**:
   - Create `.env` file in project root
   - Configure API keys (see `API_KEYS_SETUP_GUIDE.md`)
   - Minimum required: `OPENAI_API_KEY` or `GROQ_API_KEY`

3. **Database**:
   - Auto-created on first run
   - Location: `./data/database.db`
   - No manual setup needed

4. **ChromaDB**:
   - Auto-created on first run
   - Location: `./data/chroma_db`
   - No manual setup needed

#### Development Workflow

1. **Start Backend**:
   ```bash
   cd backend
   python main.py
   ```
   - Server runs on port 8000
   - Auto-reload on code changes
   - Database auto-initializes

2. **Start Frontend**:
   ```bash
   npm run dev
   ```
   - Runs on port 3000
   - Connects to backend on port 8000

3. **Testing**:
   - Backend health: `curl http://localhost:8000/health`
   - API docs: `http://localhost:8000/docs`
   - Test submission via frontend form

#### Toggle Between Modes

In `App.tsx`, you can toggle between backend and direct Gemini:

```typescript
const [useBackend, setUseBackend] = useState<boolean>(true);
```

- `true`: Use backend API (default, recommended)
- `false`: Use direct Gemini API (old behavior)

#### Common Issues

1. **Backend not running**:
   - Error: "Cannot connect to backend"
   - Solution: Start backend server first

2. **Missing dependencies**:
   - Error: "No module named 'X'"
   - Solution: `pip install -r backend/requirements.txt`

3. **Database errors**:
   - Error: Database initialization failed
   - Solution: Check file permissions for `./data/` directory

4. **CORS errors**:
   - Error: CORS policy blocked
   - Solution: Check `CORS_ORIGINS` in `.env` matches frontend URL

---

## 13. WHAT REMAINS THE SAME

Despite the major architectural changes, several aspects remain unchanged:

### User Interface
- **Frontend UI/UX**: Mostly unchanged
- **Client Form**: Same layout and fields
- **Lawyer Dashboard**: Same layout (with new Query tab)
- **Styling**: Same Tailwind CSS styles
- **Icons**: Same Font Awesome icons

### User Experience
- **Client Form Submission**: Same flow for users
- **Case Status Workflow**: Same statuses (NEW → PROCESSING → REVIEWED → SENT)
- **Legal Stage System**: Same stages (CONTROL, RAPO, LITIGATION)
- **Draft Generation**: Same email and appeal draft generation

### Core Functionality
- **Gemini API Integration**: Still used (now via backend)
- **Case ID Format**: Same format (CAS-YYYY-XXX)
- **File Upload**: Same file upload mechanism
- **Form Validation**: Same validation rules

### Business Logic
- **Legal Domain**: Same (French administrative law, CAF)
- **Case Types**: Same (RSA, APL, Prime d'activité, etc.)
- **Workflow**: Same overall case management workflow

---

## 14. SUMMARY

### Old Version (e5b166c)

**Description**: Simple client-side React application with direct Gemini API calls.

**Characteristics**:
- No backend
- No persistence
- No document processing
- No search capability
- API keys in browser
- Prototype-level implementation

**Use Case**: Quick prototype for testing AI integration

### New Version (f36fe76)

**Description**: Full-stack application with FastAPI backend, SQLite database, complete document processing pipeline, RAG system with vector search, and persistent storage.

**Characteristics**:
- Complete backend infrastructure
- Persistent database
- Document processing pipeline
- RAG with vector search
- Secure API key management
- Production-ready architecture

**Use Case**: Production-ready legal case management system with AI-powered document search

### Key Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code Added** | ~5,265 lines |
| **New Files** | 37 files |
| **New Dependencies** | 41 Python packages |
| **New Features** | 7 major features |
| **Architecture Change** | Client-only → Full-stack |
| **Database Tables** | 4 new tables |
| **API Endpoints** | 6 new endpoints |
| **Services** | 10 new backend services |

### Transformation Impact

**Before**: Simple frontend prototype  
**After**: Sophisticated legal case management system

**Key Improvements**:
1. ✅ Data persistence
2. ✅ Document processing
3. ✅ Vector search
4. ✅ RAG pipeline
5. ✅ Security improvements
6. ✅ Scalability
7. ✅ Error handling
8. ✅ Background processing

### Conclusion

The transformation from commit e5b166c to f36fe76 represents a **complete architectural overhaul**. The application has evolved from a simple frontend prototype to a production-ready, full-stack legal case management system with advanced AI capabilities including document processing, vector search, and RAG (Retrieval-Augmented Generation).

The new architecture provides:
- **Persistence**: All data saved to database
- **Scalability**: Server-side processing
- **Security**: API keys secured in backend
- **Functionality**: Document search and RAG queries
- **Reliability**: Error handling and logging
- **Maintainability**: Modular, well-organized code

This transformation enables the application to handle real-world legal case management workflows with proper data persistence, document processing, and AI-powered search capabilities.

---

**Document End**

