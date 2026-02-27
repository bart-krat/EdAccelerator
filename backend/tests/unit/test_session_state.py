"""
Tests for SessionState and SessionStore classes.

Tests state management, phase transitions, and serialization.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from state.session_state import (
    SessionState,
    SessionStore,
    Phase,
    Message,
    EvaluationPlan,
    QuizResult,
)


class TestSessionState:
    """Tests for SessionState model."""

    def test_create_session_state(self):
        """Test creating a new SessionState with defaults."""
        state = SessionState(session_id="test-123")

        assert state.session_id == "test-123"
        assert state.phase == Phase.EVALUATOR
        assert state.plan is None
        assert state.evaluator_conversation == []
        assert state.teacher_conversation == []
        assert state.quiz_conversation == []
        assert state.review_conversation == []
        assert state.teacher_questions_asked == 0
        assert state.current_difficulty == "medium"

    def test_add_message_to_evaluator_phase(self):
        """Test adding messages to evaluator conversation."""
        state = SessionState(session_id="test-123")

        state.add_message(Phase.EVALUATOR, "user", "Hello!")
        state.add_message(Phase.EVALUATOR, "assistant", "Hi there!")

        assert len(state.evaluator_conversation) == 2
        assert state.evaluator_conversation[0].role == "user"
        assert state.evaluator_conversation[0].content == "Hello!"
        assert state.evaluator_conversation[1].role == "assistant"
        assert state.evaluator_conversation[1].content == "Hi there!"

    def test_add_message_to_teacher_phase(self):
        """Test adding messages to teacher conversation."""
        state = SessionState(session_id="test-123")

        state.add_message(Phase.TEACHER, "assistant", "Let's practice!")
        state.add_message(Phase.TEACHER, "user", "Okay!")

        assert len(state.teacher_conversation) == 2
        assert state.teacher_conversation[0].content == "Let's practice!"

    def test_add_message_to_quiz_phase(self):
        """Test adding messages to quiz conversation."""
        state = SessionState(session_id="test-123")

        state.add_message(Phase.QUIZ, "assistant", "Question 1...")

        assert len(state.quiz_conversation) == 1
        assert state.quiz_conversation[0].content == "Question 1..."

    def test_add_message_to_review_phase(self):
        """Test adding messages to review conversation."""
        state = SessionState(session_id="test-123")

        state.add_message(Phase.REVIEW, "assistant", "Great job!")

        assert len(state.review_conversation) == 1
        assert state.review_conversation[0].content == "Great job!"

    def test_set_plan(self):
        """Test setting the evaluation plan."""
        state = SessionState(session_id="test-123")

        state.set_plan(student_level="high", teaching_focus="advanced concepts")

        assert state.plan is not None
        assert state.plan.student_level == "high"
        assert state.plan.teaching_focus == "advanced concepts"
        assert state.current_difficulty == "hard"

    def test_set_plan_updates_difficulty(self):
        """Test that set_plan correctly maps student level to difficulty."""
        state = SessionState(session_id="test-123")

        # Test low level -> easy difficulty
        state.set_plan(student_level="low", teaching_focus="basics")
        assert state.current_difficulty == "easy"

        # Test medium level -> medium difficulty
        state.set_plan(student_level="medium", teaching_focus="intermediate")
        assert state.current_difficulty == "medium"

        # Test high level -> hard difficulty
        state.set_plan(student_level="high", teaching_focus="advanced")
        assert state.current_difficulty == "hard"

    def test_transition_to_phase(self):
        """Test transitioning between phases."""
        state = SessionState(session_id="test-123")

        assert state.phase == Phase.EVALUATOR

        state.transition_to(Phase.TEACHER)
        assert state.phase == Phase.TEACHER

        state.transition_to(Phase.QUIZ)
        assert state.phase == Phase.QUIZ

        state.transition_to(Phase.REVIEW)
        assert state.phase == Phase.REVIEW

    def test_set_quiz_result(self):
        """Test setting quiz results."""
        state = SessionState(session_id="test-123")

        state.set_quiz_result(total=10, correct=7, time_seconds=300)

        assert state.quiz_result is not None
        assert state.quiz_result.total_questions == 10
        assert state.quiz_result.correct_answers == 7
        assert state.quiz_result.score_percentage == 70.0
        assert state.quiz_result.time_taken_seconds == 300

    def test_set_quiz_result_zero_total(self):
        """Test quiz result with zero total questions."""
        state = SessionState(session_id="test-123")

        state.set_quiz_result(total=0, correct=0, time_seconds=0)

        assert state.quiz_result.score_percentage == 0.0

    def test_to_dict_serialization(self):
        """Test converting state to dictionary."""
        state = SessionState(session_id="test-123")
        state.add_message(Phase.EVALUATOR, "user", "Hello")
        state.set_plan(student_level="medium", teaching_focus="vocabulary")

        result = state.to_dict()

        assert result["session_id"] == "test-123"
        assert result["phase"] == "evaluator"
        assert "created_at" in result
        assert len(result["evaluator_conversation"]) == 1
        assert result["plan"]["student_level"] == "medium"
        assert result["stats"]["current_difficulty"] == "medium"

    def test_to_dict_without_plan(self):
        """Test to_dict when plan is not set."""
        state = SessionState(session_id="test-123")

        result = state.to_dict()

        assert result["plan"] is None

    def test_to_dict_without_quiz_result(self):
        """Test to_dict when quiz result is not set."""
        state = SessionState(session_id="test-123")

        result = state.to_dict()

        assert result["quiz_result"] is None


class TestSessionStore:
    """Tests for SessionStore class."""

    def test_create_session(self):
        """Test creating a new session."""
        store = SessionStore()

        session = store.create("new-session")

        assert session.session_id == "new-session"
        assert session.phase == Phase.EVALUATOR

    def test_get_existing_session(self):
        """Test retrieving an existing session."""
        store = SessionStore()
        store.create("my-session")

        session = store.get("my-session")

        assert session is not None
        assert session.session_id == "my-session"

    def test_get_nonexistent_session(self):
        """Test retrieving a session that doesn't exist."""
        store = SessionStore()

        session = store.get("nonexistent")

        assert session is None

    def test_get_or_create_new_session(self):
        """Test get_or_create creates new session when needed."""
        store = SessionStore()

        session = store.get_or_create("new-session")

        assert session.session_id == "new-session"

    def test_get_or_create_existing_session(self):
        """Test get_or_create returns existing session."""
        store = SessionStore()
        original = store.create("my-session")
        original.transition_to(Phase.TEACHER)

        retrieved = store.get_or_create("my-session")

        assert retrieved.phase == Phase.TEACHER

    def test_delete_session(self):
        """Test deleting a session."""
        store = SessionStore()
        store.create("to-delete")

        result = store.delete("to-delete")

        assert result is True
        assert store.get("to-delete") is None

    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        store = SessionStore()

        result = store.delete("nonexistent")

        assert result is False

    def test_list_sessions(self):
        """Test listing all session IDs."""
        store = SessionStore()
        store.create("session-1")
        store.create("session-2")
        store.create("session-3")

        sessions = store.list_sessions()

        assert len(sessions) == 3
        assert "session-1" in sessions
        assert "session-2" in sessions
        assert "session-3" in sessions

    def test_count_sessions(self):
        """Test counting active sessions."""
        store = SessionStore()

        assert store.count() == 0

        store.create("session-1")
        assert store.count() == 1

        store.create("session-2")
        assert store.count() == 2

        store.delete("session-1")
        assert store.count() == 1


class TestPhaseEnum:
    """Tests for Phase enum."""

    def test_phase_values(self):
        """Test Phase enum has correct values."""
        assert Phase.EVALUATOR.value == "evaluator"
        assert Phase.TEACHER.value == "teacher"
        assert Phase.QUIZ.value == "quiz"
        assert Phase.REVIEW.value == "review"

    def test_phase_comparison(self):
        """Test Phase enum comparison."""
        assert Phase.EVALUATOR == Phase.EVALUATOR
        assert Phase.EVALUATOR != Phase.TEACHER


class TestMessage:
    """Tests for Message model."""

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = Message(role="user", content="Hello!")

        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = Message(role="assistant", content="Hi there!")

        assert msg.role == "assistant"
        assert msg.content == "Hi there!"
