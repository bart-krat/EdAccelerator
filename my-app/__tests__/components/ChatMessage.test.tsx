import { render, screen } from '@testing-library/react';
import { ChatMessage } from '@/components/ChatMessage';

describe('ChatMessage', () => {
  it('renders user message with correct content', () => {
    const message = {
      id: 'user-1',
      role: 'user' as const,
      content: 'Hello, tutor!',
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByText('Hello, tutor!')).toBeInTheDocument();
  });

  it('renders assistant message with correct content', () => {
    const message = {
      id: 'assistant-1',
      role: 'assistant' as const,
      content: 'Hello! How can I help you today?',
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
  });

  it('displays "You" label for user messages', () => {
    const message = {
      id: 'user-1',
      role: 'user' as const,
      content: 'Test message',
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByText('You')).toBeInTheDocument();
  });

  it('displays "Tutor" label for assistant messages', () => {
    const message = {
      id: 'assistant-1',
      role: 'assistant' as const,
      content: 'Test response',
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByText('Tutor')).toBeInTheDocument();
  });

  it('applies correct alignment for user messages', () => {
    const message = {
      id: 'user-1',
      role: 'user' as const,
      content: 'User message',
    };

    const { container } = render(<ChatMessage message={message} />);

    // User messages should be right-aligned (justify-end)
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('justify-end');
  });

  it('applies correct alignment for assistant messages', () => {
    const message = {
      id: 'assistant-1',
      role: 'assistant' as const,
      content: 'Assistant message',
    };

    const { container } = render(<ChatMessage message={message} />);

    // Assistant messages should be left-aligned (justify-start)
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('justify-start');
  });

  it('renders multiline content correctly', () => {
    const message = {
      id: 'assistant-1',
      role: 'assistant' as const,
      content: 'Line 1\nLine 2\nLine 3',
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByText('Line 1\nLine 2\nLine 3')).toBeInTheDocument();
  });

  it('handles empty content', () => {
    const message = {
      id: 'user-1',
      role: 'user' as const,
      content: '',
    };

    const { container } = render(<ChatMessage message={message} />);

    // Should still render the message bubble
    expect(container.querySelector('.rounded-2xl')).toBeInTheDocument();
  });

  it('renders long messages without breaking layout', () => {
    const longContent = 'A'.repeat(500);
    const message = {
      id: 'assistant-1',
      role: 'assistant' as const,
      content: longContent,
    };

    const { container } = render(<ChatMessage message={message} />);

    // Message bubble should have max-width constraint
    const bubble = container.querySelector('.max-w-\\[80\\%\\]');
    expect(bubble).toBeInTheDocument();
  });
});
