"""
Session Persistence Module

Optional MongoDB persistence for completed sessions.
Gracefully degrades if MongoDB is not configured.
"""

from persistence.mongodb import SessionPersistence, get_persistence

__all__ = ["SessionPersistence", "get_persistence"]
