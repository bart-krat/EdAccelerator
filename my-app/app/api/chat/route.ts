import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';
import { evaluationQuestions, samplePassage } from '@/lib/evaluation';

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages, evaluationStage, answers } = await req.json();

  // Build the system prompt based on evaluation stage
  let systemPrompt = `You are an English comprehension learning assistant. You help students improve their reading comprehension skills.

Your communication style:
- Warm, encouraging, and supportive
- Clear and concise
- Brief responses (2-3 sentences for feedback, then the next question)

Current passage for comprehension:
Title: "${samplePassage.title}"
Content: "${samplePassage.content}"
`;

  // Add stage-specific instructions
  if (evaluationStage === 'question1') {
    // Student just answered "What is this passage about?"
    systemPrompt += `
The student just answered what the passage is about.

Briefly acknowledge their answer (1-2 sentences), then ask Question 2 (Fundamentals):

"${evaluationQuestions.question1.question}"

Ask them to type A, B, C, or D.`;
  } else if (evaluationStage === 'question2') {
    // Student answered the grammar question
    systemPrompt += `
The student just answered the grammar question.
Correct answer is: ${evaluationQuestions.question1.correctAnswer}
Explanation: ${evaluationQuestions.question1.explanation}

Briefly tell them if they got it right or wrong (1 sentence), then ask Question 3 (Understanding):

"${evaluationQuestions.question2.question}"`;
  } else if (evaluationStage === 'question3') {
    // Student answered the inference question
    systemPrompt += `
The student just answered about inference from the sentence "She smiled, but her eyes told a different story."

Briefly acknowledge their interpretation (1-2 sentences), then ask Question 4 (Interest):

"${evaluationQuestions.question3.question}"`;
  } else if (evaluationStage === 'question4') {
    // Student shared reading preferences
    systemPrompt += `
The student just shared their reading preferences.

Briefly acknowledge (1 sentence), then ask the final Question 5 (Deep Comprehension):

"${evaluationQuestions.question4.question}"`;
  } else if (evaluationStage === 'question5') {
    // Final comprehension question answered
    systemPrompt += `
The student just completed their final comprehension question about the honeybee passage.

Provide brief, encouraging feedback on their answer (2-3 sentences).

Then you MUST provide scores in EXACTLY this format at the end:

EVALUATION_SCORES:
Understanding: [0-100]
Fundamentals: [0-100]
Interest: [0-100]
Comprehension: [0-100]

Base scores on:
- Comprehension: Q1 (passage overview) + Q5 (detailed analysis) - average quality
- Fundamentals: Q2 (grammar - correct=${evaluationQuestions.question1.correctAnswer} gives 85-100, wrong gives 40-60)
- Understanding: Q3 (inference depth)
- Interest: Q4 (engagement level)

Previous answers:
Q1 (Overview): ${answers?.[0] || 'not provided'}
Q2 (Grammar): ${answers?.[1] || 'not provided'}
Q3 (Inference): ${answers?.[2] || 'not provided'}
Q4 (Interest): ${answers?.[3] || 'not provided'}`;
  } else if (evaluationStage === 'complete') {
    systemPrompt += `
The evaluation is complete. Summarize their strengths, suggest one area to improve, and offer to begin practice exercises.`;
  }

  const result = streamText({
    model: openai('gpt-4o-mini'),
    system: systemPrompt,
    messages,
  });

  return result.toDataStreamResponse();
}
