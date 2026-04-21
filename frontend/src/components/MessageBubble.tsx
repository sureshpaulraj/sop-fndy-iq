import { useState } from 'react';
import { FeedbackWidget } from './FeedbackWidget';
import type { Message, Citation, ActivityStep, ReasoningNode } from '../data/types';

interface MessageBubbleProps {
  message: Message;
  onFeedback: (messageId: string, rating: 'up' | 'down') => void;
  onCitationClick: (citations: Citation[]) => void;
  onFollowUp?: (prompt: string) => void;
}

function ReasoningTree({ nodes }: { nodes: ReasoningNode[] }) {
  return (
    <div style={{ marginTop: '6px', marginLeft: '4px' }}>
      {nodes.map((node, i) => (
        <ReasoningTreeNode key={i} node={node} isLast={i === nodes.length - 1} />
      ))}
    </div>
  );
}

function ReasoningTreeNode({ node, isLast }: { node: ReasoningNode; isLast: boolean }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div style={{ position: 'relative' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '6px',
          padding: '3px 0',
          cursor: hasChildren ? 'pointer' : 'default',
        }}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        <span style={{ color: 'var(--contoso-gray-400)', fontSize: '11px', minWidth: '14px', userSelect: 'none' }}>
          {hasChildren ? (expanded ? '▼' : '▶') : isLast ? '└' : '├'}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--contoso-gray-700)', lineHeight: '18px' }}>
          {node.label}
        </span>
      </div>
      {hasChildren && expanded && (
        <div style={{ marginLeft: '16px', borderLeft: '1px dashed var(--contoso-gray-300)', paddingLeft: '8px' }}>
          {node.children!.map((child, i) => (
            <ReasoningTreeNode key={i} node={child} isLast={i === node.children!.length - 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function ThoughtProcess({ activity }: { activity: ActivityStep[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!activity || activity.length === 0) return null;

  const totalMs = activity.reduce((sum, a) => sum + (a.duration_ms || 0), 0);

  return (
    <div style={{ marginTop: '8px' }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '12px',
          color: 'var(--contoso-blue)',
          cursor: 'pointer',
          padding: '2px 6px',
          borderRadius: '4px',
          background: 'transparent',
          border: 'none',
          fontWeight: 500,
        }}
      >
        🧠 {expanded ? 'Hide' : 'Show'} thought process
        {totalMs > 0 && <span style={{ color: 'var(--contoso-gray-500)' }}>({(totalMs / 1000).toFixed(1)}s)</span>}
      </button>
      {expanded && (
        <div
          style={{
            marginTop: '6px',
            padding: '8px 12px',
            background: 'var(--contoso-gray-100)',
            borderRadius: '6px',
            borderLeft: '3px solid var(--contoso-blue)',
            fontSize: '12px',
            lineHeight: '20px',
          }}
        >
          {activity.map((step, i) => (
            <div key={i} style={{ padding: '2px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontWeight: 600, minWidth: '16px' }}>
                  {step.step === 'Query Planning' ? '📝' : step.step === 'SharePoint Search' || step.step === 'Document Search' ? '🔍' : step.step === 'AI Reasoning' ? '🧠' : step.step === 'Answer Synthesis' ? '✨' : '📋'}
                </span>
                <span style={{ color: 'var(--contoso-gray-700)' }}>
                  <strong>{step.step}</strong>: {step.detail}
                </span>
                {step.duration_ms ? (
                  <span style={{ color: 'var(--contoso-gray-400)', fontSize: '11px', marginLeft: 'auto', flexShrink: 0 }}>
                    {step.duration_ms}ms
                  </span>
                ) : null}
              </div>
              {step.reasoning_tree && step.reasoning_tree.length > 0 && (
                <div style={{
                  marginLeft: '22px',
                  marginTop: '4px',
                  padding: '6px 10px',
                  background: 'white',
                  borderRadius: '6px',
                  border: '1px solid var(--contoso-gray-200)',
                }}>
                  <ReasoningTree nodes={step.reasoning_tree} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FollowUpPrompts({ prompts, onSelect }: { prompts: string[]; onSelect: (p: string) => void }) {
  if (!prompts || prompts.length === 0) return null;
  return (
    <div style={{ marginTop: '10px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
      {prompts.map((p, i) => (
        <button
          key={i}
          onClick={() => onSelect(p)}
          style={{
            fontSize: '12px',
            padding: '4px 10px',
            borderRadius: '12px',
            background: 'var(--contoso-gray-100)',
            border: '1px solid var(--contoso-gray-300)',
            color: 'var(--contoso-dark)',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--contoso-red)';
            e.currentTarget.style.background = '#FEF2F2';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--contoso-gray-300)';
            e.currentTarget.style.background = 'var(--contoso-gray-100)';
          }}
        >
          {p}
        </button>
      ))}
    </div>
  );
}

export function MessageBubble({ message, onFeedback, onCitationClick, onFollowUp }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        maxWidth: '800px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          padding: '12px 16px',
          borderRadius: isUser ? '12px 12px 0 12px' : '12px 12px 12px 0',
          background: isUser ? 'var(--contoso-red)' : 'var(--contoso-white)',
          color: isUser ? 'var(--contoso-white)' : 'var(--contoso-dark)',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          fontSize: '15px',
          lineHeight: '24px',
        }}
      >
        {/* Message content */}
        <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>

        {/* Citation badges — clickable links to source documents */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div style={{ marginTop: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {message.citations.map((c) => (
              <a
                key={c.index}
                href={c.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  if (!c.url) {
                    e.preventDefault();
                    onCitationClick(message.citations!);
                  }
                }}
                style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: 'var(--contoso-blue-light, #EFF6FF)',
                  color: 'var(--contoso-blue)',
                  fontSize: '12px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  border: '1px solid var(--contoso-blue)',
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '3px',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#DBEAFE';
                  e.currentTarget.style.borderColor = 'var(--contoso-red)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--contoso-blue-light, #EFF6FF)';
                  e.currentTarget.style.borderColor = 'var(--contoso-blue)';
                }}
                aria-label={`Open ${c.source}: ${c.title}`}
                title={c.url ? `Open ${c.title} in SharePoint` : `View citation ${c.index}`}
              >
                [{c.index}] {c.source} {c.url ? '↗' : ''}
              </a>
            ))}
          </div>
        )}

        {/* Thought process */}
        {!isUser && message.activity && <ThoughtProcess activity={message.activity} />}

        {/* Follow-up prompts */}
        {!isUser && message.followUpPrompts && onFollowUp && (
          <FollowUpPrompts prompts={message.followUpPrompts} onSelect={onFollowUp} />
        )}

        {/* Feedback */}
        {!isUser && (
          <FeedbackWidget messageId={message.id} onFeedback={onFeedback} />
        )}

        {/* Timestamp */}
        <div
          style={{
            fontSize: '11px',
            color: isUser ? 'rgba(255,255,255,0.7)' : 'var(--contoso-gray-500)',
            marginTop: '4px',
          }}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}
