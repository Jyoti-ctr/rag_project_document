"""
database.py
-----------
MongoDB connection management using Motor (async driver).

Exposes:
    - connect_to_mongo(): open the client connection (called on startup)
    - close_mongo_connection(): close the client connection (called on shutdown)
    - get_database(): dependency-friendly accessor for the database instance
    - ensure_indexes(): create all required indexes on startup
    - collections helpers (users, documents, chunks, error_logs)
"""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)


class MongoManager:
    """Holds the singleton Motor client / database references."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongo_manager = MongoManager()


async def connect_to_mongo() -> None:
    """Create the Motor client and verify connectivity."""
    logger.info("Connecting to MongoDB at %s", settings.MONGO_URI)
    mongo_manager.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongo_manager.db = mongo_manager.client[settings.MONGO_DB_NAME]

    # Verify the connection is alive.
    await mongo_manager.client.admin.command("ping")
    logger.info("MongoDB connection established.")


async def close_mongo_connection() -> None:
    """Close the Motor client connection gracefully."""
    if mongo_manager.client is not None:
        mongo_manager.client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the active database instance.
    Used as a FastAPI dependency inside services/routes.
    """
    if mongo_manager.db is None:
        raise RuntimeError("Database has not been initialized. Did the app start up correctly?")
    return mongo_manager.db


# ---------------------------------------------------------------------------
# Collection accessors
# ---------------------------------------------------------------------------
def get_users_collection():
    return get_database()["users"]


def get_documents_collection():
    return get_database()["documents"]


def get_chunks_collection():
    return get_database()["chunks"]


def get_error_logs_collection():
    return get_database()["error_logs"]


# ---------------------------------------------------------------------------
# Index creation
# ---------------------------------------------------------------------------
async def ensure_indexes() -> None:
    """
    Creates all required indexes. Safe to call on every startup;
    MongoDB is idempotent for identical index creation calls.
    """
    users = get_users_collection()
    documents = get_documents_collection()
    chunks = get_chunks_collection()
    error_logs = get_error_logs_collection()

    await users.create_index("email", unique=True)
    await documents.create_index("user_id")
    await chunks.create_index("document_id")
    await chunks.create_index("user_id")
    await error_logs.create_index("timestamp")

    logger.info("MongoDB indexes ensured.")
