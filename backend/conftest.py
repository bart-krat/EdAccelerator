"""
Root conftest for backend tests.

Provides shared fixtures and configuration for all tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for all tests."""
    with patch("openai.OpenAI") as mock:
        client = MagicMock()
        mock.return_value = client

        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"score": 3, "summary": "Good job!", "question_reviews": []}'
                )
            )
        ]
        client.chat.completions.create.return_value = mock_response

        yield client


@pytest.fixture
def mock_questions():
    """Mock question pools for tests."""
    with patch("evaluator.question_generator.load_questions") as mock:
        mock.return_value = {
            "easy": [
                {"id": 1, "question": "What is 2+2?", "answer": "4", "explanation": "Basic math"},
            ],
            "medium": [
                {"id": 2, "question": "What color is the sky?", "answer": "Blue", "explanation": "Look up"},
            ],
            "hard": [
                {"id": 3, "question": "Explain quantum physics", "answer": "Complex", "explanation": "Physics"},
            ],
        }
        yield mock


@pytest.fixture
def sample_session_state():
    """Sample session state data for testing."""
    return {
        "session_id": "test-session-123",
        "phase": "evaluator",
        "plan": None,
    }


@pytest.fixture
def sample_plan():
    """Sample evaluation plan for testing."""
    return {
        "student_level": "medium",
        "teaching_focus": "vocabulary and comprehension"
    }


@pytest.fixture
async def test_client(mock_openai, mock_questions):
    """Create async test client for API testing."""
    # Patch question initialization to avoid OpenAI calls
    with patch("main.initialize_questions"):
        from main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
