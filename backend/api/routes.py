"""
API Routes

Thin API layer that delegates to the SessionOrchestrator.
"""

import logging
import uuid
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
)
from shared.passage import PASSAGE
from orchestrator import get_orchestrator, create_orchestrator
from state import Phase

logger = logging.getLogger("api.routes")


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
    """Health check endpoint."""
    import os
    return HealthResponse(
        status="healthy",
        env=os.getenv("ENV", "development"),
        version="1.0.0"
    )


@system_router.get("/")
async def root():
    """API root."""
    return {
        "service": "EdAccelerator API",
        "version": "1.0.0",
        "phases": ["evaluator", "teacher", "quiz", "review"]
    }


@system_router.get("/passage", response_model=PassageResponse)
async def get_passage():
    """Get the reading passage."""
    return PassageResponse(**PASSAGE)


# ============================================================
# Session Endpoints
# ============================================================

@session_router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Start a new learning session.

    Creates session and returns first evaluator question.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Create orchestrator (manages entire session)
        orch = create_orchestrator(session_id)
        result = orch.get_intro()

        logger.info(f"Session started: {session_id[:8]}...")

        return StartSessionResponse(
            session_id=session_id,
            message=result["response"],
            mode=AgentMode(result["phase"])
        )
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")


@session_router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status and current phase."""
    try:
        orch = get_orchestrator(session_id)
        state = orch.get_state()

        return {
            "session_id": session_id,
            "phase": state["phase"],
            "plan": state["plan"],
            "stats": state["stats"]
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=404, detail="Session not found")


@session_router.get("/session/{session_id}/state")
async def get_session_state(session_id: str):
    """Get complete session state including all conversations."""
    try:
        orch = get_orchestrator(session_id)
        return orch.get_state()
    except Exception as e:
        logger.error(f"Error getting state: {e}")
        raise HTTPException(status_code=404, detail="Session not found")


@session_router.post("/session/{session_id}/skip")
async def skip_to_phase(session_id: str, target_phase: str):
    """Skip to a specific phase (for testing)."""
    try:
        phase_map = {
            "evaluator": Phase.EVALUATOR,
            "teacher": Phase.TEACHER,
            "quiz": Phase.QUIZ,
            "review": Phase.REVIEW
        }

        if target_phase not in phase_map:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {target_phase}")

        orch = get_orchestrator(session_id)
        result = orch.skip_to_phase(phase_map[target_phase])

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping phase: {e}")
        raise HTTPException(status_code=500, detail="Failed to skip phase")


# ============================================================
# Quiz Endpoint
# ============================================================

@session_router.post("/session/{session_id}/quiz/submit")
async def submit_quiz(session_id: str, answers: list[dict]):
    """
    Submit quiz answers and get results.

    Body: [{"question_id": 1, "answer": "user's answer"}, ...]
    """
    try:
        orch = get_orchestrator(session_id)
        result = orch.submit_quiz(answers)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit quiz")


# ============================================================
# Chat Endpoint
# ============================================================

@chat_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message in the current session phase.

    Automatically handles phase transitions.
    """
    try:
        orch = get_orchestrator(request.session_id)
        result = orch.process_message(request.message)

        return ChatResponse(
            response=result["response"],
            is_complete=result.get("session_complete", False),
            mode=AgentMode(result["phase"]),
            show_quiz=result.get("show_quiz"),
            quiz_data=result.get("quiz_data")
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")
