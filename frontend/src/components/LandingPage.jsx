import { useEffect, useRef } from 'react';
import { ArrowRight, Cpu, Scale, BookOpen, ShieldCheck, Sparkles, Factory } from 'lucide-react';

/* ── Orbital node labels ──────────────────────────────────────────── */
const RING1_NODES = ['SAP\nSuccessFactors', 'SAP\nLearning Hub', 'CP-SAT\nSolver', 'OR-Tools'];
const RING2_NODES = ['S/4HANA\nMfg', 'Skills\nAgents', 'EEOC\nAudit', 'Worker\nPortal'];

/* ── Animated activity feed items ─────────────────────────────────── */
const FEED_ITEMS = [
  { initials: 'PS', name: 'Priya Sharma', action: 'matched to LINE-01 via CP-SAT solver', time: '2 min ago' },
  { initials: 'RA', name: 'Rohan Anand', action: 'enrolled in Robotics Safety L1 — SAP Learning Hub', time: '4 min ago' },
  { initials: 'KM', name: 'Kavita More', action: 'bias audit passed — 4/5ths Rule verified', time: '6 min ago' },
  { initials: 'VP', name: 'Vijay Patil', action: 'redeployment notice issued — 24hr review open', time: '9 min ago' },
];

export default function LandingPage({ onNavigateToManager, onQuickStartDemo }) {
  const feedRef = useRef(null);

  /* ── Staggered fade-in for feed items ─── */
  useEffect(() => {
    const items = feedRef.current?.querySelectorAll('.activity-item');
    items?.forEach((el, i) => {
      el.style.animationDelay = `${0.9 + i * 0.15}s`;
    });
  }, []);

  return (
    <div className="landing-root">
      {/* ═══════════════════ HERO SECTION ═══════════════════ */}
      <section style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="landing-hero-wrap">
          {/* Eyebrow */}
          <div className="hero-eyebrow">SAP Smart Manufacturing · Workforce Intelligence Platform</div>

          {/* Headline */}
          <h1 className="hero-headline">
            When Automation Arrives,<br />
            <em>No Worker Gets Left Behind.</em>
          </h1>

          {/* Sub-headline */}
          <p className="hero-subhead">
            ShiftSure pairs autonomous AI agents with Google OR-Tools' deterministic CP-SAT solver to turn manufacturing disruptions into equitable workforce opportunities — inside the SAP enterprise ecosystem.
          </p>

          {/* CTA Buttons */}
          <div className="hero-cta-row">
            <button
              className="btn btn-primary"
              style={{ padding: '11px 24px', fontSize: '0.9rem', fontWeight: 600 }}
              onClick={onNavigateToManager}
            >
              Launch Control Center
              <ArrowRight size={16} />
            </button>

            <button
              className="btn btn-secondary"
              style={{ padding: '11px 22px', fontSize: '0.9rem' }}
              onClick={onQuickStartDemo}
            >
              <Sparkles size={15} color="var(--accent)" />
              Quick-Start: Line 3 Demo
            </button>
          </div>

          {/* ── Orbital + Activity Feed row ── */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 48, justifyContent: 'center', flexWrap: 'wrap' }}>
            {/* Orbital System */}
            <div className="orbital-system">
              {/* Ring 1 */}
              <div className="orbital-ring orbital-ring-1">
                {RING1_NODES.map((label, i) => (
                  <div
                    key={i}
                    className="orbital-node"
                    style={getNodeStyle(i, 4)}
                  >
                    <span style={{ whiteSpace: 'pre-line', lineHeight: 1.25 }}>{label}</span>
                  </div>
                ))}
              </div>

              {/* Ring 2 */}
              <div className="orbital-ring orbital-ring-2">
                {RING2_NODES.map((label, i) => (
                  <div
                    key={i}
                    className="orbital-node"
                    style={getNodeStyle(i, 4)}
                  >
                    <span style={{ whiteSpace: 'pre-line', lineHeight: 1.25 }}>{label}</span>
                  </div>
                ))}
              </div>

              {/* Center hub */}
              <div className="orbital-center">
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                  <Cpu size={18} color="#fff" />
                </div>
                <span style={{ fontSize: '0.62rem', fontWeight: 700, color: 'var(--text-secondary)', textAlign: 'center', lineHeight: 1.3 }}>
                  ShiftSure<br />Engine
                </span>
              </div>
            </div>

            {/* Activity Feed */}
            <div className="activity-feed" ref={feedRef}>
              <div className="activity-feed-header">
                <div className="dot-indicator green" />
                Live Pipeline Events · Pune Plant #4
              </div>
              {FEED_ITEMS.map((item, i) => (
                <div key={i} className="activity-item anim-fade-up">
                  <div className="activity-avatar">{item.initials}</div>
                  <div>
                    <div className="activity-text">
                      <strong>{item.name}</strong>{' '}
                      <span>{item.action}</span>
                    </div>
                    <div className="activity-time">{item.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ METRICS STRIP ═══════════════════ */}
      <div style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-light)', padding: '0' }}>
        <div className="metrics-strip" style={{ borderRadius: 0, border: 'none', borderTop: '1px solid var(--border-light)', borderBottom: '1px solid var(--border-light)' }}>
          {[
            { value: '180', label: 'Shop Floor Operators\nacross 3 production lines' },
            { value: '45', label: 'Workers facing\nLine 3 Automation Disruption' },
            { value: '₹18.4L', label: 'External hiring avoidance\nvia internal reallocation' },
            { value: '7', label: 'Autonomous AI Agents\norchestrated sequentially' },
          ].map((m, i) => (
            <div key={i} className="metric-block" style={{ animationDelay: `${0.2 + i * 0.1}s` }}>
              <div className="metric-block-value">{m.value}</div>
              <div className="metric-block-label" style={{ whiteSpace: 'pre-line' }}>{m.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ═══════════════════ 4 FEATURE PILLARS ═══════════════════ */}
      <div className="pillars-grid">
        <div style={{ gridColumn: '1 / -1', marginBottom: 4 }}>
          <p style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: 8 }}>
            Why ShiftSure Works
          </p>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.7rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
            Three guarantees most platforms can't make.
          </h2>
        </div>

        {[
          {
            Icon: Cpu, title: 'Multi-Agent Intelligence',
            desc: 'Seven specialized autonomous agents handle skills extraction, market benchmarking, learning pathway design, and constraint solving — coordinated sequentially so every downstream agent benefits from richer context.',
            delay: '0.1s',
          },
          {
            Icon: Scale, title: 'Deterministic Zero-Hallucination Allocation',
            desc: "All shift assignments are solved by Google OR-Tools CP-SAT — a proven constraint optimizer. No LLM ever decides who works where. Guaranteed optimality, guaranteed shift law compliance, zero invented assignments.",
            delay: '0.2s',
          },
          {
            Icon: BookOpen, title: 'SAP Learning Hub Bridge Courses',
            desc: "Workers with skill gaps aren't rejected — they're matched to targeted SAP Learning Hub micro-credentials (e.g., Robotics Safety L1) with precise hour commitments and employer investment figures.",
            delay: '0.3s',
          },
          {
            Icon: ShieldCheck, title: 'EEOC & GDPR Audit Trail',
            desc: 'Every plan undergoes automated counterfactual testing and the EEOC 4/5ths Adverse Impact Check. Human review is mandatory, and workers have a built-in right-to-appeal with 24-hour response guarantees.',
            delay: '0.4s',
          },
        ].map(({ Icon, title, desc, delay }, i) => (
          <div key={i} className="pillar-card" style={{ animationDelay: delay }}>
            <div className="pillar-icon"><Icon size={22} /></div>
            <div className="pillar-title">{title}</div>
            <p className="pillar-desc">{desc}</p>
          </div>
        ))}
      </div>

      {/* ═══════════════════ GOVERNANCE BANNER ═══════════════════ */}
      <div className="governance-banner">
        <div className="governance-inner">
          <div className="governance-icon-box"><ShieldCheck size={20} /></div>
          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600, marginBottom: 6 }}>
              Audited under EEOC Uniform Guidelines & GDPR Article 22
            </h3>
            <p style={{ marginBottom: 14 }}>
              Every allocation plan is verified via automated Counterfactual Testing and the EEOC 4/5ths Adverse Impact Rule.
              No decision is finalized without the mandatory Human-in-the-Loop review window. Zero demographic attributes
              are ever used in task matching.
            </p>
            <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
              {['Zero Demographic Attributes Used', '4/5ths Rule Verified', 'Right to Appeal Built-in', 'Audit Log Immutable'].map((text) => (
                <div key={text} className="label-status blue" style={{ fontSize: '0.78rem' }}>
                  <div className="dot-indicator blue" />
                  {text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════ TRUST BAR ═══════════════════ */}
      <div className="trust-bar">
        <div className="trust-bar-label">Integrated with</div>
        <div className="trust-logos">
          {['SAP SuccessFactors', 'SAP S/4HANA', 'SAP Learning Hub', 'Google OR-Tools', 'Gemini AI', 'EEOC Certified'].map((name) => (
            <div key={name} className="trust-logo-item">{name}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Utility: evenly space N nodes around a ring ──────────────────── */
function getNodeStyle(index, total) {
  const angle = (360 / total) * index - 90; // -90 starts from top
  const rad = (angle * Math.PI) / 180;
  const radius = 50; // % from center of ring
  const x = 50 + radius * Math.cos(rad);
  const y = 50 + radius * Math.sin(rad);
  return {
    position: 'absolute',
    left: `calc(${x}% - 25px)`,
    top:  `calc(${y}% - 25px)`,
  };
}
