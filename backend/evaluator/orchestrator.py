"""
Evaluator Orchestrator - Deterministic Flow

6 fixed questions:
1. "What is this passage about?"
2. "What did you like most or find interesting?"
3. "Is this fiction or non-fiction?"
4. 1 EASY question from pool
5. 1 MEDIUM question from pool
6. 1 HARD question from pool

After all 6, send entire conversation to evaluation agent for scoring.
"""

from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
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
    student_level: str
    overall_score: int
    main_idea_score: int
    engagement_score: int
    text_type_score: int
    easy_score: int
    medium_score: int
    hard_score: int
    strengths: list[str]
    weaknesses: list[str]
    recommended_difficulty: str
    focus_areas: list[str]
    interests: str
    teaching_approach: str


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
        logger.info(f"   Questions: 6 total (3 fixed + 1 easy + 1 medium + 1 hard)")
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
            logger.info("🤖 Sending to evaluation agent...")
            logger.info("=" * 60)
            
            self.is_complete = True
            self.plan_yaml = self._evaluate_all()
            
            return {
                "response": "Thank you for answering all my questions! Let me analyze your responses and create a personalized learning plan for you...",
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
        """Send all Q&A to LLM for evaluation."""
        
        # Build the conversation summary
        qa_pairs = ""
        q_labels = ["Main Idea", "Interest/Engagement", "Fiction vs Non-fiction", 
                    "Easy Comprehension", "Medium Comprehension", "Hard Comprehension"]
        
        for i, (q, a) in enumerate(zip(self.questions, self.answers)):
            qa_pairs += f"\n{q_labels[i]}:\nQ: {q}\nA: {a}\n"
        
        prompt = f"""You are evaluating a student's reading comprehension based on their answers.

PASSAGE:
Title: {self.passage_title}
{self.passage_content}

STUDENT'S ANSWERS:
{qa_pairs}

EXPECTED ANSWERS FOR COMPREHENSION QUESTIONS:
- Easy: {self.easy_q['answer']}
- Medium: {self.medium_q['answer']}
- Hard: {self.hard_q['answer']}

Evaluate each answer and provide scores. Return JSON:
{{
    "main_idea_score": <0-100 based on understanding of passage topic>,
    "engagement_score": <0-100 based on interest shown>,
    "text_type_score": <0-100 - should identify as non-fiction>,
    "easy_score": <0-100 based on correctness>,
    "medium_score": <0-100 based on correctness>,
    "hard_score": <0-100 based on depth of analysis>,
    "overall_score": <weighted average>,
    "student_level": "<beginner/intermediate/advanced>",
    "strengths": ["<areas they did well>"],
    "weaknesses": ["<areas to improve>"],
    "interests": "<what they found interesting based on Q2>",
    "recommended_difficulty": "<easy/medium/hard>",
    "focus_areas": ["<topics to focus on>"],
    "teaching_approach": "<how to teach them>"
}}"""

        logger.info("📤 Calling evaluation LLM...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert reading assessment evaluator. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        eval_data = json.loads(response.choices[0].message.content)
        
        # Log scores
        logger.info("")
        logger.info("📊 EVALUATION RESULTS:")
        logger.info(f"   Main Idea:    {eval_data.get('main_idea_score', 0)}")
        logger.info(f"   Engagement:   {eval_data.get('engagement_score', 0)}")
        logger.info(f"   Text Type:    {eval_data.get('text_type_score', 0)}")
        logger.info(f"   Easy Q:       {eval_data.get('easy_score', 0)}")
        logger.info(f"   Medium Q:     {eval_data.get('medium_score', 0)}")
        logger.info(f"   Hard Q:       {eval_data.get('hard_score', 0)}")
        logger.info(f"   ─────────────────────")
        logger.info(f"   OVERALL:      {eval_data.get('overall_score', 0)}")
        logger.info(f"   Level:        {eval_data.get('student_level', 'unknown')}")
        logger.info(f"   Recommended:  {eval_data.get('recommended_difficulty', 'medium')}")
        
        # Create plan
        plan = StudentPlan(
            student_level=eval_data.get("student_level", "intermediate"),
            overall_score=int(eval_data.get("overall_score", 50)),
            main_idea_score=eval_data.get("main_idea_score", 50),
            engagement_score=eval_data.get("engagement_score", 50),
            text_type_score=eval_data.get("text_type_score", 50),
            easy_score=eval_data.get("easy_score", 50),
            medium_score=eval_data.get("medium_score", 50),
            hard_score=eval_data.get("hard_score", 50),
            strengths=eval_data.get("strengths", []),
            weaknesses=eval_data.get("weaknesses", []),
            recommended_difficulty=eval_data.get("recommended_difficulty", "medium"),
            focus_areas=eval_data.get("focus_areas", []),
            interests=eval_data.get("interests", ""),
            teaching_approach=eval_data.get("teaching_approach", "balanced")
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
    
    test_answers = [
        "It's about honeybees and how they live in hives with different roles.",
        "I found the waggle dance really interesting - how they communicate through dancing!",
        "Non-fictional because it has specific facts and numbers about bees.",
        "The queen bee lays the eggs.",
        "Because there's not enough food in winter to feed everyone.",
        "The author wants to show how organized and efficient bees are, like a well-run city."
    ]
    
    for answer in test_answers:
        print(f"Student: {answer}")
        result = orch.process_message(answer)
        print(f"Tutor: {result['response']}\n")
        
        if result['is_complete']:
            print("\n" + "=" * 60)
            print("PLAN:")
            print("=" * 60)
            print(result['plan_yaml'])
            break
