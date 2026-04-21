import { useState } from 'react';

interface FeedbackWidgetProps {
  messageId: string;
  onFeedback: (messageId: string, rating: 'up' | 'down') => void;
}

export function FeedbackWidget({ messageId, onFeedback }: FeedbackWidgetProps) {
  const [submitted, setSubmitted] = useState<'up' | 'down' | null>(null);

  const handleClick = (rating: 'up' | 'down') => {
    if (submitted) return;
    setSubmitted(rating);
    onFeedback(messageId, rating);
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '8px',
        marginTop: '8px',
        alignItems: 'center',
      }}
    >
      <button
        onClick={() => handleClick('up')}
        disabled={submitted !== null}
        aria-label="Thumbs up"
        style={{
          fontSize: '16px',
          opacity: submitted === 'down' ? 0.3 : 1,
          transition: 'opacity 0.2s',
        }}
      >
        👍
      </button>
      <button
        onClick={() => handleClick('down')}
        disabled={submitted !== null}
        aria-label="Thumbs down"
        style={{
          fontSize: '16px',
          opacity: submitted === 'up' ? 0.3 : 1,
          transition: 'opacity 0.2s',
        }}
      >
        👎
      </button>
      {submitted && (
        <span style={{ fontSize: '12px', color: 'var(--rccb-gray-500)' }}>
          Thanks for your feedback
        </span>
      )}
    </div>
  );
}
