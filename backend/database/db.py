from backend.database.mongo import get_database

# Alias for backward compatibility with imports
get_db = get_database

async def init_db():
    """Dummy init_db for compatibility."""
    pass

# For compatibility with code that might try to import Base
Base = object 

# For compatibility with code importing AsyncSessionLocal
class MockSession:
    def __init__(self):
        pass
    async def __aenter__(self):
        return await get_database()
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

AsyncSessionLocal = MockSession
