"""
Quiz Generator

Generates personalized quizzes based on:
- Evaluator conversation (initial assessment)
- Teacher conversation (practice session)
- Evaluation plan (student level)
- Available question pools

Returns structured JSON quiz with questions and answers.
"""

from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal, Optional
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("quiz.generator")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================
# Quiz Data Models
# ============================================================

class QuizQuestion(BaseModel):
    """A single quiz question."""
    id: int
    question: str
    difficulty: Literal["easy", "medium", "hard"]
    correct_answer: str
    explanation: str
    topic: str  # e.g., "main_idea", "vocabulary", "inference"
    source: Literal["pool", "generated"]  # whether from pool or newly generated


class Quiz(BaseModel):
    """Complete quiz structure."""
    session_id: str
    student_level: str
    total_questions: int
    questions: list[QuizQuestion]
    time_limit_seconds: int = Field(default=300)  # 5 minutes default

    def to_json(self) -> str:
        """Export quiz as JSON string."""
        return self.model_dump_json(indent=2)


# ============================================================
# Quiz Generator
# ============================================================

class QuizGenerator:
    """
    Generates personalized quizzes based on session context.

    Uses LLM to:
    1. Analyze what topics were covered in conversations
    2. Identify areas where student struggled
    3. Select/generate appropriate questions
    4. Balance difficulty based on student level
    """

    def __init__(
        self,
        session_id: str,
        evaluator_conversation: list[dict],
        teacher_conversation: list[dict],
        plan: dict,
        question_pools: dict,
        passage_content: str
    ):
        self.session_id = session_id
        self.evaluator_conversation = evaluator_conversation
        self.teacher_conversation = teacher_conversation
        self.plan = plan
        self.question_pools = question_pools
        self.passage_content = passage_content

        self.student_level = plan.get("student_level", "medium")

    def generate(self, num_questions: int = 5) -> Quiz:
        """
        Generate a personalized quiz.

        Args:
            num_questions: Number of questions to include (default 5)

        Returns:
            Quiz object with questions and answers
        """
        logger.info(f"Generating quiz for session {self.session_id[:8]}...")

        # Build context for LLM
        context = self._build_context()

        # Generate quiz via LLM
        quiz_data = self._call_llm(context, num_questions)

        # Build Quiz object
        questions = [
            QuizQuestion(
                id=i + 1,
                question=q["question"],
                difficulty=q["difficulty"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                topic=q["topic"],
                source=q.get("source", "generated")
            )
            for i, q in enumerate(quiz_data["questions"])
        ]

        quiz = Quiz(
            session_id=self.session_id,
            student_level=self.student_level,
            total_questions=len(questions),
            questions=questions,
            time_limit_seconds=quiz_data.get("time_limit_seconds", 300)
        )

        logger.info(f"Generated {len(questions)} questions for {self.student_level} level student")

        return quiz

    def _build_context(self) -> str:
        """Build context string for the LLM."""

        # Format conversations
        eval_conv = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.evaluator_conversation
        ])

        teacher_conv = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.teacher_conversation
        ])

        # Format available questions
        pool_summary = {
            "easy": [q["question"] for q in self.question_pools.get("easy", [])],
            "medium": [q["question"] for q in self.question_pools.get("medium", [])],
            "hard": [q["question"] for q in self.question_pools.get("hard", [])]
        }

        return f"""PASSAGE:
{self.passage_content}

STUDENT LEVEL: {self.student_level}
TEACHING FOCUS: {self.plan.get('teaching_focus', 'General comprehension')}

EVALUATOR CONVERSATION:
{eval_conv}

TEACHER CONVERSATION:
{teacher_conv}

AVAILABLE QUESTION POOL:
Easy: {json.dumps(pool_summary['easy'])}
Medium: {json.dumps(pool_summary['medium'])}
Hard: {json.dumps(pool_summary['hard'])}
"""

    def _call_llm(self, context: str, num_questions: int) -> dict:
        """Call LLM to generate quiz questions."""

        # Determine difficulty distribution based on level
        if self.student_level == "low":
            distribution = "3 easy, 2 medium, 0 hard"
        elif self.student_level == "high":
            distribution = "1 easy, 2 medium, 2 hard"
        else:  # medium
            distribution = "1 easy, 3 medium, 1 hard"

        prompt = f"""Based on the learning session context below, generate a {num_questions}-question quiz.

{context}

QUIZ REQUIREMENTS:
1. Generate exactly {num_questions} questions
2. Difficulty distribution: {distribution}
3. Focus on areas where the student showed weakness or uncertainty
4. Include questions that test comprehension at different levels:
   - Recall (easy): Direct facts from the passage
   - Understanding (medium): Connections and reasoning
   - Analysis (hard): Inference and critical thinking
5. You may use questions from the available pool OR generate new ones
6. Each question should have a clear correct answer

Return JSON in this exact format:
{{
    "analysis": "Brief analysis of what the student needs to practice",
    "time_limit_seconds": 300,
    "questions": [
        {{
            "question": "The question text",
            "difficulty": "easy|medium|hard",
            "correct_answer": "The expected answer",
            "explanation": "Why this is correct (for feedback after quiz)",
            "topic": "main_idea|details|vocabulary|inference|structure|author_purpose",
            "source": "pool|generated"
        }}
    ]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert reading assessment designer. Create fair, clear quiz questions that test comprehension at the appropriate level."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        logger.info(f"LLM Analysis: {result.get('analysis', 'N/A')}")

        return result


# ============================================================
# Standalone Test
# ============================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from shared.passage import PASSAGE
    from evaluator.question_generator import load_questions

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s │ %(levelname)s │ %(message)s',
        datefmt='%H:%M:%S'
    )

    # Mock session data
    mock_evaluator_conv = [
        {"role": "assistant", "content": "What is this passage about?"},
        {"role": "user", "content": "It's about bees."},
        {"role": "assistant", "content": "What did you find interesting?"},
        {"role": "user", "content": "The waggle dance."},
        {"role": "assistant", "content": "Is this fiction or non-fiction?"},
        {"role": "user", "content": "Non-fiction."},
        {"role": "assistant", "content": "What is the queen's role?"},
        {"role": "user", "content": "She lays eggs."},
        {"role": "assistant", "content": "Why are drones pushed out?"},
        {"role": "user", "content": "I'm not sure, maybe food?"},
        {"role": "assistant", "content": "What does the author want us to understand?"},
        {"role": "user", "content": "That bees are organized."},
    ]

    mock_teacher_conv = [
        {"role": "assistant", "content": "Let's practice! Can you tell me more about the waggle dance?"},
        {"role": "user", "content": "It's how bees communicate about food."},
        {"role": "assistant", "content": "Good! What information does the dance convey?"},
        {"role": "user", "content": "Direction and distance to food."},
        {"role": "assistant", "content": "Excellent! The angle shows direction relative to the sun."},
    ]

    mock_plan = {
        "student_level": "medium",
        "teaching_focus": "Strengthen fundamentals and encourage more detailed responses."
    }

    # Load question pools
    question_pools = load_questions()

    # Generate quiz
    generator = QuizGenerator(
        session_id="test-quiz",
        evaluator_conversation=mock_evaluator_conv,
        teacher_conversation=mock_teacher_conv,
        plan=mock_plan,
        question_pools=question_pools,
        passage_content=PASSAGE["content"]
    )

    quiz = generator.generate(num_questions=5)

    print("\n" + "=" * 60)
    print("GENERATED QUIZ")
    print("=" * 60)
    print(quiz.to_json())
