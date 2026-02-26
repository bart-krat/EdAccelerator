"""
One-time script to generate questions and save to JSON.
Run this once, then the evaluator loads from the cached file.
"""

from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PASSAGE = {
    "title": "The Secret Life of Honeybees",
    "content": """Inside every beehive, there is a world more organized than most human cities. A single hive can contain up to 60,000 bees, and every single one has a job to do. At the center of the hive is the queen bee. She is the only bee that lays eggs—up to 2,000 per day during summer. Despite her title, the queen doesn't actually make decisions for the hive. Her main job is simply to lay eggs and keep the colony growing.

The worker bees are all female, and they do everything else. Young workers stay inside the hive, cleaning cells, feeding larvae, and building honeycomb from wax they produce from their own bodies. As they get older, they graduate to guarding the hive entrance. The oldest workers become foragers, flying up to five miles from the hive to collect nectar and pollen.

Male bees are called drones. They don't collect food, don't guard the hive, and don't have stingers. Their only purpose is to mate with queens from other hives. In autumn, when food becomes scarce, the workers push the drones out of the hive to conserve resources.

Bees communicate through dancing. When a forager finds a good source of flowers, she returns to the hive and performs a 'waggle dance' that tells other bees exactly where to find the food. The angle of her dance shows the direction relative to the sun, and the length of her waggle shows the distance.

This tiny insect has been making honey the same way for over 100 million years. Every spoonful of honey represents the life's work of about twelve bees."""
}


def generate_and_save():
    prompt = f"""You are an expert English teacher creating comprehension questions.

Read this passage:

Title: {PASSAGE['title']}

{PASSAGE['content']}

Generate 15 comprehension questions divided into 3 difficulty levels:

EASY (5 questions): Direct recall, simple what/who/where questions
MEDIUM (5 questions): Require inference, why/how questions  
HARD (5 questions): Deep analysis, critical thinking, author's purpose

Return JSON:
{{
    "easy": [{{"question": "...", "answer": "...", "explanation": "..."}}],
    "medium": [{{"question": "...", "answer": "...", "explanation": "..."}}],
    "hard": [{{"question": "...", "answer": "...", "explanation": "..."}}]
}}"""

    print("Calling OpenAI to generate questions...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    questions = json.loads(response.choices[0].message.content)
    
    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), "questions_cache.json")
    with open(output_path, "w") as f:
        json.dump(questions, f, indent=2)
    
    print(f"Saved to {output_path}")
    print(f"\nGenerated {len(questions['easy'])} easy, {len(questions['medium'])} medium, {len(questions['hard'])} hard questions")
    
    return questions


if __name__ == "__main__":
    questions = generate_and_save()
    
    print("\n=== EASY ===")
    for q in questions["easy"]:
        print(f"- {q['question']}")
    
    print("\n=== MEDIUM ===")
    for q in questions["medium"]:
        print(f"- {q['question']}")
    
    print("\n=== HARD ===")
    for q in questions["hard"]:
        print(f"- {q['question']}")
