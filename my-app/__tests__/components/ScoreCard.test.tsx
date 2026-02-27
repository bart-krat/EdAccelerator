import { render, screen } from '@testing-library/react';
import { ScoreCard } from '@/components/ScoreCard';
import { EvaluationScores } from '@/lib/types';

describe('ScoreCard', () => {
  const defaultScores: EvaluationScores = {
    understanding: 75,
    fundamentals: 80,
    interest: 90,
    comprehension: 85,
  };

  it('renders all score categories', () => {
    render(<ScoreCard scores={defaultScores} />);

    expect(screen.getByText('Understanding')).toBeInTheDocument();
    expect(screen.getByText('Fundamentals')).toBeInTheDocument();
    expect(screen.getByText('Interest')).toBeInTheDocument();
    expect(screen.getByText('Comprehension')).toBeInTheDocument();
  });

  it('displays individual scores correctly', () => {
    render(<ScoreCard scores={defaultScores} />);

    expect(screen.getByText('75/100')).toBeInTheDocument();
    expect(screen.getByText('80/100')).toBeInTheDocument();
    expect(screen.getByText('90/100')).toBeInTheDocument();
    expect(screen.getByText('85/100')).toBeInTheDocument();
  });

  it('calculates and displays the average correctly', () => {
    render(<ScoreCard scores={defaultScores} />);

    // Average of 75+80+90+85 = 330/4 = 82.5, rounded to 83
    expect(screen.getByText('83/100')).toBeInTheDocument();
  });

  it('displays the evaluation results header', () => {
    render(<ScoreCard scores={defaultScores} />);

    expect(screen.getByText('Your Evaluation Results')).toBeInTheDocument();
  });

  it('displays overall score label', () => {
    render(<ScoreCard scores={defaultScores} />);

    expect(screen.getByText('Overall Score')).toBeInTheDocument();
  });

  it('handles perfect scores (100)', () => {
    const perfectScores: EvaluationScores = {
      understanding: 100,
      fundamentals: 100,
      interest: 100,
      comprehension: 100,
    };

    render(<ScoreCard scores={perfectScores} />);

    // All individual scores should show 100
    const scoreTexts = screen.getAllByText('100/100');
    expect(scoreTexts.length).toBe(5); // 4 categories + overall
  });

  it('handles zero scores', () => {
    const zeroScores: EvaluationScores = {
      understanding: 0,
      fundamentals: 0,
      interest: 0,
      comprehension: 0,
    };

    render(<ScoreCard scores={zeroScores} />);

    const scoreTexts = screen.getAllByText('0/100');
    expect(scoreTexts.length).toBe(5);
  });

  it('handles mixed scores with proper average', () => {
    const mixedScores: EvaluationScores = {
      understanding: 60,
      fundamentals: 70,
      interest: 80,
      comprehension: 50,
    };

    render(<ScoreCard scores={mixedScores} />);

    // Average: (60+70+80+50)/4 = 65
    expect(screen.getByText('65/100')).toBeInTheDocument();
  });

  it('renders score bars for each category', () => {
    const { container } = render(<ScoreCard scores={defaultScores} />);

    // Each ScoreBar has a progress indicator with style width
    const progressBars = container.querySelectorAll('[style*="width"]');
    expect(progressBars.length).toBeGreaterThanOrEqual(4);
  });
});
