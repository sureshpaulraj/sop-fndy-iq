import { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { LoadingSkeleton } from './LoadingSkeleton';
import { SuggestedPrompts } from './SuggestedPrompts';
import type { Message, Citation, SuggestedPrompt } from '../data/types';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSend: (query: string) => void;
  onFeedback: (messageId: string, rating: 'up' | 'down') => void;
  onCitationClick: (citations: Citation[]) => void;
  suggestedPrompts?: SuggestedPrompt[];
}

export function ChatWindow({
  messages,
  isLoading,
  onSend,
  onFeedback,
  onCitationClick,
  suggestedPrompts,
}: ChatWindowProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput('');
    inputRef.current?.focus();
  };

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        marginTop: 'var(--header-height)',
        marginLeft: 'var(--sidebar-width)',
        background: 'var(--rccb-gray-100)',
      }}
    >
      {/* Messages Area */}
      <div
        role="log"
        aria-label="Chat messages"
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        {messages.length === 0 && !isLoading && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              gap: '16px',
              color: 'var(--rccb-gray-500)',
            }}
          >
            <div style={{ fontSize: '48px' }}>📋</div>
            <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--rccb-dark)' }}>
              SOP Assistant
            </h2>
            <p>Ask a question about Standard Operating Procedures</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onFeedback={onFeedback}
            onCitationClick={onCitationClick}
            onFollowUp={onSend}
          />
        ))}

        {isLoading && <LoadingSkeleton />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: '16px 24px 8px',
          borderTop: '1px solid var(--rccb-gray-200)',
          background: 'var(--rccb-white)',
        }}
      >
        <div
          style={{
            display: 'flex',
            gap: '8px',
            maxWidth: '800px',
            margin: '0 auto',
          }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about SOPs..."
            disabled={isLoading}
            aria-label="Chat input"
            style={{
              flex: 1,
              padding: '12px 16px',
              border: '1px solid var(--rccb-gray-300)',
              borderRadius: '8px',
              fontSize: '15px',
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--rccb-red)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--rccb-gray-300)')}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
            style={{
              padding: '12px 24px',
              background: input.trim() ? 'var(--rccb-red)' : 'var(--rccb-gray-300)',
              color: 'var(--rccb-white)',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '14px',
              transition: 'background 0.2s',
            }}
          >
            Send
          </button>
        </div>
      </form>

      {/* Suggested Prompts */}
      {suggestedPrompts && suggestedPrompts.length > 0 && messages.length === 0 && (
        <div style={{ background: 'var(--rccb-white)', paddingBottom: '12px' }}>
          <SuggestedPrompts
            prompts={suggestedPrompts}
            onSelect={onSend}
            disabled={isLoading}
          />
        </div>
      )}
    </div>
  );
}
