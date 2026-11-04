import { AlertTriangle, Factory } from 'lucide-react';

export default function Header({ activeTab, onTabChange, systemStatus }) {
  const isOnline = systemStatus?.status === 'online';
  const agentsReady = systemStatus?.agents_ready ?? 7;

  return (
    <header className="app-header">
      {/* Logo */}
      <button className="logo" onClick={() => onTabChange('overview')} aria-label="ShiftSure home">
        <div className="logo-mark">S</div>
        <div>
          <div className="logo-name">ShiftSure</div>
        </div>
        <div className="logo-by">WORKFORCE RESILIENCE</div>
      </button>

      <div className="header-divider" />

      {/* Plant badge */}
      <div className="plant-chip">
        <Factory size={14} />
        <div className="plant-chip-dot" />
        Plant 01 · Bengaluru
      </div>

      <div className="header-spacer" />

      {/* Status */}
      <div className="status-indicator">
        {isOnline ? (
          <>
            <div className="status-dot" />
            Backend connected · {agentsReady} agents ready
          </>
        ) : (
          <>
            <AlertTriangle size={13} color="var(--orange)" />
            <span style={{ color: 'var(--orange)' }}>Backend status unavailable</span>
          </>
        )}
      </div>
      <div className="integration-status" aria-label="Integration status">
        <span className="integration-label live"><i />Live · BTP / GenAI Hub</span>
        <span className="integration-label simulated"><i />Simulated · Learning Hub</span>
        <span className="integration-label conceptual"><i />Conceptual · SuccessFactors</span>
      </div>
    </header>
  );
}
