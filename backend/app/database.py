import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URI

logger = logging.getLogger("uvicorn.error")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

def get_database():
    return db_instance.db

async def connect_db():
    try:
        db_instance.client = AsyncIOMotorClient(MONGODB_URI)
        # Extract database name from URI, defaulting to 'quizmaster'
        parts = MONGODB_URI.split("/")
        db_name = "quizmaster"
        if len(parts) > 3:
            db_name = parts[-1].split("?")[0] or "quizmaster"
        db_instance.db = db_instance.client[db_name]
        # Test connection by pinging
        await db_instance.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: '{db_name}'")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_db():
    if db_instance.client:
        db_instance.client.close()
        logger.info("Closed MongoDB connection.")
