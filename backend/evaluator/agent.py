"""
Evaluator Agent

Asks 4 questions to assess the student:
1. "What is this passage about?" - comprehension overview
2. "Is it fiction or non-fiction?" - text type recognition
3. "What do you like most or find interesting?" - engagement/interest
4. One MEDIUM question from cached pool - comprehension check

After 4 questions, creates a profile for the Teacher agent.
"""

from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Question(BaseModel):
    question: str
    answer: str
    explanation: str


class QuestionPool(BaseModel):
    easy: list[Question]
    medium: list[Question]
    hard: list[Question]


class StudentProfile(BaseModel):
    comprehension_score: int
    text_recognition_score: int
    engagement_score: int
    overall_level: str
    interests: list[str]
    recommended_difficulty: str


# Fixed evaluation questions (1-3)
EVAL_QUESTIONS = [
    "What is this passage about?",
    "Is this a fiction or non-fiction piece? How can you tell?",
    "What do you like most or find interesting in this text?",
]


def load_cached_questions() -> QuestionPool:
    """Load questions from cache file."""
    cache_path = os.path.join(os.path.dirname(__file__), "questions_cache.json")
    with open(cache_path, "r") as f:
        data = json.load(f)
    return QuestionPool(
        easy=[Question(**q) for q in data["easy"]],
        medium=[Question(**q) for q in data["medium"]],
        hard=[Question(**q) for q in data["hard"]]
    )


def evaluate_response(
    question: str,
    student_answer: str,
    passage_content: str,
    expected_answer: Optional[str] = None
) -> dict:
    """Evaluate a student's response and provide feedback."""
    
    prompt = f"""Evaluate this reading comprehension answer.

Passage: {passage_content}

Question: {question}
Student's Answer: {student_answer}
{"Expected Answer: " + expected_answer if expected_answer else ""}

Return JSON:
{{
    "score": <0-100>,
    "feedback": "<brief encouraging feedback, 1-2 sentences>"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only valid JSON. Be encouraging."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


class EvaluatorAgent:
    """Handles the 4-question evaluation flow."""
    
    def __init__(self, passage_title: str, passage_content: str):
        self.passage_title = passage_title
        self.passage_content = passage_content
        self.question_pools = load_cached_questions()
        self.current_question = 0
        self.answers: list[str] = []
        self.evaluations: list[dict] = []
        
    def get_current_question(self) -> Optional[str]:
        """Get the current question to ask."""
        if self.current_question < 3:
            return EVAL_QUESTIONS[self.current_question]
        elif self.current_question == 3:
            return self.question_pools.medium[0].question
        return None
    
    def get_expected_answer(self) -> Optional[str]:
        """Get expected answer for Q4."""
        if self.current_question == 3:
            return self.question_pools.medium[0].answer
        return None
        
    def submit_answer(self, answer: str) -> dict:
        """Submit answer and get evaluation."""
        question = self.get_current_question()
        expected = self.get_expected_answer()
        
        evaluation = evaluate_response(
            question,
            answer,
            self.passage_content,
            expected
        )
        
        self.answers.append(answer)
        self.evaluations.append(evaluation)
        self.current_question += 1
        
        return evaluation
    
    def is_complete(self) -> bool:
        return self.current_question >= 4
    
    def get_student_profile(self) -> StudentProfile:
        """Generate student profile after evaluation."""
        if not self.is_complete():
            raise ValueError("Evaluation not complete")
        
        scores = [e.get("score", 50) for e in self.evaluations]
        avg = sum(scores) / len(scores)
        
        if avg >= 80:
            level, difficulty = "advanced", "hard"
        elif avg >= 50:
            level, difficulty = "intermediate", "medium"
        else:
            level, difficulty = "beginner", "easy"
        
        return StudentProfile(
            comprehension_score=scores[0],
            text_recognition_score=scores[1],
            engagement_score=scores[2],
            overall_level=level,
            interests=[self.answers[2][:100]],
            recommended_difficulty=difficulty
        )
    
    def get_question_pools(self) -> QuestionPool:
        """Return pools for Teacher."""
        return self.question_pools


if __name__ == "__main__":
    from shared.passage import PASSAGE
    
    print("Testing Evaluator Agent...\n")
    agent = EvaluatorAgent(PASSAGE["title"], PASSAGE["content"])
    
    test_answers = [
        "It's about how bees live and work together in hives.",
        "Non-fiction, because it has specific facts and numbers about bees.",
        "The waggle dance is fascinating - bees communicate through dancing!",
        "Drones get pushed out because food is scarce and they don't contribute."
    ]
    
    for i, answer in enumerate(test_answers):
        q = agent.get_current_question()
        print(f"Q{i+1}: {q}")
        print(f"A: {answer}")
        result = agent.submit_answer(answer)
        print(f"Score: {result['score']} - {result['feedback']}\n")
    
    profile = agent.get_student_profile()
    print(f"=== Profile ===")
    print(f"Level: {profile.overall_level}")
    print(f"Recommended: {profile.recommended_difficulty}")
