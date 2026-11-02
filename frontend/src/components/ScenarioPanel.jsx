import { useState } from 'react';
import { Zap, AlertCircle } from 'lucide-react';
import { createScenario } from '../api';

const LINES = [
  { id: 'LINE-01', label: 'LINE-01 — Assembly Line (Smart Components)' },
  { id: 'LINE-02', label: 'LINE-02 — Quality & Maintenance Line' },
  { id: 'LINE-03', label: 'LINE-03 — Packaging Line (Automation Disruption)' },
];

export default function ScenarioPanel({ onScenarioCreated, activeScenario }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: 'Line 3 Packaging Automation',
    affected_line_id: 'LINE-03',
    workload_reduction_pct: 0.80,
    planning_period_hours: 40,
    max_training_hours: 20,
    fairness_weight: 0.35,
    idle_disparity_threshold: 0.15,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const scenario = await createScenario({
        ...form,
        workload_reduction_pct: parseFloat(form.workload_reduction_pct),
        planning_period_hours: parseFloat(form.planning_period_hours),
        max_training_hours: parseFloat(form.max_training_hours),
        fairness_weight: parseFloat(form.fairness_weight),
        idle_disparity_threshold: parseFloat(form.idle_disparity_threshold),
      });
      onScenarioCreated(scenario);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const pct = Math.round(form.workload_reduction_pct * 100);
  const fairPct = Math.round(form.fairness_weight * 100);

  return (
    <div className="card">
      <div className="card-header">
        <AlertCircle size={16} color="var(--orange)" />
        <h2>Disruption Scenario</h2>
        {activeScenario && (
          <div className="label-status green" style={{ marginLeft: 'auto', fontSize: '0.75rem' }}>
            <div className="dot-indicator green" />
            Scenario active
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          <div>
            <label className="field-label">Scenario Name</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="field-label">Affected Production Line</label>
            <select
              className="select"
              value={form.affected_line_id}
              onChange={(e) => setForm({ ...form, affected_line_id: e.target.value })}
            >
              {LINES.map((l) => (
                <option key={l.id} value={l.id}>{l.label}</option>
              ))}
            </select>
          </div>

          {/* Automation reduction slider */}
          <div>
            <label className="field-label">
              Automation Reduction
              <span style={{ marginLeft: 6, fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                {pct}%
              </span>
            </label>
            <input
              type="range" min="0.1" max="1.0" step="0.05"
              value={form.workload_reduction_pct}
              onChange={(e) => setForm({ ...form, workload_reduction_pct: e.target.value })}
              style={{ width: '100%', marginTop: 4, accentColor: 'var(--accent)' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
              <span>10%</span><span>100%</span>
            </div>
          </div>

          <div className="grid-2">
            <div>
              <label className="field-label">Planning Period (hrs)</label>
              <input type="number" className="input" value={form.planning_period_hours}
                min="8" max="160" onChange={(e) => setForm({ ...form, planning_period_hours: e.target.value })} />
            </div>
            <div>
              <label className="field-label">Max Training Hours</label>
              <input type="number" className="input" value={form.max_training_hours}
                min="0" max="40" onChange={(e) => setForm({ ...form, max_training_hours: e.target.value })} />
            </div>
          </div>

          {/* Fairness slider */}
          <div>
            <label className="field-label">
              Fairness Weight
              <span style={{ marginLeft: 6, fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                {fairPct}%
              </span>
              <span style={{ marginLeft: 4, color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.72rem' }}>(0 = pure cost)</span>
            </label>
            <input
              type="range" min="0" max="1" step="0.05"
              value={form.fairness_weight}
              onChange={(e) => setForm({ ...form, fairness_weight: e.target.value })}
              style={{ width: '100%', marginTop: 4, accentColor: 'var(--accent)' }}
            />
          </div>

          {error && (
            <div style={{
              padding: '9px 12px',
              background: 'var(--red-subtle)',
              border: '1px solid var(--red-border)',
              borderRadius: 6,
              color: 'var(--red)',
              fontSize: '0.8rem',
            }}>
              {error}
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ justifyContent: 'center' }}>
            {loading ? <span className="spinner" /> : <Zap size={14} />}
            {loading ? 'Creating scenario…' : 'Create Disruption Scenario'}
          </button>
        </div>
      </form>
    </div>
  );
}
