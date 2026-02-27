"""
Tests for API schemas (Pydantic models).

Tests request/response validation and serialization.
"""

import pytest
from pydantic import ValidationError

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.schemas import (
    AgentMode,
    StartSessionRequest,
    StartSessionResponse,
    ChatRequest,
    ChatResponse,
    QuizQuestion,
    QuizData,
    HealthResponse,
    PassageResponse,
)


class TestAgentModeEnum:
    """Tests for AgentMode enum."""

    def test_agent_mode_values(self):
        """Test AgentMode enum has correct values."""
        assert AgentMode.EVALUATOR.value == "evaluator"
        assert AgentMode.TEACHER.value == "teacher"
        assert AgentMode.QUIZ.value == "quiz"
        assert AgentMode.REVIEW.value == "review"

    def test_agent_mode_from_string(self):
        """Test creating AgentMode from string."""
        assert AgentMode("evaluator") == AgentMode.EVALUATOR
        assert AgentMode("teacher") == AgentMode.TEACHER


class TestStartSessionRequest:
    """Tests for StartSessionRequest model."""

    def test_request_with_session_id(self):
        """Test request with explicit session ID."""
        req = StartSessionRequest(session_id="my-custom-id")

        assert req.session_id == "my-custom-id"

    def test_request_without_session_id(self):
        """Test request without session ID defaults to None."""
        req = StartSessionRequest()

        assert req.session_id is None


class TestStartSessionResponse:
    """Tests for StartSessionResponse model."""

    def test_response_creation(self):
        """Test creating a valid response."""
        resp = StartSessionResponse(
            session_id="test-123",
            message="Welcome!",
            mode=AgentMode.EVALUATOR
        )

        assert resp.session_id == "test-123"
        assert resp.message == "Welcome!"
        assert resp.mode == AgentMode.EVALUATOR


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_valid_chat_request(self):
        """Test valid chat request."""
        req = ChatRequest(session_id="session-123", message="Hello there")

        assert req.session_id == "session-123"
        assert req.message == "Hello there"

    def test_chat_request_requires_session_id(self):
        """Test that session_id is required."""
        with pytest.raises(ValidationError):
            ChatRequest(message="Hello")

    def test_chat_request_requires_message(self):
        """Test that message is required."""
        with pytest.raises(ValidationError):
            ChatRequest(session_id="session-123")

    def test_chat_request_message_min_length(self):
        """Test that message must have at least 1 character."""
        with pytest.raises(ValidationError):
            ChatRequest(session_id="session-123", message="")


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_basic_response(self):
        """Test creating a basic chat response."""
        resp = ChatResponse(
            response="Hello!",
            is_complete=False,
            mode=AgentMode.EVALUATOR
        )

        assert resp.response == "Hello!"
        assert resp.is_complete is False
        assert resp.mode == AgentMode.EVALUATOR
        assert resp.show_quiz is None
        assert resp.quiz_data is None

    def test_response_with_quiz_data(self):
        """Test chat response with quiz data."""
        quiz_data = QuizData(
            total_questions=5,
            time_limit_seconds=300,
            questions=[
                QuizQuestion(id=1, question="Test?", difficulty="easy")
            ]
        )

        resp = ChatResponse(
            response="Time for quiz!",
            is_complete=False,
            mode=AgentMode.QUIZ,
            show_quiz=True,
            quiz_data=quiz_data
        )

        assert resp.show_quiz is True
        assert resp.quiz_data.total_questions == 5


class TestQuizQuestion:
    """Tests for QuizQuestion model."""

    def test_quiz_question_creation(self):
        """Test creating a quiz question."""
        q = QuizQuestion(id=1, question="What is 2+2?", difficulty="easy")

        assert q.id == 1
        assert q.question == "What is 2+2?"
        assert q.difficulty == "easy"


class TestQuizData:
    """Tests for QuizData model."""

    def test_quiz_data_creation(self):
        """Test creating quiz data."""
        data = QuizData(
            total_questions=3,
            time_limit_seconds=180,
            questions=[
                QuizQuestion(id=1, question="Q1?", difficulty="easy"),
                QuizQuestion(id=2, question="Q2?", difficulty="medium"),
                QuizQuestion(id=3, question="Q3?", difficulty="hard"),
            ]
        )

        assert data.total_questions == 3
        assert data.time_limit_seconds == 180
        assert len(data.questions) == 3


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_health_response(self):
        """Test creating a health response."""
        resp = HealthResponse(
            status="healthy",
            env="development",
            version="1.0.0"
        )

        assert resp.status == "healthy"
        assert resp.env == "development"
        assert resp.version == "1.0.0"


class TestPassageResponse:
    """Tests for PassageResponse model."""

    def test_passage_response(self):
        """Test creating a passage response."""
        resp = PassageResponse(
            title="Test Passage",
            content="This is test content.",
            difficulty="medium"
        )

        assert resp.title == "Test Passage"
        assert resp.content == "This is test content."
        assert resp.difficulty == "medium"
