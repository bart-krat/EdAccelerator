export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface EvaluationScores {
  understanding: number;
  fundamentals: number;
  interest: number;
  comprehension: number;
}

export interface EvaluationState {
  stage: 'intro' | 'idle' | 'question1' | 'question2' | 'question3' | 'question4' | 'question5' | 'scoring' | 'complete';
  answers: string[];
  scores: EvaluationScores | null;
}

export interface Passage {
  id: string;
  title: string;
  content: string;
  difficulty: 'easy' | 'medium' | 'hard';
}
