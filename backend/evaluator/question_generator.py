"""
Question Generator

Sends the passage to OpenAI and generates 3 pools of questions:
- Easy (5 questions)
- Medium (5 questions)  
- Hard (5 questions)
"""

from openai import OpenAI
from pydantic import BaseModel
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


def generate_questions(passage_title: str, passage_content: str) -> QuestionPool:
    """
    Generate 3 pools of comprehension questions based on the passage.
    """
    
    prompt = f"""You are an expert English teacher creating comprehension questions.

Read this passage:

Title: {passage_title}

{passage_content}

Generate 15 comprehension questions divided into 3 difficulty levels:

EASY (5 questions):
- Direct recall from the text
- Simple "what", "who", "where" questions
- Answers are explicitly stated in the passage

MEDIUM (5 questions):
- Require some inference
- "Why" and "how" questions
- Need to connect multiple parts of the text

HARD (5 questions):
- Deep analysis and critical thinking
- Compare, contrast, evaluate
- Apply concepts to new situations
- Infer author's purpose or tone

Return your response as JSON in this exact format:
{{
    "easy": [
        {{"question": "...", "answer": "...", "explanation": "..."}},
        ...
    ],
    "medium": [
        {{"question": "...", "answer": "...", "explanation": "..."}},
        ...
    ],
    "hard": [
        {{"question": "...", "answer": "...", "explanation": "..."}},
        ...
    ]
}}

Each question should have:
- question: The question text
- answer: The correct/expected answer
- explanation: Why this is the correct answer (for feedback)
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert English teacher. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return QuestionPool(**result)


if __name__ == "__main__":
    # Test the generator
    from shared.passage import PASSAGE
    
    print("Generating questions for passage...")
    questions = generate_questions(PASSAGE["title"], PASSAGE["content"])
    
    print("\n=== EASY QUESTIONS ===")
    for i, q in enumerate(questions.easy, 1):
        print(f"\n{i}. {q.question}")
        print(f"   Answer: {q.answer}")
    
    print("\n=== MEDIUM QUESTIONS ===")
    for i, q in enumerate(questions.medium, 1):
        print(f"\n{i}. {q.question}")
        print(f"   Answer: {q.answer}")
    
    print("\n=== HARD QUESTIONS ===")
    for i, q in enumerate(questions.hard, 1):
        print(f"\n{i}. {q.question}")
        print(f"   Answer: {q.answer}")
