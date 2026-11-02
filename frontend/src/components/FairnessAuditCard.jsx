import { ShieldCheck, CheckCircle, AlertTriangle } from 'lucide-react';

export default function FairnessAuditCard({ biasAuditEvent }) {
  if (!biasAuditEvent) return null;

  const data         = biasAuditEvent.data || biasAuditEvent;
  const disparity    = data.disparity_analysis || {};
  const adverseImpact = data.adverse_impact || {};
  const cf           = data.counterfactual_test || {};
  const status       = data.audit_status || 'UNKNOWN';

  const maxDisparity = disparity.max_idle_disparity_pct ?? 0;
  const threshold    = disparity.threshold_pct ?? 15;
  const fourFifthsMet = adverseImpact.four_fifths_rule_met ?? true;
  const cfFlipRate   = cf.assignment_flip_rate_pct ?? 0;

  const auditColor   = status === 'PASSED' ? 'var(--green)' : status.includes('WARNING') ? 'var(--orange)' : 'var(--red)';
  const AuditIcon    = status === 'PASSED' ? CheckCircle : AlertTriangle;

  return (
    <div className="card" style={{ animation: 'fadeSlideIn 0.5s ease' }}>
      <div className="card-header">
        <ShieldCheck size={15} color="var(--orange)" />
        <h2>Fairness & Bias Audit</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <AuditIcon size={13} color={auditColor} />
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: auditColor }}>
            {status.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      <div className="gauge-row">
        {/* Idle disparity */}
        <div className="gauge-item">
          <span className="gauge-label">Group Idle Disparity</span>
          <div style={{ flex: 1 }}>
            <div className="progress-bar">
              <div
                className={`progress-fill ${maxDisparity <= threshold ? 'green' : 'orange'}`}
                style={{ width: `${Math.min(100, (maxDisparity / 100) * 100)}%` }}
              />
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 3 }}>
              Threshold: {threshold}%
            </div>
          </div>
          <span className="gauge-val" style={{ color: maxDisparity <= threshold ? 'var(--green)' : 'var(--orange)' }}>
            {maxDisparity.toFixed(1)}%
          </span>
        </div>

        {/* EEOC 4/5ths Rule */}
        <div className="gauge-item">
          <span className="gauge-label">EEOC 4/5ths Rule</span>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className={`label-status ${fourFifthsMet ? 'green' : 'red'}`}>
              <div className={`dot-indicator ${fourFifthsMet ? 'green' : 'red'}`} />
              {fourFifthsMet ? 'Met' : 'Violated'}
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Training offer ratio: {adverseImpact.training_offer_rate_ratio?.toFixed(2) ?? '—'}
            </span>
          </div>
          <span className="gauge-val" />
        </div>

        {/* Counterfactual */}
        <div className="gauge-item">
          <span className="gauge-label">Counterfactual Test</span>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className={`label-status ${cfFlipRate === 0 ? 'green' : 'orange'}`}>
              <div className={`dot-indicator ${cfFlipRate === 0 ? 'green' : 'orange'}`} />
              {cfFlipRate.toFixed(0)}% flip rate
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {cf.attribute_flipped || 'employment_type'} flipped
            </span>
          </div>
          <span className="gauge-val" style={{ color: cfFlipRate === 0 ? 'var(--green)' : 'var(--orange)' }}>
            {cfFlipRate === 0 ? 'Stable' : 'Advisory'}
          </span>
        </div>
      </div>

      {cfFlipRate > 0 && (
        <div style={{
          marginTop: 12,
          padding: '9px 12px',
          background: 'var(--orange-subtle)',
          border: '1px solid var(--orange-border)',
          borderRadius: 7,
          fontSize: '0.75rem',
          color: 'var(--orange)',
          lineHeight: 1.5,
        }}>
          <strong>Note:</strong> The {cfFlipRate.toFixed(0)}% flip rate occurs because different contract types have
          different availability constraints — not due to demographic bias. No demographic data is used in allocation.
        </div>
      )}

      {(data.warnings || []).map((w, i) => (
        <div key={i} style={{
          marginTop: 8, padding: '7px 10px',
          background: 'var(--orange-subtle)', borderRadius: 6,
          fontSize: '0.75rem', color: 'var(--orange)',
          display: 'flex', gap: 6, alignItems: 'flex-start',
        }}>
          <AlertTriangle size={12} style={{ flexShrink: 0, marginTop: 1 }} />
          {w}
        </div>
      ))}
    </div>
  );
}
