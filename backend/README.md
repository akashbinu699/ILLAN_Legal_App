# Ilan Legal App - Backend RAG Pipeline

This is the Python backend for the Ilan Legal App, implementing a complete RAG (Retrieval-Augmented Generation) pipeline for legal case management.

> **📖 For complete setup instructions, see the main [README.md](../README.md)**

## Quick Start

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root. See the main README or [`../documentation/now/API_KEYS_SETUP_GUIDE.md`](../documentation/now/API_KEYS_SETUP_GUIDE.md) for detailed instructions.

**Required:**
- `GROQ_API_KEY` or `OPENAI_API_KEY` (for LLM)
- `GEMINI_API_KEY` (for frontend, but backend may use it too)

**Optional:**
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` (for email collection)
- `RERANKER_API_KEY` (Cohere, for improved search quality)
- `DATABASE_PATH`, `CHROMA_DB_PATH` (defaults usually work)

### 3. Run the Backend

From the project root:

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the startup script:

```bash
cd backend
./start.sh
```

The API will be available at `http://localhost:8000`

**Verify it's working:**
- Visit http://localhost:8000/health
- Visit http://localhost:8000/docs for interactive API documentation

## API Endpoints

- `POST /api/submit` - Submit a new case
- `GET /api/cases` - Get all cases
- `GET /api/case/{case_id}` - Get specific case
- `POST /api/query` - RAG query endpoint

## Architecture

### Services

- **gmail_service.py**: Gmail API integration for email collection
- **document_processor.py**: PDF/image processing using Unstructured.io
- **cleaning_service.py**: Text cleaning with MarkItDown
- **embedding_service.py**: Embeddings with Late Chunking strategy
- **vector_store.py**: ChromaDB vector storage
- **retrieval_service.py**: Hybrid search and re-ranking
- **llm_service.py**: LLM inference (local or cloud)
- **rag_pipeline.py**: LangGraph orchestration
- **processing_pipeline.py**: Complete processing pipeline

### Database Schema

- **submissions**: Client form submissions
- **documents**: Processed documents
- **chunks**: Document chunks with embedding metadata
- **queries**: Query history

## RAG Pipeline Flow

1. **Submission** → Form data received
2. **Document Processing** → PDFs extracted to text
3. **Cleaning** → Text standardized
4. **Vectorization** → Late Chunking with embeddings
5. **Storage** → Vectors stored in ChromaDB
6. **Query** → Hybrid search + re-ranking
7. **Generation** → LLM generates answer with citations
8. **Critique** → Second LLM validates answer
9. **Revision** → Loop back if needed

## Notes

- The backend runs independently from the React frontend
- All processing happens asynchronously
- ChromaDB stores vectors persistently in `./data/chroma_db`
- SQLite database stores metadata in `./data/database.db`

