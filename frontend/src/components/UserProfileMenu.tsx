import { useState, useRef, useEffect } from 'react';
import type { UserProfile } from '../data/types';

interface UserProfileMenuProps {
  user: UserProfile;
  onLogout: () => void;
}

export function UserProfileMenu({ user, onLogout }: UserProfileMenuProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div ref={menuRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        aria-label="User profile menu"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          padding: '4px 8px',
          borderRadius: '8px',
          transition: 'background 0.2s',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
      >
        {user.avatar ? (
          <img
            src={user.avatar}
            alt={user.name}
            style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover' }}
          />
        ) : (
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: 'var(--contoso-red)',
              color: 'var(--contoso-white)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '13px',
              fontWeight: 700,
            }}
          >
            {initials}
          </div>
        )}
        <span style={{ color: 'var(--contoso-white)', fontSize: '13px', fontWeight: 500 }}>
          {user.name.split(' ')[0]}
        </span>
        <span style={{ color: 'var(--contoso-gray-300)', fontSize: '12px' }}>▼</span>
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: '4px',
            background: 'var(--contoso-white)',
            borderRadius: '8px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
            minWidth: '220px',
            zIndex: 200,
            overflow: 'hidden',
          }}
        >
          {/* Profile info */}
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--contoso-gray-200)' }}>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--contoso-dark)' }}>
              {user.name}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--contoso-gray-500)', marginTop: '2px' }}>
              {user.email}
            </div>
            <div
              style={{
                fontSize: '11px',
                color: 'var(--contoso-white)',
                background: 'var(--contoso-red)',
                display: 'inline-block',
                padding: '2px 8px',
                borderRadius: '10px',
                marginTop: '6px',
                fontWeight: 500,
              }}
            >
              {user.role}
            </div>
          </div>

          {/* Department */}
          <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--contoso-gray-200)' }}>
            <div style={{ fontSize: '11px', color: 'var(--contoso-gray-500)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Department
            </div>
            <div style={{ fontSize: '13px', color: 'var(--contoso-dark)', marginTop: '2px' }}>
              {user.department}
            </div>
          </div>

          {/* Logout button */}
          <button
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            style={{
              width: '100%',
              padding: '10px 16px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '13px',
              color: 'var(--contoso-red)',
              fontWeight: 500,
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--contoso-gray-100)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <span style={{ fontSize: '16px' }}>🚪</span>
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
