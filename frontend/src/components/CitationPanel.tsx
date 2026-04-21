import type { Citation } from '../data/types';

interface CitationPanelProps {
  citations: Citation[];
  onClose: () => void;
}

export function CitationPanel({ citations, onClose }: CitationPanelProps) {
  if (citations.length === 0) return null;

  return (
    <div
      style={{
        width: 'var(--citation-panel-width)',
        marginTop: 'var(--header-height)',
        borderLeft: '1px solid var(--contoso-gray-200)',
        background: 'var(--contoso-white)',
        overflow: 'auto',
        padding: '16px',
        flexShrink: 0,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
        }}
      >
        <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Sources</h3>
        <button
          onClick={onClose}
          aria-label="Close citations panel"
          style={{ fontSize: '18px', color: 'var(--contoso-gray-500)', cursor: 'pointer' }}
        >
          ✕
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {citations.map((c) => (
          <div
            key={c.index}
            style={{
              padding: '12px',
              borderRadius: '8px',
              border: '1px solid var(--contoso-gray-200)',
              background: 'var(--contoso-gray-100)',
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--contoso-blue)')}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--contoso-gray-200)')}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '4px',
              }}
            >
              <span
                style={{
                  background: 'var(--contoso-blue)',
                  color: 'white',
                  borderRadius: '4px',
                  padding: '1px 6px',
                  fontSize: '11px',
                  fontWeight: 600,
                  minWidth: '20px',
                  textAlign: 'center',
                }}
              >
                {c.index}
              </span>
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--contoso-dark)' }}>
                {c.source}
              </span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--contoso-gray-700)', marginTop: '2px' }}>
              {c.title}
            </div>
            {c.snippet && (
              <div
                style={{
                  fontSize: '12px',
                  color: 'var(--contoso-gray-500)',
                  marginTop: '6px',
                  fontStyle: 'italic',
                  lineHeight: '18px',
                  maxHeight: '54px',
                  overflow: 'hidden',
                }}
              >
                {c.snippet}
              </div>
            )}
            {c.page && (
              <div style={{ fontSize: '12px', color: 'var(--contoso-gray-500)', marginTop: '4px' }}>
                📄 Page {c.page}
              </div>
            )}
            {c.url && (
              <a
                href={c.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginTop: '8px',
                  fontSize: '12px',
                  color: 'white',
                  fontWeight: 600,
                  textDecoration: 'none',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  background: 'var(--contoso-blue)',
                  transition: 'background 0.2s',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--contoso-red)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--contoso-blue)')}
              >
                📂 Open Source Document ↗
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
