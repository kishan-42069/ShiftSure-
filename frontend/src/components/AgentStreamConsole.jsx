import { useState, useEffect } from 'react';
import {
  Search, TrendingUp, BookOpen, Shuffle,
  ShieldCheck, Eye, UserCheck, CheckCircle,
  AlertTriangle, Clock, ChevronDown, ChevronUp,
  Play, RefreshCw,
} from 'lucide-react';
import { useAgentStream } from '../hooks/useAgentStream';

const AGENT_CONFIG = [
  { name: 'Skills Discovery Agent',       icon: Search,      color: 'var(--accent)' },
  { name: 'Market Intelligence Agent',    icon: TrendingUp,  color: 'var(--green)' },
  { name: 'Learning Pathway Agent',       icon: BookOpen,    color: 'var(--orange)' },
  { name: 'Inclusive Matching Agent',     icon: Shuffle,     color: 'var(--accent)' },
  { name: 'Employer Readiness Agent',     icon: ShieldCheck, color: 'var(--green)' },
  { name: 'Bias Audit Agent',            icon: Eye,         color: 'var(--orange)' },
  { name: 'Human-in-the-Loop Safeguard', icon: UserCheck,   color: 'var(--green)' },
];

function getAgentStatus(agentName, events) {
  const finished = events.find((e) => e.event_type === 'AGENT_RESULT' && e.agent === agentName);
  const started  = events.find((e) => e.event_type === 'AGENT_START'  && e.agent === agentName);
  const error    = events.find((e) => e.event_type === 'ORCHESTRATOR_ERROR');
  if (finished) return 'done';
  if (started)  return error ? 'error' : 'running';
  return 'pending';
}

function AgentStep({ config, agentStatus, result, isLast, delay }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = config.icon;
  const reasoning = result?.reasoning || '';

  useEffect(() => { if (agentStatus === 'done') setExpanded(true); }, [agentStatus]);

  return (
    <div className="agent-step" style={{ animationDelay: delay }}>
      {!isLast && <div className="agent-line" />}

      <div className={`agent-icon-wrap ${agentStatus}`}>
        {agentStatus === 'running' ? (
          <span className="spinner" />
        ) : agentStatus === 'done' ? (
          <CheckCircle size={14} color="var(--green)" />
        ) : agentStatus === 'error' ? (
          <AlertTriangle size={14} color="var(--red)" />
        ) : (
          <Icon size={13} color="var(--text-muted)" />
        )}
      </div>

      <div className={`agent-card ${agentStatus}`}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon size={13} color={agentStatus === 'pending' ? 'var(--text-muted)' : config.color} />
            <span className="agent-name">{config.name}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {agentStatus === 'running' && (
              <span className="label-status blue" style={{ fontSize: '0.73rem' }}>
                <div className="dot-indicator blue" />
                Running<span className="typing-cursor" />
              </span>
            )}
            {agentStatus === 'done' && (
              <span className="label-status green" style={{ fontSize: '0.73rem' }}>
                <div className="dot-indicator green" />
                Done
              </span>
            )}
            {agentStatus === 'pending' && (
              <span className="label-status muted" style={{ fontSize: '0.73rem' }}>Waiting</span>
            )}
            {reasoning && (
              <button
                onClick={() => setExpanded((v) => !v)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', padding: 2 }}
              >
                {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>
            )}
          </div>
        </div>

        {expanded && reasoning && (
          <p className="agent-reasoning">{reasoning}</p>
        )}

        {agentStatus === 'done' && result && (
          <AgentResultKPIs agentName={config.name} data={result.data || result} />
        )}
      </div>
    </div>
  );
}

function AgentResultKPIs({ agentName, data }) {
  if (agentName === 'Skills Discovery Agent') {
    return (
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
        <KPI label="Verified Skills" value={data.verified_skills?.length ?? 0} />
        <KPI label="Bridge Eligible" value={data.bridge_eligible ? 'Yes' : 'No'} color={data.bridge_eligible ? 'var(--green)' : 'var(--text-muted)'} />
        <KPI label="Best Match" value={`${data.best_transferability_pct ?? 0}%`} />
      </div>
    );
  }
  if (agentName === 'Inclusive Matching Agent') {
    const ps = data.plan_summary || {};
    return (
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
        <KPI label="Workers Matched" value={ps.workers_matched ?? 0} />
        <KPI label="Fill Rate" value={`${ps.fill_rate_pct ?? 0}%`} />
        <KPI label="Idle Hours Saved" value={ps.idle_hours_saved ?? 0} />
      </div>
    );
  }
  if (agentName === 'Bias Audit Agent') {
    return (
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
        <KPI label="Audit Status" value={(data.audit_status || '').replace(/_/g, ' ')}
          color={data.audit_status === 'PASSED' ? 'var(--green)' : 'var(--orange)'} />
        <KPI label="4/5ths Rule" value={data.adverse_impact?.four_fifths_rule_met ? '✓ Met' : '✗ Failed'} />
      </div>
    );
  }
  return null;
}

function KPI({ label, value, color }) {
  return (
    <div>
      <div style={{ fontSize: '0.67rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.88rem', fontWeight: 600, color: color || 'var(--text-primary)' }}>{value}</div>
    </div>
  );
}

export default function AgentStreamConsole({ scenarioId, onPipelineComplete, onBiasAuditEvent, onNotificationEvent }) {
  const { events, status, start, reset } = useAgentStream(scenarioId);
  const pipelineComplete = events.find((e) => e.event_type === 'PIPELINE_COMPLETE');

  useEffect(() => {
    if (pipelineComplete) onPipelineComplete?.(pipelineComplete.data);
  }, [pipelineComplete]);

  useEffect(() => {
    const biasEvt = events.find((e) => e.event_type === 'AGENT_RESULT' && e.agent === 'Bias Audit Agent');
    if (biasEvt) onBiasAuditEvent?.(biasEvt.data || biasEvt);
  }, [events]);

  useEffect(() => {
    const notifEvt = events.find((e) => e.event_type === 'AGENT_RESULT' && e.agent === 'Human-in-the-Loop Safeguard');
    if (notifEvt) onNotificationEvent?.(notifEvt.data || notifEvt);
  }, [events]);

  const statusColor = { idle: 'var(--text-muted)', connecting: 'var(--orange)', running: 'var(--accent)', done: 'var(--green)', error: 'var(--red)' }[status];
  const statusLabel = { idle: 'Ready', connecting: 'Connecting…', running: 'Pipeline Running', done: 'Complete', error: 'Error' }[status];

  return (
    <div className="card" style={{ animation: 'fadeSlideIn 0.4s ease' }}>
      <div className="card-header">
        <Shuffle size={15} color="var(--accent)" />
        <h2>Live Agent Reasoning Stream</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="label-status" style={{ color: statusColor, fontSize: '0.78rem' }}>
            {status === 'running' && <span className="spinner" style={{ borderTopColor: 'var(--accent)' }} />}
            {statusLabel}
          </div>
          {(status === 'idle' || status === 'done' || status === 'error') && (
            <button
              className="btn btn-primary"
              style={{ padding: '6px 14px', fontSize: '0.8rem' }}
              onClick={status === 'idle' ? start : () => { reset(); setTimeout(start, 100); }}
              disabled={!scenarioId}
            >
              {status === 'idle' ? <><Play size={12} /> Run Agents</> : <><RefreshCw size={12} /> Re-run</>}
            </button>
          )}
        </div>
      </div>

      {!scenarioId && (
        <div className="empty-state" style={{ paddingTop: 28 }}>
          <Clock size={28} />
          <p>Create a disruption scenario first, then run the agent pipeline.</p>
        </div>
      )}

      {scenarioId && (
        <div className="agent-timeline">
          {AGENT_CONFIG.map((cfg, idx) => {
            const agentStatus = getAgentStatus(cfg.name, events);
            const resultEvent = events.find((e) => e.event_type === 'AGENT_RESULT' && e.agent === cfg.name);
            return (
              <AgentStep
                key={cfg.name}
                config={cfg}
                agentStatus={agentStatus}
                result={resultEvent}
                isLast={idx === AGENT_CONFIG.length - 1}
                delay={`${idx * 0.05}s`}
              />
            );
          })}
        </div>
      )}

      {pipelineComplete && (
        <div style={{
          marginTop: 14,
          padding: '10px 14px',
          background: 'var(--green-subtle)',
          border: '1px solid var(--green-border)',
          borderRadius: 8,
          fontSize: '0.8rem',
          color: 'var(--green)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          animation: 'fadeSlideIn 0.4s ease',
        }}>
          <CheckCircle size={14} />
          All 7 agents complete · 3 allocation strategies generated · Awaiting manager approval
        </div>
      )}
    </div>
  );
}
