import { BarChart2, CheckCircle, AlertTriangle, Award } from 'lucide-react';

export default function PlanComparisonTable({ pipelineData, onApprove }) {
  if (!pipelineData?.plan_ids) return null;

  const plans = pipelineData.plans || [];

  return (
    <div className="card" style={{ animation: 'fadeSlideIn 0.5s ease' }}>
      <div className="card-header">
        <BarChart2 size={15} color="var(--accent)" />
        <h2>3-Strategy Allocation Comparison</h2>
        <div style={{ marginLeft: 'auto' }}>
          <div className="label-status blue" style={{ fontSize: '0.75rem' }}>
            <div className="dot-indicator blue" />
            OR-Tools CP-SAT · All assignments verified
          </div>
        </div>
      </div>

      <div className="plan-grid">
        <PlanCol
          label="Plan A — Supervisor Baseline"
          desc="Manual seniority ranking. No training. No fairness balancing."
          tag="Baseline"
          plan={plans.find((p) => p.strategy === 'SUPERVISOR_BASELINE')}
          quality="bad"
        />
        <PlanCol
          label="Plan B — Cost Focused"
          desc="Minimises training spend first. No fairness constraint."
          tag="Cost-Only"
          plan={plans.find((p) => p.strategy === 'COST_FOCUSED')}
          quality="warn"
        />
        <PlanCol
          label="Plan C — ShiftSure Balanced"
          desc="Fairness-weighted CP-SAT solver. Equitable idle distribution across all contract types."
          tag="Recommended"
          plan={plans.find((p) => p.strategy === 'FAIRNESS_BALANCED')}
          quality="good"
          recommended
          planId={Object.values(pipelineData.plan_ids || {}).find((id) => id?.includes('FAIR'))}
          onApprove={onApprove}
        />
      </div>
    </div>
  );
}

function PlanCol({ label, desc, tag, plan, quality, recommended, planId, onApprove }) {
  const m = plan?.metrics || {};
  const status    = plan?.solver_status || '—';
  const fillRate  = m.internal_fill_rate_pct ?? m.task_coverage_pct ?? 0;
  const idleSaved = m.idle_hours_avoided ?? m.total_idle_hours_avoided ?? 0;
  const workers   = m.total_workers ?? 0;
  const training  = m.workers_needing_training ?? 0;
  const savings   = m.external_hiring_avoidance_inr ?? 0;
  const trainCost = m.training_investment_inr ?? m.net_training_investment_inr ?? 0;
  const fillColor = fillRate >= 50 ? 'good' : fillRate >= 25 ? 'warn' : 'bad';

  return (
    <div className={`plan-card ${recommended ? 'recommended' : ''}`}>
      {/* Plan label row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div className="plan-meta-label">{label}</div>
          <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{desc}</p>
        </div>
        {recommended && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--accent)', fontSize: '0.72rem', fontWeight: 700, flexShrink: 0, marginLeft: 8 }}>
            <Award size={12} />
            {tag}
          </div>
        )}
        {!recommended && (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', fontWeight: 600, flexShrink: 0, marginLeft: 8 }}>{tag}</div>
        )}
      </div>

      {/* Solver status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
        {status === 'OPTIMAL' ? (
          <div className="label-status green" style={{ fontSize: '0.73rem' }}>
            <div className="dot-indicator green" />
            Solver: Optimal
          </div>
        ) : (
          <div className="label-status orange" style={{ fontSize: '0.73rem' }}>
            <div className="dot-indicator orange" />
            Solver: {status}
          </div>
        )}
      </div>

      {!plan && (
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', padding: '20px 0', textAlign: 'center' }}>
          Run agents to generate plan
        </p>
      )}

      {plan && (
        <>
          {/* Fill rate progress */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>Task Fill Rate</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.9rem',
                color: fillRate >= 50 ? 'var(--green)' : fillRate >= 25 ? 'var(--orange)' : 'var(--red)' }}>
                {fillRate.toFixed(1)}%
              </span>
            </div>
            <div className="progress-bar">
              <div className={`progress-fill ${fillColor}`} style={{ width: `${Math.min(100, fillRate)}%` }} />
            </div>
          </div>

          <div className="plan-metric"><span className="m-label">Idle Hours Saved</span>
            <span className={`m-value ${idleSaved > 50 ? 'good' : 'warn'}`}>{idleSaved.toFixed(0)} hrs</span>
          </div>
          <div className="plan-metric"><span className="m-label">Workers Matched</span>
            <span className="m-value">{workers}</span>
          </div>
          <div className="plan-metric"><span className="m-label">Needing Training</span>
            <span className={`m-value ${training > 0 ? 'warn' : ''}`}>{training}</span>
          </div>
          <div className="plan-metric"><span className="m-label">Training Investment</span>
            <span className="m-value">₹{trainCost.toLocaleString()}</span>
          </div>
          <div className="plan-metric"><span className="m-label">Hiring Avoidance</span>
            <span className="m-value good">₹{savings.toLocaleString()}</span>
          </div>
        </>
      )}

      {recommended && planId && onApprove && (
        <button
          className="btn btn-primary"
          style={{ width: '100%', marginTop: 14, justifyContent: 'center' }}
          onClick={() => onApprove(planId)}
        >
          <CheckCircle size={14} />
          Manager Approve Plan C
        </button>
      )}
    </div>
  );
}
