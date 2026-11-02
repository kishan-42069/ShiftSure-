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
  CheckCircle, ChevronRight, LayoutDashboard
} from 'lucide-react';

/* ── Sidebar navigation items ──────────────────────────────────────── */
const MAIN_NAV = [
  { id: 'overview',      icon: Home,            label: 'Overview & Story' },
  { id: 'manager',       icon: LayoutDashboard, label: 'Disruption Manager' },
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
    setActiveTab('manager');
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
            onNavigateToManager={() => setActiveTab('manager')}
            onQuickStartDemo={handleQuickStartDemo}
          />
        )}

        {activeTab === 'manager' && (
          <ManagerView
            activeScenario={activeScenario}
            onScenarioCreated={setActiveScenario}
            pipelineData={pipelineData}
            onPipelineComplete={handlePipelineComplete}
            biasAuditEvent={biasAuditEvent}
            onBiasAuditEvent={handleBiasAuditEvent}
            onNotificationEvent={handleNotificationEvent}
            approvalStatus={approvalStatus}
            onApprove={handleApprove}
            onSwitchToWorker={() => setActiveTab('worker')}
          />
        )}

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

/* ══════════════════════════════════════════════════════════════════════
   MANAGER VIEW — Disruption Control Center
══════════════════════════════════════════════════════════════════════ */

function ManagerView({
  activeScenario, onScenarioCreated,
  pipelineData, onPipelineComplete,
  biasAuditEvent, onBiasAuditEvent,
  onNotificationEvent, approvalStatus, onApprove,
  onSwitchToWorker,
}) {
  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      {/* Page heading */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', marginBottom: 4 }}>
            Disruption Control Center
          </h1>
          <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)' }}>
            Configure the automation event, trigger the 7-agent pipeline, compare allocation strategies, and approve the plan.
          </p>
        </div>
        {pipelineData && (
          <button className="btn btn-ghost" onClick={onSwitchToWorker} style={{ gap: 4 }}>
            Preview Priya's View <ChevronRight size={14} />
          </button>
        )}
      </div>

      {/* Two-column layout: form + stream | comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 18, alignItems: 'start' }}>

        {/* Left: Form, Summary, Fairness */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <ScenarioPanel onScenarioCreated={onScenarioCreated} activeScenario={activeScenario} />

          {pipelineData && (
            <div className="card" style={{ animation: 'scaleIn 0.4s ease' }}>
              <div className="card-header">
                <h3>Pipeline Summary</h3>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <StatBlock label="Agents Run" value={`${pipelineData.total_agents_run ?? 7} / 7`} />
                <StatBlock
                  label="Employer Readiness"
                  value={pipelineData.employer_ready ? 'Verified' : 'Blocked'}
                  color={pipelineData.employer_ready ? 'var(--green)' : 'var(--red)'}
                />
                <StatBlock
                  label="Bias Audit"
                  value={(pipelineData.audit_status || '—').replace(/_/g, ' ')}
                  color={pipelineData.audit_status === 'PASSED' ? 'var(--green)' : 'var(--orange)'}
                />
                <StatBlock label="Scenario ID" value={pipelineData.scenario_id} small />
              </div>

              {approvalStatus === 'approved' && (
                <div style={{
                  marginTop: 12,
                  padding: '10px 14px',
                  background: 'var(--green-subtle)',
                  border: '1px solid var(--green-border)',
                  borderRadius: 8,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: '0.8rem',
                  color: 'var(--green)',
                  animation: 'fadeSlideIn 0.4s ease',
                }}>
                  <CheckCircle size={14} />
                  Plan approved. Audit log committed to SAP SuccessFactors.
                </div>
              )}
            </div>
          )}

          <FairnessAuditCard biasAuditEvent={biasAuditEvent} />
        </div>

        {/* Right: Stream + Plan Comparison */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <AgentStreamConsole
            scenarioId={activeScenario?.id}
            onPipelineComplete={onPipelineComplete}
            onBiasAuditEvent={onBiasAuditEvent}
            onNotificationEvent={onNotificationEvent}
          />
          <PlanComparisonTable pipelineData={pipelineData} onApprove={onApprove} />
        </div>
      </div>
    </div>
  );
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
          SAP SuccessFactors — Employee Mobility Portal
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
