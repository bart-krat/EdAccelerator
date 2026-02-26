'use client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-[var(--user-bubble)] border-2 border-[var(--border)] text-[var(--text-primary)]'
            : 'bg-[var(--ai-bubble)] border-2 border-[var(--border-light)] text-[var(--text-primary)]'
        }`}
      >
        <div className="text-xs font-medium mb-1 opacity-70">
          {isUser ? 'You' : 'Tutor'}
        </div>
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    </div>
  );
}
