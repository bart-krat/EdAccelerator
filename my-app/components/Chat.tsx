'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ScoreCard } from './ScoreCard';
import { PassageDisplay } from './PassageDisplay';
import { QuizOverlay } from './QuizOverlay';
import { EvaluationScores } from '@/lib/types';
import { samplePassage } from '@/lib/evaluation';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface QuizData {
  total_questions: number;
  time_limit_seconds: number;
  questions: { id: number; question: string; difficulty: 'easy' | 'medium' | 'hard' }[];
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function Chat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hasStarted, setHasStarted] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [scores, setScores] = useState<EvaluationScores | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string>('evaluator');

  // Quiz state
  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [showQuizButton, setShowQuizButton] = useState(false);
  const [showQuizOverlay, setShowQuizOverlay] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFinishedReading = async () => {
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      const data = await response.json();

      setSessionId(data.session_id);
      setHasStarted(true);
      setCurrentPhase(data.mode || 'evaluator');

      await new Promise(resolve => setTimeout(resolve, 2000));

      setMessages([
        {
          id: 'intro',
          role: 'assistant',
          content: data.message,
        },
      ]);
    } catch (error) {
      console.error('Error starting session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading || !sessionId || showQuizButton) return;

    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: currentInput,
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: currentInput,
        }),
      });

      const data = await response.json();

      await new Promise(resolve => setTimeout(resolve, 2000));

      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
      }]);

      setCurrentPhase(data.phase || currentPhase);

      // Check if quiz is ready
      if (data.show_quiz && data.quiz_data) {
        setQuizData(data.quiz_data);
        setShowQuizButton(true);
      }

      if (data.is_complete) {
        setIsComplete(true);
      }

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, there was an error. Please try again.',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartQuiz = () => {
    setShowQuizButton(false);
    setShowQuizOverlay(true);
  };

  const handleQuizComplete = (result: { score: number; total: number; percentage: number }) => {
    setShowQuizOverlay(false);
    setCurrentPhase('review');

    // Add a message about quiz completion
    setMessages(prev => [...prev, {
      id: `quiz-result-${Date.now()}`,
      role: 'assistant',
      content: `**Quiz Complete!**\n\nYou scored ${result.score}/${result.total} (${result.percentage.toFixed(0)}%).\n\nGreat job completing your learning session! Feel free to ask any questions about your performance.`,
    }]);
  };

  const handleQuizClose = () => {
    setShowQuizOverlay(false);
  };

  // Get phase display name
  const getPhaseLabel = () => {
    switch (currentPhase) {
      case 'evaluator': return 'Assessment';
      case 'teacher': return 'Practice';
      case 'quiz': return 'Quiz';
      case 'review': return 'Review';
      default: return '';
    }
  };

  return (
    <div className="flex h-screen bg-[var(--bg-primary)]">
      {/* Quiz Overlay */}
      {showQuizOverlay && quizData && sessionId && (
        <QuizOverlay
          quizData={quizData}
          sessionId={sessionId}
          onComplete={handleQuizComplete}
          onClose={handleQuizClose}
        />
      )}

      {/* Left Side - Passage Display */}
      <div className="w-[450px] flex-shrink-0">
        <PassageDisplay
          passage={samplePassage}
          onFinishedReading={handleFinishedReading}
          hasStarted={hasStarted}
        />
      </div>

      {/* Right Side - Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Phase Indicator */}
        {hasStarted && (
          <div className="px-6 py-2 bg-[var(--bg-secondary)] border-b-2 border-[var(--border)]">
            <div className="flex items-center gap-2">
              <span className="text-sm text-[var(--text-secondary)]">Current Phase:</span>
              <span className="text-sm font-medium text-[var(--accent)]">{getPhaseLabel()}</span>
            </div>
          </div>
        )}

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto chat-scroll px-6 py-4">
          <div className="max-w-2xl">
            {/* Empty state */}
            {!hasStarted && messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-[var(--text-secondary)]">
                <p className="text-center">
                  Read the passage on the left, then click "Finished Reading" to begin.
                </p>
              </div>
            )}

            {/* Messages */}
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Start Quiz Button */}
            {showQuizButton && (
              <div className="flex justify-center my-6">
                <button
                  onClick={handleStartQuiz}
                  className="px-8 py-4 rounded-xl bg-[var(--accent)] text-white font-bold text-lg hover:bg-[var(--accent-hover)] transition-colors border-2 border-[var(--border)] shadow-lg"
                >
                  Start Quiz
                </button>
              </div>
            )}

            {/* Score card */}
            {scores && <ScoreCard scores={scores} />}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-[var(--ai-bubble)] border-2 border-[var(--border-light)] rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Input Area */}
        <footer className="bg-[var(--bg-secondary)] border-t-2 border-[var(--border)] px-6 py-4">
          <form onSubmit={onSubmit} className="flex gap-3 max-w-2xl">
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              placeholder={
                showQuizButton
                  ? "Click 'Start Quiz' to continue"
                  : hasStarted
                    ? "Type your message..."
                    : "Click 'Finished Reading' to start"
              }
              className="flex-1 px-4 py-3 rounded-xl bg-[var(--bg-chat)] border-2 border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)] transition-colors disabled:opacity-50"
              disabled={isLoading || !hasStarted || showQuizButton}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim() || !hasStarted || showQuizButton}
              className="px-6 py-3 rounded-xl bg-[var(--accent)] text-white font-medium hover:bg-[var(--accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors border-2 border-[var(--border)]"
            >
              Send
            </button>
          </form>
        </footer>
      </div>
    </div>
  );
}
