"""
Session State Management

Holds global state for each learning session:
- Phase tracking (evaluator → teacher → quiz → review)
- Conversation histories for each phase
- Evaluation plan and scores
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class Phase(str, Enum):
    EVALUATOR = "evaluator"
    TEACHER = "teacher"
    QUIZ = "quiz"
    REVIEW = "review"


class Message(BaseModel):
    """A single message in a conversation."""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class EvaluationPlan(BaseModel):
    """The evaluation result/plan."""
    student_level: Literal["low", "medium", "high"]
    teaching_focus: str


class QuizResult(BaseModel):
    """Results from the quiz phase."""
    total_questions: int = 0
    correct_answers: int = 0
    score_percentage: float = 0.0
    time_taken_seconds: int = 0


class SessionState(BaseModel):
    """
    Complete state for a learning session.

    Tracks all 4 phases: Evaluator → Teacher → Quiz → Review
    """
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    phase: Phase = Phase.EVALUATOR

    # Evaluator phase
    evaluator_conversation: list[Message] = Field(default_factory=list)

    # Plan (generated after evaluation)
    plan: Optional[EvaluationPlan] = None

    # Teacher phase
    teacher_conversation: list[Message] = Field(default_factory=list)
    teacher_questions_asked: int = 0
    teacher_correct: int = 0
    current_difficulty: str = "medium"

    # Quiz phase
    quiz_conversation: list[Message] = Field(default_factory=list)
    quiz_result: Optional[QuizResult] = None

    # Review phase
    review_conversation: list[Message] = Field(default_factory=list)

    def add_message(self, phase: Phase, role: Literal["user", "assistant"], content: str) -> None:
        """Add a message to the appropriate phase conversation."""
        message = Message(role=role, content=content)
        if phase == Phase.EVALUATOR:
            self.evaluator_conversation.append(message)
        elif phase == Phase.TEACHER:
            self.teacher_conversation.append(message)
        elif phase == Phase.QUIZ:
            self.quiz_conversation.append(message)
        elif phase == Phase.REVIEW:
            self.review_conversation.append(message)

    def set_plan(self, student_level: str, teaching_focus: str) -> None:
        """Set the evaluation plan."""
        self.plan = EvaluationPlan(
            student_level=student_level,
            teaching_focus=teaching_focus
        )
        self.current_difficulty = {
            "low": "easy",
            "medium": "medium",
            "high": "hard"
        }.get(student_level, "medium")

    def transition_to(self, phase: Phase) -> None:
        """Transition to a new phase."""
        self.phase = phase

    def set_quiz_result(self, total: int, correct: int, time_seconds: int) -> None:
        """Set the quiz results."""
        self.quiz_result = QuizResult(
            total_questions=total,
            correct_answers=correct,
            score_percentage=(correct / total * 100) if total > 0 else 0,
            time_taken_seconds=time_seconds
        )

    def to_dict(self) -> dict:
        """Export state as dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "phase": self.phase.value,
            "evaluator_conversation": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.evaluator_conversation
            ],
            "plan": self.plan.model_dump() if self.plan else None,
            "teacher_conversation": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.teacher_conversation
            ],
            "quiz_conversation": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.quiz_conversation
            ],
            "quiz_result": self.quiz_result.model_dump() if self.quiz_result else None,
            "review_conversation": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                for m in self.review_conversation
            ],
            "stats": {
                "teacher_questions_asked": self.teacher_questions_asked,
                "teacher_correct": self.teacher_correct,
                "current_difficulty": self.current_difficulty
            }
        }


class SessionStore:
    """
    In-memory storage for session states.

    For production, this could be backed by Redis or a database.
    """

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def create(self, session_id: str) -> SessionState:
        """Create a new session."""
        state = SessionState(session_id=session_id)
        self._sessions[session_id] = state
        return state

    def get(self, session_id: str) -> Optional[SessionState]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> SessionState:
        """Get existing session or create new one."""
        if session_id not in self._sessions:
            return self.create(session_id)
        return self._sessions[session_id]

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return list(self._sessions.keys())

    def count(self) -> int:
        """Count active sessions."""
        return len(self._sessions)


# Global session store instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get the global session store instance."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
