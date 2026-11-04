import { Cpu, Database, ShieldCheck, Scale, BookOpen, Lock, Layers } from 'lucide-react';

const AGENTS = [
  { step: '01', name: 'Skills Discovery Agent',       sap: 'SAP SuccessFactors Skills Ontology',      role: 'Extracts verified skills and adjacent competencies from unstructured tenure logs, machine operating records, and past certifications.' },
  { step: '02', name: 'Market Intelligence Agent',    sap: 'Industry Labor Benchmark Indices',         role: 'Scans external manufacturing labor demand signals and maps internal vacant shift requirements across adjacent production lines.' },
  { step: '03', name: 'Learning Pathway Agent',       sap: 'SAP Learning Hub (Student Edition)',       role: 'Computes skill deltas and matches workers to targeted micro-credential bridge courses with explicit hour commitments and employer cost.' },
  { step: '04', name: 'Inclusive Matching Agent',     sap: 'CP-SAT Deterministic Optimization',        role: 'Runs Google OR-Tools CP-SAT constraint programming. Evaluates thousands of candidate allocations to balance task coverage and idle hour equity.' },
  { step: '05', name: 'Employer Readiness Agent',     sap: 'SAP S/4HANA Manufacturing Operations',    role: 'Validates line transition feasibility, workstation safety clearances, supervisor capacity, and ROI on training investments.' },
  { step: '06', name: 'Bias Audit Agent',            sap: 'Algorithmic Fairness & Audit Trail',       role: 'Runs automated Counterfactual Testing and verifies compliance with the EEOC 4/5ths Adverse Impact Rule before any plan is surfaced.' },
  { step: '07', name: 'Human-in-the-Loop Safeguard', sap: 'SAP SuccessFactors Audit Trail',           role: 'Enforces GDPR Article 22 compliance. Drafts transparent worker notices, opens 24-hour review windows, and commits immutable audit logs.' },
];

export default function ArchitecturePage() {
  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.7rem', marginBottom: 6 }}>
          System Architecture & AI Governance
        </h1>
        <p style={{ fontSize: '0.88rem', maxWidth: 720 }}>
          ShiftSure combines autonomous language model agents with a deterministic constraint solver to produce explainable, bias-audited workforce mobility decisions inside the SAP enterprise ecosystem.
        </p>
      </div>

      {/* Dual Engine */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <Layers size={15} color="var(--accent)" />
          <h2>The Dual-Engine Paradigm</h2>
        </div>
        <p style={{ marginBottom: 16, fontSize: '0.85rem' }}>
          ShiftSure deliberately separates <strong>qualitative reasoning</strong> (LLM) from <strong>deterministic decision-making</strong> (OR-Tools CP-SAT).
          This means the AI explains context and generates insights, while the solver makes allocation decisions with mathematical optimality guarantees.
        </p>
        <div className="grid-2">
          <div style={{ padding: '16px 18px', background: 'var(--accent-subtle)', border: '1px solid var(--accent-border)', borderRadius: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Cpu size={16} color="var(--accent)" />
              <h3 style={{ color: 'var(--accent)' }}>Engine A — LLM Cognitive Layer</h3>
            </div>
            <p style={{ fontSize: '0.8rem' }}>
              Used for extracting tacit competencies from unstructured text, generating human-readable reasoning narratives, and synthesizing cross-agent context.
            </p>
            <div style={{ marginTop: 10, fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Natural language understanding · Context synthesis · Explanation generation
            </div>
          </div>
          <div style={{ padding: '16px 18px', background: 'var(--green-subtle)', border: '1px solid var(--green-border)', borderRadius: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Scale size={16} color="var(--green)" />
              <h3 style={{ color: 'var(--green)' }}>Engine B — Google OR-Tools CP-SAT</h3>
            </div>
            <p style={{ fontSize: '0.8rem' }}>
              All shift assignment decisions are made by this deterministic constraint solver. Guaranteed zero hallucinations, 100% shift law compliance, and mathematical idle-hour equity across contract types.
            </p>
            <div style={{ marginTop: 10, fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Deterministic constraint satisfaction · Verifiable optimality bounds · Zero hallucinated shifts
            </div>
          </div>
        </div>
      </div>

      {/* 7-Agent Pipeline */}
      <div style={{ marginBottom: 24 }}>
        <div className="section-header">
          <h2>Sequential 7-Agent Pipeline</h2>
          <div className="label-status muted" style={{ fontSize: '0.75rem' }}>Asynchronous SSE event stream</div>
        </div>
        <div className="agent-flow-grid">
          {AGENTS.map((agent, i) => (
            <div key={agent.step} className="agent-arch-card" style={{ animationDelay: `${i * 0.07}s` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span className="agent-step-num">Agent {agent.step}</span>
                <span style={{ fontSize: '0.67rem', color: 'var(--accent)', fontWeight: 500 }}>{agent.sap}</span>
              </div>
              <h4 style={{ color: 'var(--text-primary)', fontSize: '0.88rem', marginBottom: 6 }}>{agent.name}</h4>
              <p style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>{agent.role}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Ethical Framework */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <ShieldCheck size={15} color="var(--orange)" />
          <h2>Ethical AI Framework & Audit Guarantees</h2>
        </div>
        <div className="grid-3">
          {[
            {
              title: 'EEOC 4/5ths Rule',
              body: "Automatically calculates selection and training offer rates across worker categories. If any cohort's selection rate falls below 80% of the highest group, the plan triggers a compliance warning and human review.",
            },
            {
              title: 'Counterfactual Testing',
              body: "The system programmatically flips non-job-relevant attributes (e.g., contract type) and re-solves. The assignment flip rate is recorded in the audit log to guarantee all decisions are strictly competence-driven.",
            },
            {
              title: 'GDPR Article 22 Safeguard',
              body: "No automated decision is final without explicit human oversight. A 24-hour review window is mandated for every plant supervisor, with a built-in right-to-appeal interface for every affected worker.",
            },
          ].map(({ title, body }) => (
            <div key={title} style={{ padding: '16px 18px', background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 10, animation: 'fadeSlideIn 0.5s ease' }}>
              <h4 style={{ color: 'var(--text-primary)', fontSize: '0.88rem', marginBottom: 8, fontFamily: 'var(--font-display)' }}>{title}</h4>
              <p style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>{body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* SAP Integration */}
      <div>
        <div className="section-header">
          <h2>SAP Ecosystem Integration</h2>
        </div>
        <div className="sap-integration-grid">
          {[
            { Icon: Database, color: 'var(--accent)', title: 'SAP SuccessFactors', badge: 'Conceptual', body: 'Future mapping target for employee profiles, skills, and internal opportunity records. No live SuccessFactors connection is configured in this prototype.' },
            { Icon: BookOpen, color: 'var(--green)',  title: 'SAP Learning Hub',   badge: 'Simulated', body: 'Learning pathways are represented in the prototype. Course suggestions and enrollment are not connected to SAP Learning Hub.' },
            { Icon: Lock,     color: 'var(--orange)', title: 'SAP S/4HANA Mfg',   badge: 'BAPI / RFC Event Sync', body: 'Feeds optimal shift rosters and worker qualification flags into Production Planning (PP) and Plant Maintenance (PM) work centers.' },
          ].map(({ Icon, color, title, badge, body }) => (
            <div key={title} className="sap-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Icon size={16} color={color} />
                <h3 style={{ fontSize: '0.9rem' }}>{title}</h3>
              </div>
              <p style={{ fontSize: '0.78rem', lineHeight: 1.5, marginBottom: 10 }}>{body}</p>
              <div className="label-status muted" style={{ fontSize: '0.72rem' }}>
                <div className="dot-indicator blue" />
                {badge}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
