from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

class MongoDB:
    """MongoDB connection handler."""
    
    client: AsyncIOMotorClient = None
    db = None
    
    @classmethod
    async def connect_db(cls):
        """Create database connection."""
        if cls.client is None:
            try:
                cls.client = AsyncIOMotorClient(settings.mongodb_url)
                # Verify connection
                await cls.client.admin.command('ping')
                cls.db = cls.client.ilan_legal_app
                print(f"✓ Connected to MongoDB at {settings.mongodb_url} (db: ilan_legal_app)")
            except Exception as e:
                print(f"⚠️ MongoDB connection error: {e}")
                
    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            print("MongoDB connection closed.")

# Dependency for FastAPI
async def get_database():
    """Yield database instance."""
    if MongoDB.client is None:
        await MongoDB.connect_db()
    return MongoDB.db
