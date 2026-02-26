'use client';

import { useState } from 'react';
import { Passage } from '@/lib/types';

interface PassageDisplayProps {
  passage: Passage;
  onFinishedReading: () => void;
  hasStarted: boolean;
}

function splitIntoSentences(text: string): string[] {
  // Split by sentence-ending punctuation, keeping the punctuation
  return text.match(/[^.!?]+[.!?]+\s*/g) || [text];
}

export function PassageDisplay({ passage, onFinishedReading, hasStarted }: PassageDisplayProps) {
  const sentences = splitIntoSentences(passage.content);
  const [readSentences, setReadSentences] = useState<Set<number>>(new Set());

  const handleSentenceHover = (index: number) => {
    if (!hasStarted) {
      setReadSentences(prev => new Set(prev).add(index));
    }
  };

  const readProgress = (readSentences.size / sentences.length) * 100;
  const allRead = readSentences.size === sentences.length;

  return (
    <div className="h-full flex flex-col bg-[var(--bg-chat)] border-r-2 border-[var(--border)]">
      {/* Header */}
      <div className="px-6 py-4 border-b-2 border-[var(--border)] bg-[var(--bg-secondary)]">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[var(--text-primary)]">Reading Passage</h2>
          <span className="text-xs px-2 py-1 rounded-full bg-[var(--accent)] text-white font-medium">
            {passage.difficulty}
          </span>
        </div>

        {/* Progress bar */}
        {!hasStarted && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-1">
              <span>Reading progress</span>
              <span>{Math.round(readProgress)}%</span>
            </div>
            <div className="w-full h-2 bg-[var(--bg-primary)] rounded-full border border-[var(--border-light)]">
              <div
                className="h-full rounded-full bg-[var(--accent)] transition-all duration-300"
                style={{ width: `${readProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Passage Content */}
      <div className="flex-1 overflow-y-auto chat-scroll p-6">
        <h3 className="text-xl font-bold text-[var(--text-primary)] mb-4">
          {passage.title}
        </h3>
        <div className="text-sm leading-relaxed">
          {sentences.map((sentence, index) => (
            <span
              key={index}
              onMouseEnter={() => handleSentenceHover(index)}
              className={`transition-all duration-300 cursor-default ${
                hasStarted || readSentences.has(index)
                  ? 'text-[var(--text-primary)]'
                  : 'text-[var(--text-primary)]/30 hover:text-[var(--text-primary)]'
              }`}
            >
              {sentence}
            </span>
          ))}
        </div>
      </div>

      {/* Finished Reading Button */}
      {!hasStarted && (
        <div className="px-6 py-4 border-t-2 border-[var(--border)] bg-[var(--bg-secondary)]">
          <button
            onClick={onFinishedReading}
            disabled={!allRead}
            className={`w-full px-6 py-3 rounded-xl font-medium transition-all duration-300 border-2 border-[var(--border)] ${
              allRead
                ? 'bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] cursor-pointer'
                : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] cursor-not-allowed opacity-60'
            }`}
          >
            {allRead ? 'Finished Reading' : `Hover over text to read (${Math.round(readProgress)}%)`}
          </button>
        </div>
      )}
    </div>
  );
}
