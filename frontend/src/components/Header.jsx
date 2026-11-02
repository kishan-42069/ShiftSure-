import { AlertTriangle } from 'lucide-react';

export default function Header({ activeTab, onTabChange, systemStatus }) {
  const isOnline = systemStatus?.status === 'online';
  const agentsReady = systemStatus?.agents_ready ?? 7;

  return (
    <header className="app-header">
      {/* Logo */}
      <div className="logo" onClick={() => onTabChange('overview')}>
        <div className="logo-mark">SS</div>
        <div>
          <div className="logo-name">ShiftSure</div>
        </div>
        <div className="logo-by">by SAP</div>
      </div>

      <div className="header-divider" />

      {/* Plant badge */}
      <div className="plant-chip">
        <div className="plant-chip-dot" />
        Pune Smart Manufacturing Hub · Plant #4
      </div>

      <div className="header-spacer" />

      {/* Status */}
      <div className="status-indicator">
        {isOnline ? (
          <>
            <div className="status-dot" />
            Backend online · {agentsReady} agents ready
          </>
        ) : (
          <>
            <AlertTriangle size={13} color="var(--orange)" />
            <span style={{ color: 'var(--orange)' }}>Connecting to backend…</span>
          </>
        )}
      </div>
    </header>
  );
}
