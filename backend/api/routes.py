"""
API Routes

Endpoint definitions for the EdAccelerator API.
Routes are organized by domain: sessions, chat, system.
"""

import logging
import uuid
import yaml
from typing import Optional
from fastapi import APIRouter, HTTPException

from api.schemas import (
    StartSessionRequest,
    StartSessionResponse,
    ChatRequest,
    ChatResponse,
    SessionStatusResponse,
    HealthResponse,
    PassageResponse,
    AgentMode,
    EvaluationProgress,
    TeachingSummary,
)
from shared.passage import PASSAGE
from evaluator.orchestrator import EvaluatorOrchestrator
from teacher.agent import TeacherAgent

logger = logging.getLogger("api.routes")

# ============================================================
# Session Storage
# ============================================================

class Session:
    """Represents an active learning session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.mode: AgentMode = AgentMode.EVALUATOR
        self.evaluator: Optional[EvaluatorOrchestrator] = None
        self.teacher: Optional[TeacherAgent] = None
        self.plan: Optional[dict] = None


# In-memory session storage (use Redis for production scale)
sessions: dict[str, Session] = {}


# ============================================================
# Routers
# ============================================================

system_router = APIRouter(tags=["System"])
session_router = APIRouter(tags=["Sessions"])
chat_router = APIRouter(tags=["Chat"])


# ============================================================
# System Endpoints
# ============================================================

@system_router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and deployment verification.
    """
    import os
    return HealthResponse(
        status="healthy",
        env=os.getenv("ENV", "development"),
        version="1.0.0"
    )


@system_router.get("/", response_model=dict)
async def root():
    """
    API root - basic service info.
    """
    import os
    return {
        "service": "EdAccelerator API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@system_router.get("/passage", response_model=PassageResponse)
async def get_passage():
    """
    Get the current reading passage.
    """
    return PassageResponse(**PASSAGE)


# ============================================================
# Session Endpoints
# ============================================================

@session_router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Start a new learning session.
    
    Creates a new session and returns the first evaluation question.
    The session progresses through evaluation → teaching phases automatically.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Create session
        session = Session(session_id)
        session.evaluator = EvaluatorOrchestrator(
            PASSAGE["title"],
            PASSAGE["content"],
            session_id
        )
        sessions[session_id] = session

        intro = session.evaluator.get_intro_message()

        logger.info(f"📗 Session started: {session_id[:8]}...")

        return StartSessionResponse(
            session_id=session_id,
            message=intro,
            mode=AgentMode.EVALUATOR
        )
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")


@session_router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get the current status of a session.
    
    Returns mode, progress, and plan (if evaluation complete).
    Useful for debugging and session recovery.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    response = SessionStatusResponse(
        session_id=session_id,
        mode=session.mode,
        plan=session.plan
    )

    if session.mode == AgentMode.TEACHER and session.teacher:
        summary = session.teacher.get_session_summary()
        response.teaching_summary = TeachingSummary(**summary)
    elif session.mode == AgentMode.EVALUATOR and session.evaluator:
        progress = session.evaluator.get_progress()
        response.evaluation_progress = EvaluationProgress(**progress)

    return response


# ============================================================
# Chat Endpoints
# ============================================================

@chat_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message in an active session.
    
    Routes to the appropriate agent (evaluator or teacher) based on session state.
    Automatically transitions from evaluator to teacher when evaluation completes.
    """
    try:
        # Get or create session
        if request.session_id not in sessions:
            session = Session(request.session_id)
            session.evaluator = EvaluatorOrchestrator(
                PASSAGE["title"],
                PASSAGE["content"],
                request.session_id
            )
            sessions[request.session_id] = session
            
            return ChatResponse(
                response=session.evaluator.get_intro_message(),
                is_complete=False,
                mode=AgentMode.EVALUATOR
            )

        session = sessions[request.session_id]

        # Route based on current mode
        if session.mode == AgentMode.EVALUATOR:
            return await _handle_evaluator(session, request.message)
        else:
            return await _handle_teacher(session, request.message)

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


async def _handle_evaluator(session: Session, message: str) -> ChatResponse:
    """Handle message during evaluation phase."""
    
    result = session.evaluator.process_message(message)

    # Check if evaluation is complete
    if result["is_complete"]:
        # Parse the plan
        session.plan = yaml.safe_load(result["plan_yaml"])

        # Transition to teacher mode
        session.mode = AgentMode.TEACHER
        session.teacher = TeacherAgent(
            PASSAGE["title"],
            PASSAGE["content"],
            session.session_id,
            session.plan
        )

        # Get teacher's intro
        teacher_intro = session.teacher.get_intro_message()

        logger.info(f"📘 Session {session.session_id[:8]}... → Teacher mode")

        return ChatResponse(
            response=result["response"] + "\n\n" + teacher_intro,
            is_complete=False,
            mode=AgentMode.TEACHER
        )

    return ChatResponse(
        response=result["response"],
        is_complete=False,
        mode=AgentMode.EVALUATOR
    )


async def _handle_teacher(session: Session, message: str) -> ChatResponse:
    """Handle message during teaching phase."""
    
    result = session.teacher.process_message(message)

    return ChatResponse(
        response=result["response"],
        is_complete=False,
        mode=AgentMode.TEACHER
    )
