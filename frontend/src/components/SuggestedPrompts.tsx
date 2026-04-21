import type { SuggestedPrompt } from '../data/types';

interface SuggestedPromptsProps {
  prompts: SuggestedPrompt[];
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export function SuggestedPrompts({ prompts, onSelect, disabled }: SuggestedPromptsProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        justifyContent: 'center',
        maxWidth: '800px',
        margin: '0 auto',
        padding: '0 24px 8px',
      }}
    >
      {prompts.map((prompt, i) => (
        <button
          key={i}
          onClick={() => onSelect(prompt.text)}
          disabled={disabled}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            background: 'var(--rccb-white)',
            border: '1px solid var(--rccb-gray-200)',
            borderRadius: '20px',
            fontSize: '13px',
            color: 'var(--rccb-gray-700)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={(e) => {
            if (!disabled) {
              e.currentTarget.style.borderColor = 'var(--rccb-red)';
              e.currentTarget.style.color = 'var(--rccb-red)';
              e.currentTarget.style.background = '#FFF5F5';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--rccb-gray-200)';
            e.currentTarget.style.color = 'var(--rccb-gray-700)';
            e.currentTarget.style.background = 'var(--rccb-white)';
          }}
        >
          <span>{prompt.icon}</span>
          <span>{prompt.text}</span>
        </button>
      ))}
    </div>
  );
}
