import { useState } from 'react';
import { ChatWindow } from './components/ChatWindow';
import { ConversationHistory } from './components/ConversationHistory';
import { CitationPanel } from './components/CitationPanel';
import { UserProfileMenu } from './components/UserProfileMenu';
import type { Message, Citation, Conversation, UserProfile, SuggestedPrompt } from './data/types';

// Mock user — replace with MSAL auth in production
const mockUser: UserProfile = {
  name: 'Suresh Paulraj',
  email: 'sureshpaulraj@contoso.com',
  role: 'Operations Manager',
  department: 'Warehouse Operations',
};

// Curated prompts based on user role/department
const getPromptsForUser = (user: UserProfile): SuggestedPrompt[] => {
  const basePrompts: SuggestedPrompt[] = [
    { icon: '📋', text: 'Show me all active SOPs' },
    { icon: '🔍', text: 'Search for safety procedures' },
  ];

  const rolePrompts: Record<string, SuggestedPrompt[]> = {
    'Warehouse Operations': [
      { icon: '🏭', text: 'Warehouse spill cleanup procedure' },
      { icon: '🚛', text: 'Forklift operation safety checklist' },
      { icon: '📦', text: 'Inventory receiving SOP' },
      { icon: '⚠️', text: 'Emergency evacuation protocol' },
    ],
    'Quality Assurance': [
      { icon: '🧪', text: 'Quality inspection checklist' },
      { icon: '🌡️', text: 'Cold chain temperature monitoring SOP' },
      { icon: '📊', text: 'Product sampling procedures' },
    ],
    'Distribution': [
      { icon: '🚚', text: 'Delivery route planning SOP' },
      { icon: '❄️', text: 'Cold chain delivery compliance' },
      { icon: '📝', text: 'Driver pre-trip inspection checklist' },
    ],
  };

  return [...basePrompts, ...(rolePrompts[user.department] || [])];
};

export function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [showCitations, setShowCitations] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [user] = useState<UserProfile>(mockUser);

  const suggestedPrompts = getPromptsForUser(user);

  const handleLogout = () => {
    // In production, call MSAL logout
    window.location.href = '/';
  };

  const handleSend = async (query: string) => {
    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, conversation_id: conversationId }),
      });
      const data = await response.json();

      const assistantMsg: Message = {
        id: `msg-${Date.now()}-resp`,
        role: 'assistant',
        content: data.response,
        citations: data.citations,
        timestamp: new Date().toISOString(),
        grounded: data.grounded,
        confidence: data.confidence,
        activity: data.activity,
        followUpPrompts: data.follow_up_prompts,
      };

      setMessages((prev) => {
        const updated = [...prev, assistantMsg];
        // Auto-create conversation entry from first user message
        if (updated.filter(m => m.role === 'user').length === 1) {
          const firstUserMsg = updated.find(m => m.role === 'user');
          const convId = data.conversation_id || `conv-${Date.now()}`;
          setConversations((prevConvs) => {
            // Don't add duplicate
            if (prevConvs.some(c => c.id === convId)) return prevConvs;
            return [{
              id: convId,
              title: firstUserMsg?.content.slice(0, 50) || 'New chat',
              date: new Date().toISOString(),
              messageCount: updated.length,
            }, ...prevConvs];
          });
        } else {
          // Update message count on existing conversation
          setConversations((prevConvs) =>
            prevConvs.map((c, idx) =>
              idx === 0 ? { ...c, messageCount: updated.length } : c
            )
          );
        }
        return updated;
      });
      setActiveCitations(data.citations || []);
      if (data.conversation_id) setConversationId(data.conversation_id);
    } catch (error) {
      const errorMsg: Message = {
        id: `msg-${Date.now()}-err`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    if (messages.length > 0) {
      setConversations((prev) => [
        ...prev,
        {
          id: conversationId || `conv-${Date.now()}`,
          title: messages[0]?.content.slice(0, 50) || 'New chat',
          date: new Date().toISOString(),
          messageCount: messages.length,
        },
      ]);
    }
    setMessages([]);
    setActiveCitations([]);
    setConversationId('');
  };

  const handleFeedback = async (messageId: string, rating: 'up' | 'down') => {
    try {
      await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, rating }),
      });
    } catch {
      // Silently handle feedback errors
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Header */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: 'var(--header-height)',
          background: 'var(--contoso-dark)',
          color: 'var(--contoso-white)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: 'var(--contoso-red)', fontWeight: 700, fontSize: '18px' }}>
            Contoso
          </span>
          <span style={{ fontSize: '16px', fontWeight: 500 }}>SOP Assistant</span>
        </div>
        <UserProfileMenu user={user} onLogout={handleLogout} />
      </div>

      {/* Sidebar */}
      <ConversationHistory
        conversations={conversations}
        onNewChat={handleNewChat}
        onSelectConversation={() => {}}
      />

      {/* Chat Area */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSend={handleSend}
        onFeedback={handleFeedback}
        suggestedPrompts={suggestedPrompts}
        onCitationClick={(citations) => {
          setActiveCitations(citations);
          setShowCitations(true);
        }}
      />

      {/* Citation Panel */}
      {showCitations && (
        <CitationPanel
          citations={activeCitations}
          onClose={() => setShowCitations(false)}
        />
      )}
    </div>
  );
}
