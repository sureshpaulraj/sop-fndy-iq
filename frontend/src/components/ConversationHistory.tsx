import type { Conversation } from '../data/types';

interface ConversationHistoryProps {
  conversations: Conversation[];
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
}

export function ConversationHistory({
  conversations,
  onNewChat,
  onSelectConversation,
}: ConversationHistoryProps) {
  return (
    <div
      style={{
        width: 'var(--sidebar-width)',
        marginTop: 'var(--header-height)',
        borderRight: '1px solid var(--contoso-gray-200)',
        background: 'var(--contoso-white)',
        overflow: 'auto',
        padding: '16px',
        position: 'fixed',
        left: 0,
        top: 'var(--header-height)',
        bottom: 0,
      }}
    >
      <button
        onClick={onNewChat}
        style={{
          width: '100%',
          padding: '10px',
          borderRadius: '8px',
          border: '1px solid var(--contoso-gray-300)',
          background: 'var(--contoso-white)',
          fontWeight: 500,
          fontSize: '13px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          justifyContent: 'center',
        }}
      >
        ＋ New Chat
      </button>

      {conversations.length === 0 ? (
        <div style={{ color: 'var(--contoso-gray-500)', fontSize: '13px', textAlign: 'center' }}>
          No conversations yet
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              style={{
                padding: '8px 10px',
                borderRadius: '6px',
                textAlign: 'left',
                fontSize: '13px',
                color: 'var(--contoso-dark)',
                width: '100%',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {conv.title}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
