"""
Session Orchestrator

Single orchestrator that manages the complete 4-phase learning session:
1. EVALUATOR - Assess student level (6 questions → plan)
2. TEACHER   - Adaptive practice based on plan
3. QUIZ      - Timed assessment
4. REVIEW    - Summary and next steps

All state is managed through SessionState.
"""

import logging
import yaml
from typing import Optional

from state import SessionState, get_session_store, Phase
from shared.passage import PASSAGE

# Import agents
from evaluator.orchestrator import EvaluatorOrchestrator
from teacher.agent import TeacherAgent
from quiz.generator import QuizGenerator, Quiz
from evaluator.question_generator import load_questions
from persistence import get_persistence

logger = logging.getLogger("orchestrator")


class SessionOrchestrator:
    """
    Unified orchestrator for the complete 4-phase learning session.

    Phases:
        EVALUATOR → TEACHER (10 questions) → QUIZ → REVIEW

    Each phase has its own agent that handles the conversation logic.
    The orchestrator manages state and transitions between phases.
    """

    # Transition rules
    PHASE_ORDER = [Phase.EVALUATOR, Phase.TEACHER, Phase.QUIZ, Phase.REVIEW]
    TEACHER_QUESTIONS_BEFORE_QUIZ = 5  # Transition to quiz after N teacher questions

    def __init__(self, session_id: str):
        self.session_id = session_id

        # Get or create session state
        store = get_session_store()
        self.state = store.get_or_create(session_id)

        # Agent instances (lazy loaded)
        self._evaluator: Optional[EvaluatorOrchestrator] = None
        self._teacher: Optional[TeacherAgent] = None
        self._quiz: Optional[Quiz] = None
        self._quiz_current_index: int = 0
        self._review = None  # TODO: ReviewAgent

        logger.info(f"Orchestrator initialized: {session_id[:8]}... (phase: {self.state.phase.value})")

    # ============================================================
    # Properties
    # ============================================================

    @property
    def phase(self) -> str:
        """Current phase name."""
        return self.state.phase.value

    @property
    def plan(self) -> Optional[dict]:
        """Evaluation plan (available after evaluator phase)."""
        return self.state.plan.model_dump() if self.state.plan else None

    # ============================================================
    # Agent Initialization
    # ============================================================

    def _get_evaluator(self) -> EvaluatorOrchestrator:
        """Get or create the evaluator agent."""
        if self._evaluator is None:
            self._evaluator = EvaluatorOrchestrator(
                PASSAGE["title"],
                PASSAGE["content"],
                self.session_id
            )
        return self._evaluator

    def _get_teacher(self) -> TeacherAgent:
        """Get or create the teacher agent."""
        if self._teacher is None:
            if not self.state.plan:
                raise ValueError("Cannot create teacher without evaluation plan")

            # Get questions already asked in evaluator to avoid repetition
            already_asked = []
            if self._evaluator:
                already_asked = self._evaluator.questions

            self._teacher = TeacherAgent(
                PASSAGE["title"],
                PASSAGE["content"],
                self.session_id,
                self.state.plan.model_dump(),
                already_asked_questions=already_asked
            )
        return self._teacher

    def _generate_quiz(self) -> Quiz:
        """Generate quiz based on session context."""
        question_pools = load_questions()

        generator = QuizGenerator(
            session_id=self.session_id,
            evaluator_conversation=self.get_conversation(Phase.EVALUATOR),
            teacher_conversation=self.get_conversation(Phase.TEACHER),
            plan=self.state.plan.model_dump(),
            question_pools=question_pools,
            passage_content=PASSAGE["content"]
        )

        self._quiz = generator.generate(num_questions=5)
        self._quiz_current_index = 0

        logger.info(f"Generated quiz with {self._quiz.total_questions} questions")

        return self._quiz

    # ============================================================
    # Main Interface
    # ============================================================

    def get_intro(self) -> dict:
        """
        Get the intro message for the current phase.

        Returns:
            dict with response, phase, plan
        """
        phase = self.state.phase

        if phase == Phase.EVALUATOR:
            intro = self._get_evaluator().get_intro_message()
            self.state.add_message(Phase.EVALUATOR, "assistant", intro)

        elif phase == Phase.TEACHER:
            intro = self._get_teacher().get_intro_message()
            self.state.add_message(Phase.TEACHER, "assistant", intro)

        elif phase == Phase.QUIZ:
            # Generate quiz if not already generated
            if not self._quiz:
                self._generate_quiz()
            intro = self._build_quiz_intro()
            self.state.add_message(Phase.QUIZ, "assistant", intro)

        elif phase == Phase.REVIEW:
            intro = "Great work! Let's review how you did today."
            self.state.add_message(Phase.REVIEW, "assistant", intro)

        else:
            intro = "Session complete."

        return {
            "response": intro,
            "phase": self.phase,
            "plan": self.plan
        }

    def process_message(self, user_message: str) -> dict:
        """
        Process a user message in the current phase.

        Handles phase transitions automatically when a phase completes.

        Returns:
            dict with:
            - response: Assistant's response
            - phase: Current phase
            - plan: Evaluation plan (if available)
            - transitioned: True if we just changed phases
            - session_complete: True if all phases done
        """
        phase = self.state.phase

        if phase == Phase.EVALUATOR:
            return self._process_evaluator(user_message)
        elif phase == Phase.TEACHER:
            return self._process_teacher(user_message)
        elif phase == Phase.QUIZ:
            return self._process_quiz(user_message)
        elif phase == Phase.REVIEW:
            return self._process_review(user_message)
        else:
            return {
                "response": "Session complete.",
                "phase": self.phase,
                "plan": self.plan,
                "transitioned": False,
                "session_complete": True
            }

    # ============================================================
    # Phase Handlers
    # ============================================================

    def _process_evaluator(self, user_message: str) -> dict:
        """Handle evaluator phase messages."""

        self.state.add_message(Phase.EVALUATOR, "user", user_message)
        result = self._get_evaluator().process_message(user_message)

        if result["is_complete"]:
            # Parse and store plan
            plan_data = yaml.safe_load(result["plan_yaml"])
            self.state.set_plan(
                student_level=plan_data["student_level"],
                teaching_focus=plan_data["teaching_focus"]
            )
            self.state.add_message(Phase.EVALUATOR, "assistant", result["response"])

            # Transition to teacher
            self.state.transition_to(Phase.TEACHER)
            teacher_intro = self._get_teacher().get_intro_message()
            self.state.add_message(Phase.TEACHER, "assistant", teacher_intro)

            logger.info(f"Session {self.session_id[:8]}... → TEACHER (level: {plan_data['student_level']})")

            return {
                "response": result["response"] + "\n\n" + teacher_intro,
                "phase": "teacher",
                "plan": self.plan,
                "transitioned": True,
                "session_complete": False
            }

        self.state.add_message(Phase.EVALUATOR, "assistant", result["response"])

        return {
            "response": result["response"],
            "phase": "evaluator",
            "plan": None,
            "transitioned": False,
            "session_complete": False
        }

    def _process_teacher(self, user_message: str) -> dict:
        """Handle teacher phase messages."""

        self.state.add_message(Phase.TEACHER, "user", user_message)
        result = self._get_teacher().process_message(user_message)

        # Update stats
        self.state.teacher_questions_asked = result.get("questions_asked", 0)
        self.state.current_difficulty = result.get("current_difficulty", "medium")

        self.state.add_message(Phase.TEACHER, "assistant", result["response"])

        # Check if ready to transition to quiz after N questions
        if self.state.teacher_questions_asked >= self.TEACHER_QUESTIONS_BEFORE_QUIZ:
            # Generate quiz
            quiz = self._generate_quiz()

            # Transition to quiz phase
            self.state.transition_to(Phase.QUIZ)

            logger.info(f"Session {self.session_id[:8]}... → QUIZ (after {self.state.teacher_questions_asked} questions)")

            # Return quiz data for frontend overlay (don't include answers)
            quiz_questions = [
                {
                    "id": q.id,
                    "question": q.question,
                    "difficulty": q.difficulty
                }
                for q in quiz.questions
            ]

            return {
                "response": result["response"] + "\n\nGreat practice! Let's see what you've learned with a quick quiz.",
                "phase": "quiz",
                "plan": self.plan,
                "transitioned": True,
                "session_complete": False,
                "show_quiz": True,
                "quiz_data": {
                    "total_questions": quiz.total_questions,
                    "time_limit_seconds": quiz.time_limit_seconds,
                    "questions": quiz_questions
                }
            }

        return {
            "response": result["response"],
            "phase": "teacher",
            "plan": self.plan,
            "transitioned": False,
            "session_complete": False,
            "teacher_questions": self.state.teacher_questions_asked,
            "questions_until_quiz": self.TEACHER_QUESTIONS_BEFORE_QUIZ - self.state.teacher_questions_asked
        }

    def _build_quiz_intro(self) -> str:
        """Build the intro message for the quiz phase."""
        if not self._quiz:
            return "Time for a quiz!"

        return f"""Great practice session! Now let's see what you've learned.

I have {self._quiz.total_questions} questions for you. Take your time - you have {self._quiz.time_limit_seconds // 60} minutes.

Here's your first question:

**Question 1:** {self._quiz.questions[0].question}"""

    def _process_quiz(self, user_message: str) -> dict:
        """Handle quiz phase messages (for chat-based interactions during quiz)."""
        # Quiz is handled via submit_quiz(), not chat
        return {
            "response": "Please complete the quiz using the quiz interface.",
            "phase": "quiz",
            "plan": self.plan,
            "transitioned": False,
            "session_complete": False,
            "show_quiz": True
        }

    def submit_quiz(self, answers: list[dict]) -> dict:
        """
        Submit quiz answers and get results with LLM review.

        Args:
            answers: List of {"question_id": int, "answer": str}

        Returns:
            dict with quiz results, LLM review, and transition to review phase
        """
        if not self._quiz:
            return {"error": "No quiz available"}

        logger.info(f"Processing quiz submission for session {self.session_id[:8]}...")

        # Build Q&A pairs for review
        qa_pairs = []
        for ans in answers:
            q_id = ans["question_id"]
            user_answer = ans["answer"]

            question = next((q for q in self._quiz.questions if q.id == q_id), None)
            if not question:
                continue

            qa_pairs.append({
                "question_id": q_id,
                "question": question.question,
                "difficulty": question.difficulty,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation
            })

        # Get comprehensive LLM review
        review = self._generate_quiz_review(qa_pairs)

        # Calculate score
        correct_count = review["score"]
        total = len(qa_pairs)
        percentage = (correct_count / total * 100) if total > 0 else 0

        # Store quiz result
        self.state.set_quiz_result(total, correct_count, 0)

        # Transition to review
        self.state.transition_to(Phase.REVIEW)

        logger.info(f"Session {self.session_id[:8]}... → REVIEW (score: {correct_count}/{total})")

        # Persist session after quiz completion (checkpoint)
        self._persist_session()

        return {
            "success": True,
            "phase": "review",
            "quiz_result": {
                "score": correct_count,
                "total": total,
                "percentage": percentage,
                "summary": review["summary"],
                "question_reviews": review["question_reviews"]
            }
        }

    def _generate_quiz_review(self, qa_pairs: list[dict]) -> dict:
        """Generate comprehensive LLM review of quiz answers."""
        from openai import OpenAI
        import json
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Build the review prompt
        qa_text = ""
        for i, qa in enumerate(qa_pairs, 1):
            qa_text += f"""
Question {i} ({qa['difficulty']}): {qa['question']}
Expected Answer: {qa['correct_answer']}
Student's Answer: {qa['user_answer']}
---"""

        prompt = f"""Review this student's quiz answers about the following passage.

PASSAGE:
{PASSAGE['content']}

QUIZ ANSWERS:
{qa_text}

For each question:
1. Determine if the student's answer is correct (they don't need exact wording, just the right concept)
2. Provide encouraging, constructive feedback

Return JSON:
{{
    "score": <number of correct answers out of {len(qa_pairs)}>,
    "summary": "<2-3 sentence overall summary of performance, encouraging tone>",
    "question_reviews": [
        {{
            "question_id": <id>,
            "is_correct": true/false,
            "feedback": "<1-2 sentence feedback for this specific answer>"
        }}
    ]
}}"""

        logger.info("Generating comprehensive quiz review...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a supportive reading tutor reviewing a student's quiz. Be encouraging but accurate. Celebrate what they got right and gently guide them on incorrect answers."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Merge the review back with question details
        for review in result["question_reviews"]:
            qa = next((q for q in qa_pairs if q["question_id"] == review["question_id"]), None)
            if qa:
                review["question"] = qa["question"]
                review["user_answer"] = qa["user_answer"]
                review["correct_answer"] = qa["correct_answer"]
                review["difficulty"] = qa["difficulty"]

        logger.info(f"Quiz review complete: {result['score']}/{len(qa_pairs)}")

        return result

    def _evaluate_quiz_answer(self, question, user_answer: str) -> dict:
        """Evaluate a quiz answer using LLM."""
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""Evaluate this quiz answer.

Question: {question.question}
Expected Answer: {question.correct_answer}
Student's Answer: {user_answer}

Determine if the student's answer is correct (they don't need exact wording, just the right concept).

Return JSON:
{{
    "is_correct": true/false,
    "feedback": "Brief encouraging feedback (1-2 sentences). If wrong, gently explain the correct answer."
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a supportive teacher evaluating quiz answers. Be encouraging but accurate."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        import json
        return json.loads(response.choices[0].message.content)

    def _build_review_intro(self) -> str:
        """Build the intro message for the review phase."""
        quiz_result = self.state.quiz_result

        if quiz_result:
            score_msg = f"You scored {quiz_result.correct_answers}/{quiz_result.total_questions} ({quiz_result.score_percentage:.0f}%) on the quiz."
        else:
            score_msg = ""

        return f"""**Session Review**

{score_msg}

Here's a summary of your learning session:
- Student Level: {self.state.plan.student_level if self.state.plan else 'N/A'}
- Practice Questions: {self.state.teacher_questions_asked}

What would you like to know about your performance?"""

    def _process_review(self, user_message: str) -> dict:
        """Handle review phase messages."""

        self.state.add_message(Phase.REVIEW, "user", user_message)

        # TODO: Implement ReviewAgent
        response = "Thanks for practicing today! Your session is complete."

        self.state.add_message(Phase.REVIEW, "assistant", response)

        # Persist completed session to MongoDB (if configured)
        self._persist_session()

        return {
            "response": response,
            "phase": "review",
            "plan": self.plan,
            "transitioned": False,
            "session_complete": True
        }

    def _persist_session(self) -> None:
        """
        Persist the session state to MongoDB.

        This is a no-op if MongoDB is not configured.
        """
        try:
            persistence = get_persistence()
            session_data = self.state.to_dict()
            persistence.save_session(session_data)
        except Exception as e:
            # Never let persistence failures break the session
            logger.warning(f"Session persistence failed (non-fatal): {e}")

    # ============================================================
    # Manual Phase Control
    # ============================================================

    def skip_to_phase(self, target_phase: Phase) -> dict:
        """
        Manually skip to a specific phase.

        Useful for testing or allowing users to skip ahead.
        """
        current_idx = self.PHASE_ORDER.index(self.state.phase)
        target_idx = self.PHASE_ORDER.index(target_phase)

        if target_idx <= current_idx:
            return {
                "success": False,
                "error": f"Cannot go back to {target_phase.value}"
            }

        self.state.transition_to(target_phase)
        intro = self.get_intro()

        logger.info(f"Session {self.session_id[:8]}... skipped to {target_phase.value}")

        return {
            "success": True,
            "response": intro["response"],
            "phase": target_phase.value
        }

    # ============================================================
    # State Access
    # ============================================================

    def get_state(self) -> dict:
        """Get the complete session state."""
        return self.state.to_dict()

    def get_conversation(self, phase: Phase) -> list[dict]:
        """Get conversation history for a specific phase."""
        if phase == Phase.EVALUATOR:
            messages = self.state.evaluator_conversation
        elif phase == Phase.TEACHER:
            messages = self.state.teacher_conversation
        elif phase == Phase.QUIZ:
            messages = self.state.quiz_conversation
        elif phase == Phase.REVIEW:
            messages = self.state.review_conversation
        else:
            messages = []

        return [{"role": m.role, "content": m.content} for m in messages]


# ============================================================
# Global Orchestrator Registry
# ============================================================

_orchestrators: dict[str, SessionOrchestrator] = {}


def get_orchestrator(session_id: str) -> SessionOrchestrator:
    """Get or create an orchestrator for a session."""
    if session_id not in _orchestrators:
        _orchestrators[session_id] = SessionOrchestrator(session_id)
    return _orchestrators[session_id]


def create_orchestrator(session_id: str) -> SessionOrchestrator:
    """Create a new orchestrator (replaces existing if any)."""
    _orchestrators[session_id] = SessionOrchestrator(session_id)
    return _orchestrators[session_id]
