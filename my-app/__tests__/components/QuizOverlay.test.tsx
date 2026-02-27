import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuizOverlay } from '@/components/QuizOverlay';

describe('QuizOverlay', () => {
  const mockQuizData = {
    total_questions: 3,
    time_limit_seconds: 300,
    questions: [
      { id: 1, question: 'What is 2+2?', difficulty: 'easy' as const },
      { id: 2, question: 'What color is the sky?', difficulty: 'medium' as const },
      { id: 3, question: 'Explain gravity.', difficulty: 'hard' as const },
    ],
  };

  const defaultProps = {
    quizData: mockQuizData,
    sessionId: 'test-session-123',
    onComplete: jest.fn(),
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('renders quiz header', () => {
    render(<QuizOverlay {...defaultProps} />);

    expect(screen.getByText('Comprehension Quiz')).toBeInTheDocument();
  });

  it('displays all quiz questions', () => {
    render(<QuizOverlay {...defaultProps} />);

    expect(screen.getByText('What is 2+2?')).toBeInTheDocument();
    expect(screen.getByText('What color is the sky?')).toBeInTheDocument();
    expect(screen.getByText('Explain gravity.')).toBeInTheDocument();
  });

  it('shows question count in subtitle', () => {
    render(<QuizOverlay {...defaultProps} />);

    expect(screen.getByText('Answer all 3 questions below')).toBeInTheDocument();
  });

  it('displays difficulty badges for each question', () => {
    render(<QuizOverlay {...defaultProps} />);

    expect(screen.getByText('easy')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
    expect(screen.getByText('hard')).toBeInTheDocument();
  });

  it('renders question numbers', () => {
    render(<QuizOverlay {...defaultProps} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders textarea for each question', () => {
    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');
    expect(textareas).toHaveLength(3);
  });

  it('disables submit button when not all questions answered', () => {
    render(<QuizOverlay {...defaultProps} />);

    const submitButton = screen.getByRole('button', { name: /Submit Quiz/i });
    expect(submitButton).toBeDisabled();
  });

  it('updates answer count as questions are answered', async () => {
    const user = userEvent.setup();
    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');

    await user.type(textareas[0], 'Answer 1');

    expect(screen.getByText(/1\/3 answered/i)).toBeInTheDocument();
  });

  it('enables submit button when all questions are answered', async () => {
    const user = userEvent.setup();
    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');

    await user.type(textareas[0], 'Four');
    await user.type(textareas[1], 'Blue');
    await user.type(textareas[2], 'Mass attracts mass');

    const submitButton = screen.getByRole('button', { name: /Submit Quiz/i });
    expect(submitButton).not.toBeDisabled();
  });

  it('shows submitting state while submitting', async () => {
    const user = userEvent.setup();

    // Mock slow fetch
    (global.fetch as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                json: () =>
                  Promise.resolve({
                    success: true,
                    quiz_result: {
                      score: 2,
                      total: 3,
                      percentage: 66.7,
                      summary: 'Good job!',
                      question_reviews: [],
                    },
                  }),
              }),
            100
          )
        )
    );

    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');
    await user.type(textareas[0], 'Four');
    await user.type(textareas[1], 'Blue');
    await user.type(textareas[2], 'Mass');

    const submitButton = screen.getByRole('button', { name: /Submit Quiz/i });
    fireEvent.click(submitButton);

    expect(screen.getByText('Submitting...')).toBeInTheDocument();
  });

  it('shows results after successful submission', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          success: true,
          quiz_result: {
            score: 2,
            total: 3,
            percentage: 66.67,
            summary: 'Nice work on the quiz!',
            question_reviews: [
              {
                question_id: 1,
                question: 'What is 2+2?',
                user_answer: 'Four',
                correct_answer: '4',
                is_correct: true,
                feedback: 'Correct!',
                difficulty: 'easy',
              },
            ],
          },
        }),
    });

    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');
    await user.type(textareas[0], 'Four');
    await user.type(textareas[1], 'Blue');
    await user.type(textareas[2], 'Mass');

    const submitButton = screen.getByRole('button', { name: /Submit Quiz/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Quiz Results')).toBeInTheDocument();
    });

    expect(screen.getByText('2 / 3')).toBeInTheDocument();
    expect(screen.getByText('67% Correct')).toBeInTheDocument();
  });

  it('displays overall feedback after submission', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          success: true,
          quiz_result: {
            score: 3,
            total: 3,
            percentage: 100,
            summary: 'Perfect score! You understood the material excellently.',
            question_reviews: [],
          },
        }),
    });

    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');
    await user.type(textareas[0], 'Four');
    await user.type(textareas[1], 'Blue');
    await user.type(textareas[2], 'Mass');

    fireEvent.click(screen.getByRole('button', { name: /Submit Quiz/i }));

    await waitFor(() => {
      expect(screen.getByText('Overall Feedback')).toBeInTheDocument();
    });

    expect(
      screen.getByText('Perfect score! You understood the material excellently.')
    ).toBeInTheDocument();
  });

  it('calls onComplete and onClose when clicking continue after results', async () => {
    const onComplete = jest.fn();
    const onClose = jest.fn();
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          success: true,
          quiz_result: {
            score: 2,
            total: 3,
            percentage: 66.67,
            summary: 'Good!',
            question_reviews: [],
          },
        }),
    });

    render(
      <QuizOverlay {...defaultProps} onComplete={onComplete} onClose={onClose} />
    );

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');
    await user.type(textareas[0], 'Four');
    await user.type(textareas[1], 'Blue');
    await user.type(textareas[2], 'Mass');

    fireEvent.click(screen.getByRole('button', { name: /Submit Quiz/i }));

    await waitFor(() => {
      expect(screen.getByText('Continue to Review')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Continue to Review'));

    expect(onComplete).toHaveBeenCalledWith({
      score: 2,
      total: 3,
      percentage: 66.67,
    });
    expect(onClose).toHaveBeenCalled();
  });

  it('handles fetch error gracefully', async () => {
    const user = userEvent.setup();
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<QuizOverlay {...defaultProps} />);

    const textareas = screen.getAllByPlaceholderText('Type your answer here...');
    await user.type(textareas[0], 'Four');
    await user.type(textareas[1], 'Blue');
    await user.type(textareas[2], 'Mass');

    fireEvent.click(screen.getByRole('button', { name: /Submit Quiz/i }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error submitting quiz:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });
});
