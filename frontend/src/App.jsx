import { useState, useEffect } from 'react';
import './index.css';
import Header from './components/Header';
import LandingPage from './components/LandingPage';
import ArchitecturePage from './components/ArchitecturePage';
import ScenarioPanel from './components/ScenarioPanel';
import AgentStreamConsole from './components/AgentStreamConsole';
import PlanComparisonTable from './components/PlanComparisonTable';
import FairnessAuditCard from './components/FairnessAuditCard';
import WorkerPortal from './components/WorkerPortal';
import { getHealth, getAgentHealth, approvePlan, createScenario } from './api';
import {
  Home, Sliders, UserCheck, Layers,
  CheckCircle, ChevronRight, LayoutDashboard, Activity,
  ShieldCheck, GitCompare, ArrowRight, Factory, Users,
  Gauge, AlertTriangle, Sparkles
} from 'lucide-react';

/* ── Sidebar navigation items ──────────────────────────────────────── */
const MAIN_NAV = [
  { id: 'overview',      icon: Home,            label: 'Overview' },
  { id: 'scenario',      icon: Sliders,         label: 'Disruption scenario' },
  { id: 'agents',        icon: Activity,        label: 'Live agent stream' },
  { id: 'fairness',      icon: ShieldCheck,     label: 'Fairness & bias' },
  { id: 'strategies',    icon: GitCompare,      label: 'Allocation strategies' },
  { id: 'worker',        icon: UserCheck,        label: 'Worker Portal' },
];
const SECONDARY_NAV = [
  { id: 'architecture',  icon: Layers,           label: 'Architecture & AI' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [systemStatus, setSystemStatus] = useState(null);
  const [activeScenario, setActiveScenario] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [biasAuditEvent, setBiasAuditEvent] = useState(null);
  const [notification, setNotification] = useState(null);
  const [approvalStatus, setApprovalStatus] = useState(null);

  useEffect(() => {
    (async () => {
      const [health, agentHealth] = await Promise.all([getHealth(), getAgentHealth()]);
      const { status: _agentStatus, ...agentHealthRest } = agentHealth;
      setSystemStatus({ ...health, ...agentHealthRest, agents_status: _agentStatus });
    })();
  }, []);

  const handlePipelineComplete = (data) => setPipelineData(data);
  const handleBiasAuditEvent   = (evt) => setBiasAuditEvent(evt);
  const handleNotificationEvent = (evt) => setNotification(evt);

  const handleApprove = async (planId) => {
    try {
      await approvePlan(planId, 'PLANT_MGR_PUNE_4');
      setApprovalStatus('approved');
    } catch { setApprovalStatus('error'); }
  };

  const handleQuickStartDemo = async () => {
    try {
      const scenario = await createScenario({
        name: 'Line 3 Packaging Automation (80% Disruption)',
        affected_line_id: 'LINE-03',
        workload_reduction_pct: 0.80,
        planning_period_hours: 40,
        max_training_hours: 20,
        fairness_weight: 0.35,
        idle_disparity_threshold: 0.15,
      });
      setActiveScenario(scenario);
    } catch {}
    setActiveTab('agents');
  };

  /* ── Landing page has no sidebar ──────────────────────────────────── */
  const isLanding = activeTab === 'overview';

  return (
    <div className={isLanding ? 'app-shell-nosidebar' : 'app-shell'}>
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        systemStatus={systemStatus}
      />

      {/* ── Sidebar (only for app pages) ─────────────────────────────── */}
      {!isLanding && (
        <aside className="sidebar">
          <div className="sidebar-section-label">Main</div>
          {MAIN_NAV.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`sidebar-item ${activeTab === id ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}

          <div className="sidebar-divider" />
          <div className="sidebar-section-label">Docs</div>
          {SECONDARY_NAV.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`sidebar-item ${activeTab === id ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}

          <div className="sidebar-divider" />

          {/* Scenario status in sidebar */}
          {activeScenario && (
            <div style={{
              padding: '10px 12px',
              background: 'var(--accent-subtle)',
              border: '1px solid var(--accent-border)',
              borderRadius: 8,
              margin: '0 0 8px',
            }}>
              <div style={{ fontSize: '0.67rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--accent)', marginBottom: 4 }}>
                Active Scenario
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {activeScenario.name || activeScenario.id}
              </div>
            </div>
          )}

          <div className="sidebar-footer">
            <button
              className="sidebar-item"
              onClick={() => setActiveTab('overview')}
              style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}
            >
              <Home size={13} />
              Back to Landing
            </button>
          </div>
        </aside>
      )}

      {/* ── Main Content ───────────────────────────────────────────────── */}
      <main className="main-content">
        {activeTab === 'overview' && (
          <LandingPage
            onNavigateToManager={() => setActiveTab('scenario')}
            onQuickStartDemo={handleQuickStartDemo}
          />
        )}

        {activeTab === 'scenario' && <ScenarioWorkspace activeScenario={activeScenario} onScenarioCreated={setActiveScenario} onContinue={() => setActiveTab('agents')} />}

        <div className="agent-screen" style={{ display: activeTab === 'agents' ? 'block' : 'none' }}>
          <div className="agent-screen-heading">
            <div><div className="screen-kicker"><Activity size={13}/> DECISION PIPELINE</div><h1>Live agent stream</h1><p>Watch each specialist agent inspect evidence, propose matches, and hand off to the next step.</p></div>
            <div className="agent-live-indicator"><span className="agent-live-pulse"/> REAL-TIME REASONING</div>
          </div>
          {activeScenario && <div className="active-scenario-strip"><Factory size={15}/><span>{activeScenario.name || activeScenario.id}</span><button onClick={() => setActiveTab('scenario')}>Edit scenario</button></div>}
          {!activeScenario && <div className="screen-empty"><div className="screen-empty-icon"><Sliders size={20}/></div><div><b>No disruption scenario yet</b><p>Configure the workload change and affected production line before running agents.</p></div><button className="btn btn-primary" onClick={() => setActiveTab('scenario')}>Set up a scenario <ArrowRight size={14}/></button></div>}
          <AgentStreamConsole scenarioId={activeScenario?.id} onPipelineComplete={handlePipelineComplete} onBiasAuditEvent={handleBiasAuditEvent} onNotificationEvent={handleNotificationEvent}/>
          {pipelineData && <div className="stream-result-link"><CheckCircle size={15}/> Pipeline complete · {pipelineData.total_agents_run ?? 7} agents finished <button onClick={() => setActiveTab('fairness')}>Review fairness results <ArrowRight size={13}/></button></div>}
        </div>

        {activeTab === 'fairness' && <FairnessWorkspace biasAuditEvent={biasAuditEvent} pipelineData={pipelineData} onStrategies={() => setActiveTab('strategies')} />}
        {activeTab === 'strategies' && <StrategyWorkspace pipelineData={pipelineData} onApprove={handleApprove} approvalStatus={approvalStatus} onRun={() => setActiveTab(activeScenario ? 'agents' : 'scenario')} />}

        {activeTab === 'worker' && (
          <WorkerView notification={notification} />
        )}

        {activeTab === 'architecture' && (
          <ArchitecturePage />
        )}
      </main>
    </div>
  );
}

function ScenarioWorkspace({ activeScenario, onScenarioCreated, onContinue }) {
  return <div className="workspace-page scenario-workspace">
    <div className="workspace-page-head"><div><div className="screen-kicker"><Sliders size={13}/> SCENARIO DESIGN</div><h1>Disruption scenario</h1><p>Describe the operational change, then set workforce and training constraints for the planning run.</p></div><div className="step-chip"><span>01</span> CONFIGURE <i/> 02 OPTIMIZE <i/> 03 REVIEW</div></div>
    <div className="scenario-layout"><div className="scenario-form-card"><ScenarioPanel onScenarioCreated={onScenarioCreated} activeScenario={activeScenario}/></div><aside className="scenario-side">
      <div className="scenario-side-card scenario-context"><span className="context-icon"><Factory size={17}/></span><div className="screen-kicker">CURRENT CONTEXT</div><h2>{activeScenario?.name || 'Plant 01 · Line 03'}</h2><p>{activeScenario ? 'Scenario saved and ready for the optimization pipeline.' : 'Model an automation event or operational disruption and estimate the team capacity it releases.'}</p>{activeScenario && <div className="scenario-id">Scenario ID <b>{activeScenario.id}</b></div>}</div>
      <div className="scenario-side-card"><div className="side-title"><Gauge size={16}/> Planning guardrails</div><ul><li>Role eligibility uses job-related skills and availability</li><li>Training time stays within the limit you set</li><li>Fairness weight balances the allocation objective</li><li>A manager reviews every generated plan</li></ul></div>
      <div className="scenario-side-card scenario-next"><div className="side-title"><Sparkles size={16}/> Next step</div><p>{activeScenario ? 'Run the agent pipeline to build and audit allocation options.' : 'Save your scenario to unlock workforce analysis and strategy comparison.'}</p><button className="btn btn-primary" disabled={!activeScenario} onClick={onContinue}>Open live agent stream <ArrowRight size={14}/></button></div>
    </aside></div>
  </div>;
}

function FairnessWorkspace({ biasAuditEvent, pipelineData, onStrategies }) {
  const data = biasAuditEvent?.data || biasAuditEvent || {};
  const disparity = data.disparity_analysis || {};
  const impact = data.adverse_impact || {};
  const counter = data.counterfactual_test || {};
  const status = data.audit_status || pipelineData?.audit_status || 'AWAITING RUN';
  const value = (v, suffix='') => v == null ? '—' : `${v}${suffix}`;
  return <div className="workspace-page fairness-workspace">
    <div className="workspace-page-head"><div><div className="screen-kicker"><ShieldCheck size={13}/> RESPONSIBLE ALLOCATION</div><h1>Fairness &amp; bias dashboard</h1><p>Review disparity indicators and counterfactual checks as signals for human investigation.</p></div><button className="btn btn-secondary" onClick={onStrategies}>Compare 3 strategies <ArrowRight size={14}/></button></div>
    <div className="audit-status-banner"><div className={`audit-status-mark ${status==='PASSED'?'ok':''}`}><ShieldCheck size={21}/></div><div><small>BIAS AUDIT STATUS</small><b>{String(status).replace(/_/g,' ')}</b><span>{biasAuditEvent ? 'Pipeline evidence loaded · review signals with context before approval.' : 'Run the agent pipeline to populate scenario-specific audit evidence.'}</span></div><span className="audit-tag">HUMAN REVIEW REQUIRED</span></div>
    <div className="audit-kpi-grid">
      <div className="audit-kpi"><div className="audit-kpi-label">Idle disparity</div><strong>{value(disparity.max_idle_disparity_pct,'%')}</strong><small>Threshold {value(disparity.threshold_pct,'%')}</small><div className="audit-meter"><i style={{width:`${Math.min(100,Number(disparity.max_idle_disparity_pct||0))}%`}}/></div></div>
      <div className="audit-kpi"><div className="audit-kpi-label">Training offer ratio</div><strong>{value(impact.training_offer_rate_ratio,'×')}</strong><small>Four-fifths rule {impact.four_fifths_rule_met == null ? '—' : impact.four_fifths_rule_met ? 'met' : 'needs review'}</small><div className="audit-meter teal"><i style={{width:`${Math.min(100,Number(impact.training_offer_rate_ratio||0)*100)}%`}}/></div></div>
      <div className="audit-kpi"><div className="audit-kpi-label">Counterfactual flip rate</div><strong>{value(counter.assignment_flip_rate_pct,'%')}</strong><small>{counter.attribute_flipped || 'Attribute test'} · review signal</small><div className="audit-meter violet"><i style={{width:`${Math.min(100,Number(counter.assignment_flip_rate_pct||0))}%`}}/></div></div>
      <div className="audit-kpi"><div className="audit-kpi-label">Agents completed</div><strong>{pipelineData?.total_agents_run ?? '—'}<em>{pipelineData ? ' / 7' : ''}</em></strong><small>Evidence from this scenario run</small><div className="audit-meter slate"><i style={{width:`${Math.min(100,Number(pipelineData?.total_agents_run||0)/7*100)}%`}}/></div></div>
    </div>
    <div className="audit-lower-grid"><div className="audit-detail-card"><div className="side-title"><ShieldCheck size={16}/> Audit checks</div><FairnessAuditCard biasAuditEvent={biasAuditEvent}/>{!biasAuditEvent && <div className="audit-empty"><AlertTriangle size={16}/><span>Audit details appear after the bias agent completes a pipeline run.</span></div>}</div><div className="audit-detail-card fairness-note"><div className="side-title"><Users size={16}/> How to read these signals</div><p>A counterfactual change or disparity does not establish discrimination. It highlights an allocation that deserves a closer look.</p><div className="audit-note-row"><span className="note-dot blue"/><span>Check the job-related evidence and constraint that produced the recommendation.</span></div><div className="audit-note-row"><span className="note-dot amber"/><span>Review whether training opportunities and idle hours are distributed unevenly.</span></div><div className="audit-note-row"><span className="note-dot green"/><span>Managers retain authority; no assignment is applied automatically.</span></div><button className="btn btn-primary" onClick={onStrategies}>Open allocation strategies <ArrowRight size={14}/></button></div></div>
  </div>;
}

function StrategyWorkspace({ pipelineData, onApprove, approvalStatus, onRun }) {
  return <div className="workspace-page strategy-workspace"><div className="workspace-page-head"><div><div className="screen-kicker"><GitCompare size={13}/> DECISION OPTIONS</div><h1>Allocation strategies</h1><p>Compare baseline, cost-focused, and fairness-balanced plans using the same scenario evidence.</p></div><button className="btn btn-secondary" onClick={onRun}>{pipelineData ? 'Re-run pipeline' : 'Set up / run scenario'} <ArrowRight size={14}/></button></div>
    {approvalStatus==='approved' && <div className="approval-confirm"><CheckCircle size={16}/> Plan approved and recorded in the ShiftSure workflow.</div>}
    {approvalStatus==='error' && <div className="approval-error"><AlertTriangle size={16}/> Approval did not complete. Check the backend connection and retry.</div>}
    <div className="strategy-intro"><div><b>Three options, one human decision</b><span>The optimizer returns comparable plans. Review trade-offs before selecting a recommendation.</span></div><span className="integration-label conceptual"><i/>Decision remains with manager</span></div>
    <PlanComparisonTable pipelineData={pipelineData} onApprove={onApprove}/>
    {!pipelineData && <div className="strategy-empty"><div className="screen-empty-icon"><GitCompare size={19}/></div><b>No strategy results yet</b><p>Create a disruption scenario, then run the live agent pipeline to generate the three options.</p><button className="btn btn-primary" onClick={onRun}>Continue to planning <ArrowRight size={14}/></button></div>}
  </div>;
}

function StatBlock({ label, value, color, small }) {
  return (
    <div style={{
      padding: '10px 12px',
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-light)',
      borderRadius: 8,
      animation: 'fadeSlideIn 0.4s ease',
    }}>
      <div style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{
        fontFamily: small ? 'var(--font-sans)' : 'var(--font-display)',
        fontSize: small ? '0.78rem' : '0.95rem',
        fontWeight: 600,
        color: color || 'var(--text-primary)',
      }}>
        {value}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════
   WORKER VIEW — Priya Sharma Employee Portal
══════════════════════════════════════════════════════════════════════ */

function WorkerView({ notification }) {
  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', marginBottom: 4 }}>
          Employee Mobility Portal <span className="integration-label conceptual"><i />Conceptual · SuccessFactors</span>
        </h1>
        <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)' }}>
          Personalised redeployment notice, bridge course recommendation, and appeal rights for displaced operators.
        </p>
      </div>
      <div style={{ maxWidth: 720 }}>
        <WorkerPortal notification={notification} />
      </div>
    </div>
  );
}
