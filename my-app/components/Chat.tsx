'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ScoreCard } from './ScoreCard';
import { PassageDisplay } from './PassageDisplay';
import { EvaluationScores } from '@/lib/types';
import { samplePassage } from '@/lib/evaluation';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export function Chat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hasStarted, setHasStarted] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [scores, setScores] = useState<EvaluationScores | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFinishedReading = async () => {
    setIsLoading(true);

    try {
      // Call backend to start session and get intro message
      const response = await fetch(`${BACKEND_URL}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      const data = await response.json();

      setSessionId(data.session_id);
      setHasStarted(true);

      // Add 2 second delay before showing first message
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
    if (!inputValue.trim() || isLoading || !sessionId) return;

    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    // Add user message
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

      // Add 2 second delay before showing response
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Add assistant response
      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
      }]);

      // Check if evaluation complete
      if (data.is_complete) {
        setIsComplete(true);
        // Optionally fetch the plan/scores
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

  return (
    <div className="flex h-screen bg-[var(--bg-primary)]">
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
              placeholder={hasStarted ? "Type your message..." : "Click 'Finished Reading' to start"}
              className="flex-1 px-4 py-3 rounded-xl bg-[var(--bg-chat)] border-2 border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)] transition-colors disabled:opacity-50"
              disabled={isLoading || !hasStarted}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim() || !hasStarted}
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
