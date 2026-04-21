export function LoadingSkeleton() {
  return (
    <div
      role="status"
      aria-label="Loading response"
      style={{
        display: 'flex',
        justifyContent: 'flex-start',
        maxWidth: '800px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          padding: '16px',
          borderRadius: '12px 12px 12px 0',
          background: 'var(--contoso-white)',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '14px' }}>🤖</span>
          <span style={{ fontSize: '13px', color: 'var(--contoso-gray-500)' }}>
            Thinking...
          </span>
        </div>
        {[200, 280, 160].map((w, i) => (
          <div
            key={i}
            style={{
              height: '12px',
              width: `${w}px`,
              borderRadius: '4px',
              background: 'var(--contoso-gray-200)',
              animation: 'pulse 1.5s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 1; }
          }
        `}</style>
      </div>
    </div>
  );
}
