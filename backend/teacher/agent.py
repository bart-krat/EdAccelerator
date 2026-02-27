"""
Teacher Agent

Takes the evaluation plan and conducts an interactive teaching session.
- Generates questions based on student level
- Provides constructive feedback
- Drives engagement and understanding
- Adapts to student responses
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

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.utils import safe_json_parse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("teacher")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_question_pools() -> dict:
    """Load the cached question pools."""
    cache_path = os.path.join(os.path.dirname(__file__), "..", "evaluator", "questions_cache.json")
    with open(cache_path, "r") as f:
        return json.load(f)


def load_plan(session_id: str) -> Optional[dict]:
    """Load the evaluation plan for a session."""
    plan_path = os.path.join(os.path.dirname(__file__), "..", "plans", f"plan_{session_id}.yaml")
    if os.path.exists(plan_path):
        with open(plan_path, "r") as f:
            # Skip comment lines
            content = "\n".join(line for line in f.readlines() if not line.startswith("#"))
            return yaml.safe_load(content)
    return None


class TeacherAgent:
    """
    Interactive teaching agent that adapts to the student's level.
    """

    def __init__(self, passage_title: str, passage_content: str, session_id: str, plan: dict = None, already_asked_questions: list[str] = None):
        self.session_id = session_id
        self.passage_title = passage_title
        self.passage_content = passage_content

        # Load plan or use provided one
        self.plan = plan or load_plan(session_id) or self._default_plan()

        # Load question pools
        self.question_pools = load_question_pools()

        # Questions already asked in evaluator (to avoid repetition)
        self.already_asked = already_asked_questions or []

        # Session state
        self.conversation_history: list[dict] = []
        self.questions_asked: list[str] = []
        self.correct_answers = 0
        self.total_answers = 0

        # Derive starting difficulty from student level
        level = self.plan.get("student_level", "medium")
        self.current_difficulty = {"low": "easy", "medium": "medium", "high": "hard"}.get(level, "medium")

        logger.info("=" * 60)
        logger.info("📚 TEACHER SESSION STARTED")
        logger.info(f"   Session: {session_id}")
        logger.info(f"   Student Level: {level}")
        logger.info(f"   Starting Difficulty: {self.current_difficulty}")
        logger.info(f"   Teaching Focus: {self.plan.get('teaching_focus', 'N/A')[:50]}...")
        logger.info("=" * 60)

    def _default_plan(self) -> dict:
        """Default plan if none exists."""
        return {
            "student_level": "medium",
            "teaching_focus": "Strengthen fundamentals and encourage more detailed responses. Build confidence with medium-difficulty questions."
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the teaching LLM."""

        return f"""You are an engaging, supportive reading tutor working with a student.

PASSAGE:
Title: {self.passage_title}
{self.passage_content}

STUDENT PROFILE:
- Level: {self.plan.get('student_level', 'medium')}
- Teaching Focus: {self.plan.get('teaching_focus', 'Strengthen fundamentals and encourage more detailed responses.')}

CURRENT SESSION:
- Questions asked so far: {len(self.questions_asked)}
- Correct answers: {self.correct_answers}/{self.total_answers}
- Current difficulty: {self.current_difficulty}

YOUR TEACHING STYLE:
1. Be warm, encouraging, and patient
2. Give constructive feedback - always find something positive first
3. If they're wrong, guide them to the right answer instead of just telling them
4. Ask follow-up questions to deepen understanding
5. Connect concepts to things they might find interesting
6. Celebrate small wins to build confidence
7. If they seem stuck, offer hints rather than answers

QUESTIONS ALREADY ASKED (DO NOT repeat these):
{json.dumps(self.already_asked, indent=2)}

QUESTION POOL (use NEW questions from these or create similar ones - avoid repeating questions above):
Easy: {json.dumps([q['question'] for q in self.question_pools['easy']], indent=2)}
Medium: {json.dumps([q['question'] for q in self.question_pools['medium']], indent=2)}
Hard: {json.dumps([q['question'] for q in self.question_pools['hard']], indent=2)}

RESPONSE FORMAT:
Always respond with JSON:
{{
    "message": "<your response to the student - conversational, warm>",
    "asked_question": true/false,  // did you ask them a question?
    "question_difficulty": "easy/medium/hard/none",  // if you asked a question
    "evaluation": {{  // only if they answered a previous question
        "was_correct": true/false/partial,
        "score": 0-100,
        "feedback_type": "praise/encouragement/guidance/correction"
    }},
    "engagement_level": "low/medium/high",  // how engaged does the student seem?
    "should_adjust_difficulty": "up/down/stay"  // based on performance
}}

IMPORTANT:
- Keep responses concise but warm (2-4 sentences + question)
- Don't ask more than one question at a time
- If student asks an off-topic question, answer briefly then guide back
- Track their progress and adjust difficulty accordingly"""

    def get_intro_message(self) -> str:
        """Generate the opening message for the teaching session."""

        level = self.plan.get("student_level", "medium")
        teaching_focus = self.plan.get("teaching_focus", "")

        prompt = f"""Generate an opening message for a teaching session.

Student info:
- Level: {level}
- Teaching focus: {teaching_focus}

IMPORTANT: These questions were already asked - DO NOT ask any of these again:
{json.dumps(self.already_asked, indent=2)}

Start by:
1. Welcoming them warmly
2. Briefly mentioning you'll be practicing together
3. Asking a NEW question (use {self.current_difficulty} difficulty) - must be different from the ones listed above

Keep it brief and friendly. Return JSON with "message" field."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        data = safe_json_parse(
            response.choices[0].message.content,
            {"message": "Let's practice! Can you tell me about the different roles bees have in the hive?"}
        )
        message = data.get("message", "Let's practice! Can you tell me about the different roles bees have in the hive?")
        
        self.conversation_history.append({"role": "assistant", "content": message})
        
        if data.get("asked_question"):
            self.questions_asked.append(data.get("question_difficulty", "medium"))
        
        logger.info(f"📝 Intro: {message[:80]}...")
        
        return message

    def process_message(self, user_message: str) -> dict:
        """Process student's message and generate response."""
        
        logger.info("")
        logger.info(f"{'─' * 60}")
        logger.info(f"👤 Student: {user_message[:80]}{'...' if len(user_message) > 80 else ''}")
        
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *self.conversation_history
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}
        )

        data = safe_json_parse(
            response.choices[0].message.content,
            {"message": "That's interesting! Can you tell me more?"}
        )
        message = data.get("message", "That's interesting! Can you tell me more?")
        
        # Track evaluation if present
        if "evaluation" in data and data["evaluation"]:
            eval_data = data["evaluation"]
            self.total_answers += 1
            if eval_data.get("was_correct") == True:
                self.correct_answers += 1
            elif eval_data.get("was_correct") == "partial":
                self.correct_answers += 0.5
            
            logger.info(f"📊 Evaluation: {eval_data.get('feedback_type', 'unknown')} - Score: {eval_data.get('score', 0)}")
        
        # Track question asked
        if data.get("asked_question"):
            self.questions_asked.append(data.get("question_difficulty", "medium"))
        
        # Adjust difficulty if needed
        if data.get("should_adjust_difficulty") == "up" and self.current_difficulty != "hard":
            if self.current_difficulty == "easy":
                self.current_difficulty = "medium"
            else:
                self.current_difficulty = "hard"
            logger.info(f"📈 Difficulty increased to: {self.current_difficulty}")
        elif data.get("should_adjust_difficulty") == "down" and self.current_difficulty != "easy":
            if self.current_difficulty == "hard":
                self.current_difficulty = "medium"
            else:
                self.current_difficulty = "easy"
            logger.info(f"📉 Difficulty decreased to: {self.current_difficulty}")
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": message})
        
        logger.info(f"🤖 Teacher: {message[:80]}...")
        logger.info(f"   Engagement: {data.get('engagement_level', 'unknown')} | Correct: {self.correct_answers}/{self.total_answers}")
        
        return {
            "response": message,
            "engagement_level": data.get("engagement_level", "medium"),
            "questions_asked": len(self.questions_asked),
            "accuracy": self.correct_answers / self.total_answers if self.total_answers > 0 else 0,
            "current_difficulty": self.current_difficulty
        }

    def get_session_summary(self) -> dict:
        """Get a summary of the teaching session."""
        return {
            "session_id": self.session_id,
            "questions_asked": len(self.questions_asked),
            "total_answers": self.total_answers,
            "correct_answers": self.correct_answers,
            "accuracy": self.correct_answers / self.total_answers if self.total_answers > 0 else 0,
            "final_difficulty": self.current_difficulty,
            "conversation_turns": len(self.conversation_history)
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from shared.passage import PASSAGE
    
    # Create a mock plan (simplified format)
    mock_plan = {
        "student_level": "medium",
        "teaching_focus": "Strengthen fundamentals and encourage more detailed responses. Build confidence with medium-difficulty questions."
    }
    
    print("\n")
    teacher = TeacherAgent(
        PASSAGE["title"],
        PASSAGE["content"],
        "test_session",
        mock_plan
    )
    
    print(f"Teacher: {teacher.get_intro_message()}\n")
    
    # Simulate a conversation
    test_messages = [
        "The queen bee lays all the eggs",
        "I'm not sure about the drones",
        "Oh they get kicked out because of food?",
        "That's kind of sad but makes sense"
    ]
    
    for msg in test_messages:
        print(f"Student: {msg}")
        result = teacher.process_message(msg)
        print(f"Teacher: {result['response']}")
        print(f"[Accuracy: {result['accuracy']:.0%} | Difficulty: {result['current_difficulty']}]\n")
    
    print("\n" + "=" * 60)
    print("SESSION SUMMARY:")
    print(json.dumps(teacher.get_session_summary(), indent=2))
