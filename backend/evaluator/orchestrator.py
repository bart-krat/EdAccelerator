"""
Evaluator Orchestrator - Deterministic Flow

6 fixed questions:
1. "What is this passage about?"
2. "What did you like most or find interesting?"
3. "Is this fiction or non-fiction?"
4. 1 EASY question from pool
5. 1 MEDIUM question from pool
6. 1 HARD question from pool

After all 6, evaluate and output simple plan:
- Student Level: Low / Medium / High
- Teaching Focus: based on level
"""

from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, Literal
import json
import yaml
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("evaluator")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_cached_questions() -> dict:
    cache_path = os.path.join(os.path.dirname(__file__), "questions_cache.json")
    with open(cache_path, "r") as f:
        return json.load(f)


class StudentPlan(BaseModel):
    student_level: Literal["low", "medium", "high"]
    teaching_focus: str


TEACHING_FOCUS = {
    "low": "Improve interest and engagement with the text. Use simpler questions and encourage longer responses.",
    "medium": "Strengthen fundamentals and encourage more detailed responses. Build confidence with medium-difficulty questions.",
    "high": "Polish comprehension with more challenging questions. Explore deeper analysis and critical thinking."
}


class EvaluatorOrchestrator:
    """Deterministic 6-question evaluation flow."""

    def __init__(self, passage_title: str, passage_content: str, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.passage_title = passage_title
        self.passage_content = passage_content

        # Load question pools
        pools = load_cached_questions()
        self.easy_q = pools["easy"][0]
        self.medium_q = pools["medium"][0]
        self.hard_q = pools["hard"][0]

        # Fixed questions
        self.questions = [
            "I'm going to ask you a few questions so I can tailor your learning. Can you first tell me what this passage is about?",
            "What did you like most about this passage or find most interesting?",
            "Would you say this piece is fictional or non-fictional? What makes you think that?",
            self.easy_q["question"],
            self.medium_q["question"],
            self.hard_q["question"],
        ]

        self.current_question = 0
        self.answers: list[str] = []
        self.is_complete = False
        self.plan_yaml: Optional[str] = None

        logger.info("=" * 60)
        logger.info("🚀 NEW EVALUATION SESSION")
        logger.info(f"   Session: {self.session_id}")
        logger.info(f"   Questions: 6 total")
        logger.info("=" * 60)

    def get_intro_message(self) -> str:
        """Return the first question."""
        logger.info(f"📝 Q1: {self.questions[0][:60]}...")
        return self.questions[0]

    def process_message(self, user_message: str) -> dict:
        """Process user's answer, return next question or evaluate."""

        # Store the answer
        self.answers.append(user_message)
        q_num = self.current_question + 1

        logger.info("")
        logger.info(f"{'─' * 60}")
        logger.info(f"📥 ANSWER {q_num}/6")
        logger.info(f"{'─' * 60}")
        logger.info(f"   Q: {self.questions[self.current_question][:50]}...")
        logger.info(f"   A: {user_message[:80]}{'...' if len(user_message) > 80 else ''}")

        self.current_question += 1

        # Check if we have all 6 answers
        if self.current_question >= 6:
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ ALL 6 QUESTIONS ANSWERED")
            logger.info("🤖 Evaluating...")
            logger.info("=" * 60)

            self.is_complete = True
            self.plan_yaml = self._evaluate_all()

            return {
                "response": "Thank you for answering all my questions! Let me create your personalized learning plan...",
                "is_complete": True,
                "plan_yaml": self.plan_yaml,
                "show_next_question": False
            }

        # Return next question
        next_q = self.questions[self.current_question]
        logger.info(f"📝 Q{self.current_question + 1}: {next_q[:60]}...")

        return {
            "response": next_q,
            "is_complete": False,
            "plan_yaml": None,
            "show_next_question": True
        }

    def _evaluate_all(self) -> str:
        """Send all Q&A to LLM for simple evaluation."""

        # Build the conversation summary
        qa_pairs = ""
        q_labels = ["Main Idea", "Interest/Engagement", "Fiction vs Non-fiction",
                    "Easy Question", "Medium Question", "Hard Question"]

        for i, (q, a) in enumerate(zip(self.questions, self.answers)):
            qa_pairs += f"\n{q_labels[i]}:\nQ: {q}\nA: {a}\n"

        prompt = f"""Evaluate this student's reading comprehension responses.

PASSAGE:
{self.passage_content}

STUDENT'S ANSWERS:
{qa_pairs}

Categorize the student into ONE level based on these criteria:

LOW: Poor engagement, very short answers (few words), doesn't understand the text well
MEDIUM: Good attempt, reasonable answers, but lacks detail or depth
HIGH: Detailed responses, good understanding, thoughtful answers

Look at:
1. Answer length and effort
2. Understanding of the passage
3. Engagement and interest shown

Return JSON:
{{
    "level": "low" or "medium" or "high",
    "reason": "brief explanation of why this level"
}}"""

        logger.info("📤 Calling evaluation LLM...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are evaluating student reading comprehension. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        eval_data = json.loads(response.choices[0].message.content)
        level = eval_data.get("level", "medium").lower()

        # Validate level
        if level not in ["low", "medium", "high"]:
            level = "medium"

        logger.info("")
        logger.info("📊 EVALUATION RESULT:")
        logger.info(f"   Level: {level.upper()}")
        logger.info(f"   Reason: {eval_data.get('reason', 'N/A')}")

        # Create simple plan
        plan = StudentPlan(
            student_level=level,
            teaching_focus=TEACHING_FOCUS[level]
        )

        plan_yaml = yaml.dump(plan.model_dump(), default_flow_style=False, sort_keys=False)

        # Save to file
        self._save_plan(plan_yaml)

        return plan_yaml

    def _save_plan(self, plan_yaml: str):
        """Save plan to file."""
        plans_dir = os.path.join(os.path.dirname(__file__), "..", "plans")
        os.makedirs(plans_dir, exist_ok=True)

        filepath = os.path.join(plans_dir, f"plan_{self.session_id}.yaml")

        with open(filepath, "w") as f:
            f.write(f"# Evaluation Plan - {self.session_id}\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            f.write(plan_yaml)

        logger.info(f"💾 Plan saved: {filepath}")

    def get_progress(self) -> dict:
        """Get current progress."""
        return {
            "current_question": self.current_question,
            "total_questions": 6,
            "answers_collected": len(self.answers),
            "is_complete": self.is_complete
        }


if __name__ == "__main__":
    from shared.passage import PASSAGE

    print("\n")
    orch = EvaluatorOrchestrator(PASSAGE["title"], PASSAGE["content"], "test123")

    print(f"Tutor: {orch.get_intro_message()}\n")

    # Test with LOW engagement answers
    test_answers_low = ["bees", "idk", "non fiction", "queen", "no food", "organized"]

    # Test with HIGH engagement answers
    test_answers_high = [
        "This passage is about the fascinating social structure of honeybees and how they organize their hive with different roles for queens, workers, and drones.",
        "I found the waggle dance absolutely fascinating - the idea that bees can communicate precise locations through dance movements is incredible!",
        "This is clearly non-fiction because it presents factual information with specific numbers and scientific observations about bee behavior.",
        "The queen bee's primary role is to lay eggs - up to 2,000 per day - to keep the colony growing and thriving.",
        "Drones are pushed out in autumn because food becomes scarce and since they don't contribute to food gathering or hive protection, the workers prioritize the colony's survival.",
        "The author compares the hive to a city to emphasize the remarkable level of organization - every bee has a specific job that changes with age, similar to how human societies organize labor."
    ]

    for answer in test_answers_high:
        print(f"Student: {answer}")
        result = orch.process_message(answer)
        print(f"Tutor: {result['response']}\n")

        if result['is_complete']:
            print("\n" + "=" * 60)
            print("PLAN:")
            print("=" * 60)
            print(result['plan_yaml'])
            break
