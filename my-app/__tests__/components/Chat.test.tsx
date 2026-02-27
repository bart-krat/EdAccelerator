import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Chat } from '@/components/Chat';

// Mock the child components to simplify testing
jest.mock('@/components/ChatMessage', () => ({
  ChatMessage: ({ message }: { message: { content: string; role: string } }) => (
    <div data-testid={`message-${message.role}`}>{message.content}</div>
  ),
}));

jest.mock('@/components/ScoreCard', () => ({
  ScoreCard: () => <div data-testid="score-card">Score Card</div>,
}));

jest.mock('@/components/PassageDisplay', () => ({
  PassageDisplay: ({
    onFinishedReading,
    hasStarted,
  }: {
    onFinishedReading: () => void;
    hasStarted: boolean;
  }) => (
    <div data-testid="passage-display">
      {!hasStarted && (
        <button onClick={onFinishedReading} data-testid="finish-reading-btn">
          Finished Reading
        </button>
      )}
    </div>
  ),
}));

jest.mock('@/components/QuizOverlay', () => ({
  QuizOverlay: ({
    onComplete,
    onClose,
  }: {
    onComplete: (result: { score: number; total: number; percentage: number }) => void;
    onClose: () => void;
  }) => (
    <div data-testid="quiz-overlay">
      <button
        onClick={() => {
          onComplete({ score: 3, total: 5, percentage: 60 });
          onClose();
        }}
        data-testid="complete-quiz-btn"
      >
        Complete Quiz
      </button>
    </div>
  ),
}));

describe('Chat', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('renders initial state with passage display', () => {
    render(<Chat />);

    expect(screen.getByTestId('passage-display')).toBeInTheDocument();
  });

  it('shows instruction message before starting', () => {
    render(<Chat />);

    expect(
      screen.getByText(/Read the passage on the left/i)
    ).toBeInTheDocument();
  });

  it('disables input before session starts', () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText(/Click 'Finished Reading' to start/i);
    expect(input).toBeDisabled();
  });

  it('starts session when finished reading is clicked', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          session_id: 'test-session-123',
          message: 'Welcome to your learning session!',
          mode: 'evaluator',
        }),
    });

    render(<Chat />);

    const finishButton = screen.getByTestId('finish-reading-btn');
    fireEvent.click(finishButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/start',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  it('displays welcome message after session starts', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          session_id: 'test-session-123',
          message: 'Welcome to your learning session!',
          mode: 'evaluator',
        }),
    });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(
          screen.getByText('Welcome to your learning session!')
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('enables input after session starts', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          session_id: 'test-session-123',
          message: 'Welcome!',
          mode: 'evaluator',
        }),
    });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        const input = screen.getByPlaceholderText('Type your message...');
        expect(input).not.toBeDisabled();
      },
      { timeout: 3000 }
    );
  });

  it('shows current phase indicator after starting', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          session_id: 'test-session-123',
          message: 'Welcome!',
          mode: 'evaluator',
        }),
    });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByText('Assessment')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('sends message when form is submitted', async () => {
    const user = userEvent.setup();

    // Mock start session
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          session_id: 'test-session-123',
          message: 'Welcome!',
          mode: 'evaluator',
        }),
    });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('Type your message...')).not.toBeDisabled();
      },
      { timeout: 3000 }
    );

    // Mock chat response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          response: 'Great answer!',
          is_complete: false,
          phase: 'evaluator',
        }),
    });

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'My answer');

    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/chat',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('My answer'),
        })
      );
    });
  });

  it('displays user message after sending', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            session_id: 'test-session-123',
            message: 'Welcome!',
            mode: 'evaluator',
          }),
      })
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            response: 'Great!',
            is_complete: false,
            phase: 'evaluator',
          }),
      });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('Type your message...')).not.toBeDisabled();
      },
      { timeout: 3000 }
    );

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Hello tutor');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toHaveTextContent('Hello tutor');
    });
  });

  it('clears input after sending message', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            session_id: 'test-session-123',
            message: 'Welcome!',
            mode: 'evaluator',
          }),
      })
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            response: 'Great!',
            is_complete: false,
            phase: 'evaluator',
          }),
      });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('Type your message...')).not.toBeDisabled();
      },
      { timeout: 3000 }
    );

    const input = screen.getByPlaceholderText('Type your message...') as HTMLInputElement;
    await user.type(input, 'My message');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(input.value).toBe('');
  });

  it('shows loading indicator while waiting for response', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          session_id: 'test-session-123',
          message: 'Welcome!',
          mode: 'evaluator',
        }),
    });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('Type your message...')).not.toBeDisabled();
      },
      { timeout: 3000 }
    );

    // Mock slow response
    (global.fetch as jest.Mock).mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                json: () =>
                  Promise.resolve({
                    response: 'Response',
                    is_complete: false,
                    phase: 'evaluator',
                  }),
              }),
            500
          )
        )
    );

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Test');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    // Loading indicator should appear (animated dots)
    const loadingContainer = document.querySelector('.animate-bounce');
    expect(loadingContainer).toBeInTheDocument();
  });

  it('handles error response gracefully', async () => {
    const user = userEvent.setup();
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            session_id: 'test-session-123',
            message: 'Welcome!',
            mode: 'evaluator',
          }),
      })
      .mockRejectedValueOnce(new Error('Network error'));

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('Type your message...')).not.toBeDisabled();
      },
      { timeout: 3000 }
    );

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Test');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText(/Sorry, there was an error/i)).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('shows quiz button when quiz data is received', async () => {
    const user = userEvent.setup();

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            session_id: 'test-session-123',
            message: 'Welcome!',
            mode: 'evaluator',
          }),
      })
      .mockResolvedValueOnce({
        json: () =>
          Promise.resolve({
            response: 'Time for a quiz!',
            is_complete: false,
            phase: 'quiz',
            show_quiz: true,
            quiz_data: {
              total_questions: 5,
              time_limit_seconds: 300,
              questions: [{ id: 1, question: 'Q1?', difficulty: 'easy' }],
            },
          }),
      });

    render(<Chat />);

    fireEvent.click(screen.getByTestId('finish-reading-btn'));

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('Type your message...')).not.toBeDisabled();
      },
      { timeout: 3000 }
    );

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Ready for quiz');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(
      () => {
        expect(screen.getByText('Start Quiz')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });
});
