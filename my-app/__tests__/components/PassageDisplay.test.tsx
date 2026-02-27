import { render, screen, fireEvent } from '@testing-library/react';
import { PassageDisplay } from '@/components/PassageDisplay';
import { Passage } from '@/lib/types';

describe('PassageDisplay', () => {
  const samplePassage: Passage = {
    id: '1',
    title: 'Test Passage',
    content: 'First sentence. Second sentence. Third sentence.',
    difficulty: 'medium',
  };

  const defaultProps = {
    passage: samplePassage,
    onFinishedReading: jest.fn(),
    hasStarted: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders passage title', () => {
    render(<PassageDisplay {...defaultProps} />);

    expect(screen.getByText('Test Passage')).toBeInTheDocument();
  });

  it('renders passage content', () => {
    render(<PassageDisplay {...defaultProps} />);

    expect(screen.getByText(/First sentence/)).toBeInTheDocument();
    expect(screen.getByText(/Second sentence/)).toBeInTheDocument();
    expect(screen.getByText(/Third sentence/)).toBeInTheDocument();
  });

  it('displays difficulty badge', () => {
    render(<PassageDisplay {...defaultProps} />);

    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('displays reading progress header', () => {
    render(<PassageDisplay {...defaultProps} />);

    expect(screen.getByText('Reading Passage')).toBeInTheDocument();
  });

  it('shows progress bar when not started', () => {
    render(<PassageDisplay {...defaultProps} />);

    expect(screen.getByText('Reading progress')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('hides progress bar when session has started', () => {
    render(<PassageDisplay {...defaultProps} hasStarted={true} />);

    expect(screen.queryByText('Reading progress')).not.toBeInTheDocument();
  });

  it('shows disabled button when not all sentences read', () => {
    render(<PassageDisplay {...defaultProps} />);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent(/Hover over text to read/);
  });

  it('tracks hover state on sentences', () => {
    const { container } = render(<PassageDisplay {...defaultProps} />);

    // Find sentence spans
    const sentences = container.querySelectorAll('span[class*="transition-all"]');
    expect(sentences.length).toBe(3);

    // Hover over first sentence
    fireEvent.mouseEnter(sentences[0]);

    // Progress should update
    expect(screen.getByText('33%')).toBeInTheDocument();
  });

  it('enables button when all sentences are read', () => {
    const { container } = render(<PassageDisplay {...defaultProps} />);

    const sentences = container.querySelectorAll('span[class*="transition-all"]');

    // Hover over all sentences
    sentences.forEach((sentence) => {
      fireEvent.mouseEnter(sentence);
    });

    const button = screen.getByRole('button');
    expect(button).not.toBeDisabled();
    expect(button).toHaveTextContent('Finished Reading');
  });

  it('calls onFinishedReading when button is clicked after reading all', () => {
    const onFinishedReading = jest.fn();
    const { container } = render(
      <PassageDisplay {...defaultProps} onFinishedReading={onFinishedReading} />
    );

    // Read all sentences
    const sentences = container.querySelectorAll('span[class*="transition-all"]');
    sentences.forEach((sentence) => {
      fireEvent.mouseEnter(sentence);
    });

    // Click button
    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onFinishedReading).toHaveBeenCalledTimes(1);
  });

  it('does not track hover when session has started', () => {
    const { container } = render(<PassageDisplay {...defaultProps} hasStarted={true} />);

    // Should not show progress bar
    expect(screen.queryByText('Reading progress')).not.toBeInTheDocument();
  });

  it('hides finished reading button when session has started', () => {
    render(<PassageDisplay {...defaultProps} hasStarted={true} />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('correctly splits text into sentences', () => {
    const passageWithVariedPunctuation: Passage = {
      id: '2',
      title: 'Varied Passage',
      content: 'Is this a question? Yes, it is! And this is a statement.',
      difficulty: 'easy',
    };

    const { container } = render(
      <PassageDisplay
        {...defaultProps}
        passage={passageWithVariedPunctuation}
      />
    );

    const sentences = container.querySelectorAll('span[class*="transition-all"]');
    expect(sentences.length).toBe(3);
  });

  it('handles passage with single sentence', () => {
    const singleSentence: Passage = {
      id: '3',
      title: 'Short',
      content: 'Just one sentence.',
      difficulty: 'easy',
    };

    const { container } = render(
      <PassageDisplay {...defaultProps} passage={singleSentence} />
    );

    const sentences = container.querySelectorAll('span[class*="transition-all"]');
    expect(sentences.length).toBe(1);

    // Hover once should enable button
    fireEvent.mouseEnter(sentences[0]);

    const button = screen.getByRole('button');
    expect(button).not.toBeDisabled();
  });
});
