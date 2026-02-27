"""
MongoDB Session Persistence

Provides optional persistence for completed learning sessions.
If MONGODB_URI is not configured, operations are no-ops.

Usage:
    from persistence import get_persistence

    persistence = get_persistence()
    persistence.save_session(session_state.to_dict())
"""

import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger("persistence.mongodb")


class SessionPersistence:
    """
    MongoDB persistence for session data.

    Gracefully handles missing configuration - if MONGODB_URI is not set,
    all operations become no-ops and log informational messages.
    """

    def __init__(self):
        self._client = None
        self._db = None
        self._collection = None
        self._initialized = False
        self._available = False

    def _ensure_connected(self) -> bool:
        """
        Lazy initialization of MongoDB connection.

        Returns True if connection is available, False otherwise.
        """
        if self._initialized:
            return self._available

        self._initialized = True

        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            logger.info("MONGODB_URI not configured - session persistence disabled")
            return False

        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

            # Parse database name from URI or use default
            db_name = os.getenv("MONGODB_DATABASE", "edaccelerator")
            collection_name = os.getenv("MONGODB_COLLECTION", "sessions")

            # Connect with a short timeout to fail fast
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )

            # Test connection
            self._client.admin.command('ping')

            self._db = self._client[db_name]
            self._collection = self._db[collection_name]

            # Create index on session_id for faster lookups
            self._collection.create_index("session_id", unique=True)

            self._available = True
            logger.info(f"MongoDB connected: {db_name}.{collection_name}")
            return True

        except ImportError:
            logger.warning("pymongo not installed - session persistence disabled")
            return False
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"MongoDB connection failed: {e} - session persistence disabled")
            return False
        except Exception as e:
            logger.warning(f"MongoDB setup failed: {e} - session persistence disabled")
            return False

    def save_session(self, session_data: dict) -> bool:
        """
        Save a completed session to MongoDB.

        Args:
            session_data: Session state dictionary from SessionState.to_dict()

        Returns:
            True if saved successfully, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            session_id = session_data.get("session_id")
            if not session_id:
                logger.error("Cannot save session without session_id")
                return False

            # Add persistence metadata
            document = {
                **session_data,
                "persisted_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }

            # Upsert: update if exists, insert if new
            result = self._collection.update_one(
                {"session_id": session_id},
                {"$set": document},
                upsert=True
            )

            if result.upserted_id:
                logger.info(f"Session {session_id[:8]}... persisted (new)")
            else:
                logger.info(f"Session {session_id[:8]}... persisted (updated)")

            return True

        except Exception as e:
            logger.error(f"Failed to persist session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve a persisted session by ID.

        Args:
            session_id: The session identifier

        Returns:
            Session data dict or None if not found
        """
        if not self._ensure_connected():
            return None

        try:
            document = self._collection.find_one({"session_id": session_id})
            if document:
                # Remove MongoDB's _id field for cleaner data
                document.pop("_id", None)
                return document
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve session: {e}")
            return None

    def list_sessions(self, limit: int = 100) -> list[dict]:
        """
        List recent persisted sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        if not self._ensure_connected():
            return []

        try:
            cursor = self._collection.find(
                {},
                {
                    "session_id": 1,
                    "created_at": 1,
                    "phase": 1,
                    "plan": 1,
                    "quiz_result": 1,
                    "persisted_at": 1
                }
            ).sort("persisted_at", -1).limit(limit)

            sessions = []
            for doc in cursor:
                doc.pop("_id", None)
                sessions.append(doc)
            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a persisted session.

        Args:
            session_id: The session identifier

        Returns:
            True if deleted, False otherwise
        """
        if not self._ensure_connected():
            return False

        try:
            result = self._collection.delete_one({"session_id": session_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def is_available(self) -> bool:
        """Check if persistence is available."""
        return self._ensure_connected()

    def close(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._available = False
            logger.info("MongoDB connection closed")


# Global singleton instance
_persistence: Optional[SessionPersistence] = None


def get_persistence() -> SessionPersistence:
    """Get the global persistence instance."""
    global _persistence
    if _persistence is None:
        _persistence = SessionPersistence()
    return _persistence
