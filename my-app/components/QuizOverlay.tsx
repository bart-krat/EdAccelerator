'use client';

import { useState } from 'react';

interface QuizQuestion {
  id: number;
  question: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

interface QuizData {
  total_questions: number;
  time_limit_seconds: number;
  questions: QuizQuestion[];
}

interface QuestionReview {
  question_id: number;
  question: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  feedback: string;
  difficulty: string;
}

interface QuizResultData {
  score: number;
  total: number;
  percentage: number;
  summary: string;
  question_reviews: QuestionReview[];
}

interface QuizOverlayProps {
  quizData: QuizData;
  sessionId: string;
  onComplete: (result: { score: number; total: number; percentage: number }) => void;
  onClose: () => void;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function QuizOverlay({ quizData, sessionId, onComplete, onClose }: QuizOverlayProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizResultData | null>(null);

  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const allAnswered = quizData.questions.every(q => answers[q.id]?.trim());

  const handleSubmit = async () => {
    if (!allAnswered) return;

    setIsSubmitting(true);

    try {
      const answersList = quizData.questions.map(q => ({
        question_id: q.id,
        answer: answers[q.id] || ''
      }));

      const response = await fetch(`${BACKEND_URL}/session/${sessionId}/quiz/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answersList)
      });

      const data = await response.json();

      if (data.success) {
        setQuizResult(data.quiz_result);
        setShowResults(true);
      }
    } catch (error) {
      console.error('Error submitting quiz:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinish = () => {
    if (quizResult) {
      onComplete({
        score: quizResult.score,
        total: quizResult.total,
        percentage: quizResult.percentage
      });
    }
    onClose();
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-800 border-green-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'hard': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--bg-primary)] rounded-2xl border-2 border-[var(--border)] max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b-2 border-[var(--border)] bg-[var(--bg-secondary)]">
          <h2 className="text-xl font-bold text-[var(--text-primary)]">
            {showResults ? 'Quiz Results' : 'Comprehension Quiz'}
          </h2>
          {!showResults && (
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Answer all {quizData.total_questions} questions below
            </p>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!showResults ? (
            // Quiz Questions
            quizData.questions.map((q, index) => (
              <div key={q.id} className="bg-[var(--bg-secondary)] rounded-xl p-4 border-2 border-[var(--border)]">
                <div className="flex items-start gap-3 mb-3">
                  <span className="flex-shrink-0 w-8 h-8 rounded-full bg-[var(--accent)] text-white flex items-center justify-center font-bold">
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${getDifficultyColor(q.difficulty)}`}>
                        {q.difficulty}
                      </span>
                    </div>
                    <p className="text-[var(--text-primary)] font-medium">{q.question}</p>
                  </div>
                </div>
                <textarea
                  value={answers[q.id] || ''}
                  onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                  placeholder="Type your answer here..."
                  className="w-full px-4 py-3 rounded-xl bg-[var(--bg-chat)] border-2 border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)] transition-colors resize-none"
                  rows={3}
                />
              </div>
            ))
          ) : (
            // Results with LLM Review
            <>
              {/* Score Summary */}
              <div className="bg-[var(--accent)] text-white rounded-xl p-6 text-center">
                <div className="text-4xl font-bold mb-2">
                  {quizResult?.score} / {quizResult?.total}
                </div>
                <div className="text-lg opacity-90">
                  {quizResult?.percentage.toFixed(0)}% Correct
                </div>
              </div>

              {/* LLM Summary */}
              {quizResult?.summary && (
                <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4">
                  <h3 className="font-bold text-blue-800 mb-2">Overall Feedback</h3>
                  <p className="text-blue-900">{quizResult.summary}</p>
                </div>
              )}

              {/* Individual Question Reviews */}
              <h3 className="font-bold text-[var(--text-primary)] mt-4">Question Review</h3>
              {quizResult?.question_reviews?.map((r, index) => (
                <div
                  key={r.question_id}
                  className={`rounded-xl p-4 border-2 ${
                    r.is_correct
                      ? 'bg-green-50 border-green-300'
                      : 'bg-red-50 border-red-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      r.is_correct ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                      {r.is_correct ? '✓' : '✗'}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <p className="font-medium text-gray-800">
                          {index + 1}. {r.question}
                        </p>
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${getDifficultyColor(r.difficulty)}`}>
                          {r.difficulty}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">
                        <span className="font-medium">Your answer:</span> {r.user_answer}
                      </p>
                      {!r.is_correct && (
                        <p className="text-sm text-gray-600 mb-1">
                          <span className="font-medium">Correct answer:</span> {r.correct_answer}
                        </p>
                      )}
                      <p className="text-sm text-gray-700 mt-2 p-2 bg-white/50 rounded-lg italic">
                        {r.feedback}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t-2 border-[var(--border)] bg-[var(--bg-secondary)]">
          {!showResults ? (
            <button
              onClick={handleSubmit}
              disabled={!allAnswered || isSubmitting}
              className="w-full px-6 py-3 rounded-xl bg-[var(--accent)] text-white font-medium hover:bg-[var(--accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors border-2 border-[var(--border)]"
            >
              {isSubmitting ? 'Submitting...' : `Submit Quiz (${Object.keys(answers).length}/${quizData.total_questions} answered)`}
            </button>
          ) : (
            <button
              onClick={handleFinish}
              className="w-full px-6 py-3 rounded-xl bg-[var(--accent)] text-white font-medium hover:bg-[var(--accent-hover)] transition-colors border-2 border-[var(--border)]"
            >
              Continue to Review
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
