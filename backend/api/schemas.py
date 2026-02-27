"""
API Schemas

Pydantic models for request/response validation.
Centralizes all API contracts for consistency and documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class AgentMode(str, Enum):
    """Current phase of the learning session."""
    EVALUATOR = "evaluator"
    TEACHER = "teacher"
    QUIZ = "quiz"
    REVIEW = "review"


# ============================================================
# Session Endpoints
# ============================================================

class StartSessionRequest(BaseModel):
    """Request to start a new learning session."""
    session_id: Optional[str] = Field(
        default=None,
        description="Optional custom session ID. If not provided, one will be generated."
    )


class StartSessionResponse(BaseModel):
    """Response after starting a session."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="Initial message from the tutor")
    mode: AgentMode = Field(..., description="Current agent mode")


# ============================================================
# Chat Endpoints
# ============================================================

class ChatRequest(BaseModel):
    """Request to send a message in an active session."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., min_length=1, description="User's message")


class QuizQuestion(BaseModel):
    """A quiz question (without answer for frontend)."""
    id: int
    question: str
    difficulty: str


class QuizData(BaseModel):
    """Quiz data sent to frontend."""
    total_questions: int
    time_limit_seconds: int
    questions: List[QuizQuestion]


class ChatResponse(BaseModel):
    """Response from the tutor."""
    response: str = Field(..., description="Tutor's response message")
    is_complete: bool = Field(..., description="Whether session is complete")
    mode: AgentMode = Field(..., description="Current phase")
    show_quiz: Optional[bool] = Field(default=None, description="Whether to show quiz UI")
    quiz_data: Optional[QuizData] = Field(default=None, description="Quiz questions if show_quiz is true")


# ============================================================
# Session Status Endpoints
# ============================================================

class EvaluationProgress(BaseModel):
    """Progress through the evaluation questions."""
    current_question: int
    total_questions: int
    answers_collected: int
    is_complete: bool


class TeachingSummary(BaseModel):
    """Summary of the teaching session."""
    session_id: str
    questions_asked: int
    total_answers: int
    correct_answers: float
    accuracy: float
    final_difficulty: str
    conversation_turns: int


class SessionStatusResponse(BaseModel):
    """Full session status for debugging/monitoring."""
    session_id: str
    mode: AgentMode
    plan: Optional[dict] = None
    evaluation_progress: Optional[EvaluationProgress] = None
    teaching_summary: Optional[TeachingSummary] = None


# ============================================================
# Health & System Endpoints
# ============================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service health status")
    env: str = Field(..., description="Current environment")
    version: str = Field(..., description="API version")


class PassageResponse(BaseModel):
    """Reading passage data."""
    title: str
    content: str
    difficulty: str
