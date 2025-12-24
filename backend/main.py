"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api import routes
from backend.database.db import init_db
import asyncio

app = FastAPI(
    title="Ilan Legal App RAG Pipeline",
    description="Backend API for legal case management with RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api", tags=["api"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    # Log configuration status on startup
    from backend.config import log_config_status
    log_config_status()
    
    try:
        await init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        print("Server will continue, but database features may not work.")
        import traceback
        traceback.print_exc()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Ilan Legal App RAG Pipeline API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

