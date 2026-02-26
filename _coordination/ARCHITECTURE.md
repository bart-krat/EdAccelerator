# Architecture - EdAccelerator

## What We're Building
An AI-powered English comprehension learning app with a single chat interface. The app evaluates student literacy levels through a structured assessment (3 hardcoded questions + 1 text-based comprehension question), then provides adaptive practice questions to improve their skills.

Key user needs: Assess current reading level, get personalized comprehension practice, track improvement across Understanding, Fundamentals, Interest, and Comprehension dimensions.

## Tech Stack
**Language:** TypeScript
**Framework:** Next.js 14 (App Router)
**AI:** Vercel AI SDK + OpenAI/Anthropic
**Styling:** Tailwind CSS (pastel yellow + brown theme)
**Deployment:** Vercel
**State:** React state (no database needed for MVP - session-based)

**Rationale:** Next.js + Vercel AI SDK is the fastest path to a production chat interface on Vercel. No database keeps deployment simple for interview demo. Tailwind makes custom theming easy.

## System Components

- **Chat Interface:** Single conversational UI for all interactions
- **Evaluation Engine:** Manages the 4-question assessment flow and scoring
- **Passage Display:** Shows reading passages alongside chat
- **Score Calculator:** Computes Understanding, Fundamentals, Interest, Comprehension scores
- **AI Service:** Handles prompt engineering for evaluation and adaptive questions

## File Structure
```
src/
  app/
    page.tsx              # Main chat interface
    layout.tsx            # Root layout with theme
    api/
      chat/
        route.ts          # AI chat endpoint
    globals.css           # Pastel yellow/brown theme
  components/
    Chat.tsx              # Chat container
    ChatMessage.tsx       # Individual message bubble
    PassageDisplay.tsx    # Text passage component
    ScoreCard.tsx         # Shows evaluation scores
    QuestionCard.tsx      # Displays current question
  lib/
    evaluation.ts         # Hardcoded questions + scoring logic
    prompts.ts            # AI prompt templates
    types.ts              # TypeScript interfaces
  data/
    passages.ts           # Sample reading passages
    questions.ts          # Hardcoded evaluation questions
```

## Feature Roadmap (Priority Order)

### Phase 1 - Bootstrap (Get it running)
1. Basic chat UI with pastel yellow/brown theme
2. Hardcoded passage display
3. AI chat integration via Vercel AI SDK
4. Deploy to Vercel

### Phase 2 - Evaluation Flow (Core Feature)
5. 3 hardcoded evaluation questions (non-text-dependent)
6. 1 AI-generated comprehension question based on passage
7. Score calculation (Understanding, Fundamentals, Interest, Comprehension)
8. Score display card after evaluation

### Phase 3 - Adaptive Practice
9. AI generates practice questions based on evaluation scores
10. Track correct/incorrect responses in session
11. Difficulty adjustment based on performance

### Phase 4 - Polish
12. Multiple passage options
13. Progress visualization
14. Better mobile responsiveness

## Production Considerations

**Security:** API route validates requests, rate limiting via Vercel
**Error Handling:** Graceful fallbacks if AI fails, user-friendly error messages
**Logging:** Console logging for MVP, can add Vercel Analytics later
**Performance:** Stream AI responses for better UX

## Data Model

```typescript
interface EvaluationState {
  stage: 'intro' | 'evaluation' | 'scoring' | 'practice';
  currentQuestion: number;
  answers: Answer[];
  scores: {
    understanding: number;    // 0-100
    fundamentals: number;     // 0-100
    interest: number;         // 0-100
    comprehension: number;    // 0-100
  };
}

interface Answer {
  questionId: string;
  response: string;
  isCorrect?: boolean;
  aiEvaluation?: string;
}

interface Passage {
  id: string;
  title: string;
  content: string;
  difficulty: 'easy' | 'medium' | 'hard';
}
```

## Evaluation Questions Design

**Hardcoded Questions (assess baseline):**
1. **Fundamentals:** Grammar/vocabulary question (multiple choice)
2. **Understanding:** Inference question about a short provided sentence
3. **Interest:** Open-ended question about reading preferences

**AI-Generated Question:**
4. **Comprehension:** Complex question requiring synthesis of passage content

## Scoring Logic

- **Fundamentals:** Based on Q1 correctness (0, 50, or 100)
- **Understanding:** Based on Q2 quality, AI evaluates (0-100)
- **Interest:** Based on Q3 engagement level, AI evaluates (0-100)
- **Comprehension:** Based on Q4 depth of analysis, AI evaluates (0-100)

## Theme Specification

```css
/* Pastel Yellow + Brown */
--bg-primary: #FFF9E6;      /* Light pastel yellow */
--bg-secondary: #FFF3CC;    /* Slightly darker yellow */
--border: #8B7355;          /* Warm brown */
--text-primary: #5C4033;    /* Dark brown */
--accent: #D4A574;          /* Light brown accent */
```
