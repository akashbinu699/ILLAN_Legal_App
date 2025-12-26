"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.config import settings

# Create async engine for SQLite
database_url = f"sqlite+aiosqlite:///{settings.database_path}"
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False}
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables and run migrations."""
    async with engine.begin() as conn:
        # Create all tables (if they don't exist)
        await conn.run_sync(Base.metadata.create_all)
        
        # Run migrations to add new columns if they don't exist
        await migrate_database(conn)

async def migrate_database(conn):
    """Add new columns to existing tables if they don't exist."""
    from sqlalchemy import text
    
    # Check if submissions table exists and add new columns
    try:
        # Check if columns exist by trying to select them
        result = await conn.execute(text("PRAGMA table_info(submissions)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add new columns if they don't exist
        if 'generated_email_draft' not in columns:
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN generated_email_draft TEXT"))
            print("✓ Added generated_email_draft column")
        
        if 'generated_appeal_draft' not in columns:
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN generated_appeal_draft TEXT"))
            print("✓ Added generated_appeal_draft column")
        
        if 'email_prompt' not in columns:
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN email_prompt TEXT"))
            print("✓ Added email_prompt column")
        
        if 'appeal_prompt' not in columns:
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN appeal_prompt TEXT"))
            print("✓ Added appeal_prompt column")
        
        if 'cas_number' not in columns:
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN cas_number INTEGER"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_submissions_cas_number ON submissions(cas_number)"))
            print("✓ Added cas_number column")
    except Exception as e:
        # Table might not exist yet, which is fine
        print(f"Migration check: {e}")
    
    # Check if queries table exists and add submission_id column
    try:
        result = await conn.execute(text("PRAGMA table_info(queries)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'submission_id' not in columns:
            await conn.execute(text("ALTER TABLE queries ADD COLUMN submission_id INTEGER"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_queries_submission_id ON queries(submission_id)"))
            print("✓ Added submission_id column to queries")
        
        if 'submission_ids' not in columns:
            await conn.execute(text("ALTER TABLE queries ADD COLUMN submission_ids TEXT"))  # JSON stored as TEXT in SQLite
            print("✓ Added submission_ids column to queries")
    except Exception as e:
        # Table might not exist yet, which is fine
        print(f"Migration check for queries: {e}")

