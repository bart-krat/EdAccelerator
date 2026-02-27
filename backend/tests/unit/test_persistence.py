"""
Tests for MongoDB session persistence.

Tests graceful degradation when MongoDB is not configured.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from persistence.mongodb import SessionPersistence, get_persistence


class TestSessionPersistenceWithoutMongoDB:
    """Tests for when MongoDB is not configured."""

    def test_save_returns_false_without_uri(self):
        """Test that save returns False when MONGODB_URI is not set."""
        with patch.dict(os.environ, {}, clear=True):
            persistence = SessionPersistence()
            result = persistence.save_session({"session_id": "test-123"})
            assert result is False

    def test_get_session_returns_none_without_uri(self):
        """Test that get_session returns None when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            persistence = SessionPersistence()
            result = persistence.get_session("test-123")
            assert result is None

    def test_list_sessions_returns_empty_without_uri(self):
        """Test that list_sessions returns empty list when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            persistence = SessionPersistence()
            result = persistence.list_sessions()
            assert result == []

    def test_is_available_returns_false_without_uri(self):
        """Test that is_available returns False when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            persistence = SessionPersistence()
            assert persistence.is_available() is False

    def test_delete_returns_false_without_uri(self):
        """Test that delete returns False when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            persistence = SessionPersistence()
            result = persistence.delete_session("test-123")
            assert result is False


class TestSessionPersistenceWithMongoDB:
    """Tests for when MongoDB is configured (mocked)."""

    @pytest.fixture
    def mock_mongo(self):
        """Mock MongoDB client and collection."""
        with patch.dict(os.environ, {"MONGODB_URI": "mongodb://localhost:27017"}):
            with patch("persistence.mongodb.MongoClient") as mock_client:
                # Setup mock chain
                mock_collection = MagicMock()
                mock_db = MagicMock()
                mock_db.__getitem__ = MagicMock(return_value=mock_collection)

                mock_instance = MagicMock()
                mock_instance.__getitem__ = MagicMock(return_value=mock_db)
                mock_instance.admin.command = MagicMock(return_value=True)

                mock_client.return_value = mock_instance

                yield {
                    "client": mock_client,
                    "instance": mock_instance,
                    "db": mock_db,
                    "collection": mock_collection
                }

    def test_save_session_success(self, mock_mongo):
        """Test successful session save."""
        mock_mongo["collection"].update_one.return_value = MagicMock(upserted_id="new-id")

        persistence = SessionPersistence()
        result = persistence.save_session({
            "session_id": "test-123",
            "phase": "review",
            "plan": {"student_level": "medium"}
        })

        assert result is True
        mock_mongo["collection"].update_one.assert_called_once()

    def test_save_session_without_session_id(self, mock_mongo):
        """Test that save fails without session_id."""
        persistence = SessionPersistence()
        result = persistence.save_session({"phase": "review"})

        assert result is False

    def test_get_session_found(self, mock_mongo):
        """Test retrieving an existing session."""
        mock_mongo["collection"].find_one.return_value = {
            "_id": "mongo-id",
            "session_id": "test-123",
            "phase": "review"
        }

        persistence = SessionPersistence()
        result = persistence.get_session("test-123")

        assert result is not None
        assert result["session_id"] == "test-123"
        assert "_id" not in result  # _id should be removed

    def test_get_session_not_found(self, mock_mongo):
        """Test retrieving a non-existent session."""
        mock_mongo["collection"].find_one.return_value = None

        persistence = SessionPersistence()
        result = persistence.get_session("nonexistent")

        assert result is None

    def test_list_sessions(self, mock_mongo):
        """Test listing sessions."""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"_id": "1", "session_id": "session-1"},
            {"_id": "2", "session_id": "session-2"}
        ]
        mock_mongo["collection"].find.return_value = mock_cursor

        persistence = SessionPersistence()
        result = persistence.list_sessions(limit=10)

        assert len(result) == 2

    def test_delete_session_success(self, mock_mongo):
        """Test successful session deletion."""
        mock_mongo["collection"].delete_one.return_value = MagicMock(deleted_count=1)

        persistence = SessionPersistence()
        result = persistence.delete_session("test-123")

        assert result is True

    def test_delete_session_not_found(self, mock_mongo):
        """Test deleting non-existent session."""
        mock_mongo["collection"].delete_one.return_value = MagicMock(deleted_count=0)

        persistence = SessionPersistence()
        result = persistence.delete_session("nonexistent")

        assert result is False

    def test_is_available_with_connection(self, mock_mongo):
        """Test is_available returns True when connected."""
        persistence = SessionPersistence()
        assert persistence.is_available() is True

    def test_connection_failure_handling(self):
        """Test graceful handling of connection failures."""
        with patch.dict(os.environ, {"MONGODB_URI": "mongodb://invalid:27017"}):
            with patch("persistence.mongodb.MongoClient") as mock_client:
                from pymongo.errors import ServerSelectionTimeoutError
                mock_client.side_effect = ServerSelectionTimeoutError("timeout")

                persistence = SessionPersistence()
                assert persistence.is_available() is False
                assert persistence.save_session({"session_id": "test"}) is False


class TestGetPersistence:
    """Tests for get_persistence singleton."""

    def test_returns_same_instance(self):
        """Test that get_persistence returns singleton."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset the global
            import persistence.mongodb as pm
            pm._persistence = None

            p1 = get_persistence()
            p2 = get_persistence()

            assert p1 is p2

            # Cleanup
            pm._persistence = None
