interface GDPRBannerProps {
  onAccept: () => void;
}

export function GDPRBanner({ onAccept }: GDPRBannerProps) {
  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      padding: '12px 20px',
      borderRadius: '8px',
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.3)',
      display: 'flex',
      alignItems: 'center',
      gap: '15px',
      zIndex: 1000,
      maxWidth: '90%',
      width: 'auto'
    }}>
      <span style={{ 
        color: 'white', 
        fontSize: '14px'
      }}>
        We use cookies to enhance your browsing experience
      </span>
      <button
        onClick={onAccept}
        style={{
          backgroundColor: '#4A4A4A',
          color: 'white',
          border: 'none',
          padding: '8px 15px',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '13px',
          whiteSpace: 'nowrap'
        }}
        onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5A5A5A'}
        onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#4A4A4A'}
      >
        Accept
      </button>
    </div>
  );
} 