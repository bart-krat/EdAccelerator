'use client';

import { EvaluationScores } from '@/lib/types';

interface ScoreCardProps {
  scores: EvaluationScores;
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-400';
  };

  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-[var(--text-primary)]">{label}</span>
        <span className="text-sm font-bold text-[var(--text-primary)]">{score}/100</span>
      </div>
      <div className="w-full h-3 bg-[var(--bg-secondary)] rounded-full border border-[var(--border-light)]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getScoreColor(score)}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

export function ScoreCard({ scores }: ScoreCardProps) {
  const average = Math.round(
    (scores.understanding + scores.fundamentals + scores.interest + scores.comprehension) / 4
  );

  return (
    <div className="bg-[var(--ai-bubble)] border-2 border-[var(--border)] rounded-xl p-5 my-4">
      <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4 text-center">
        Your Evaluation Results
      </h3>

      <ScoreBar label="Understanding" score={scores.understanding} />
      <ScoreBar label="Fundamentals" score={scores.fundamentals} />
      <ScoreBar label="Interest" score={scores.interest} />
      <ScoreBar label="Comprehension" score={scores.comprehension} />

      <div className="mt-4 pt-4 border-t-2 border-[var(--border-light)]">
        <div className="flex justify-between items-center">
          <span className="text-base font-bold text-[var(--text-primary)]">Overall Score</span>
          <span className="text-2xl font-bold text-[var(--accent)]">{average}/100</span>
        </div>
      </div>
    </div>
  );
}
