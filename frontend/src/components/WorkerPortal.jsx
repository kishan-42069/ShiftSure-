import { useState } from 'react';
import { User, BookOpen, MessageSquare, CheckCircle, ExternalLink, Clock } from 'lucide-react';

const WORKER = {
  name: 'Priya Sharma',
  initials: 'PS',
  role: 'Senior Packaging & Assembly Specialist',
  line: 'LINE-03 — Packaging Line',
  shift: 'Morning Shift',
  tenure: '5.2 years',
  skills: ['Manual Assembly', 'Quality Inspection', 'Packaging Operations'],
  bridgeCourse: {
    code: 'SAP-LH-ROB-101',
    title: 'Robotics Safety & Collaborative Arm Operation',
    hours: 8,
    cost: 4500,
    cert: 'ROBOTICS_SAFETY_L1',
    url: 'https://learning.sap.com/courses/robotics-safety-collaborative',
    provider: 'SAP Learning Hub (Student Edition)',
  },
  newRole: {
    title: 'Automated Pick-and-Place Quality Checker',
    line: 'LINE-01 — Assembly Line (Smart Components)',
    shift: 'Morning Shift',
  },
};

export default function WorkerPortal({ notification }) {
  const [appealText, setAppealText] = useState('');
  const [appealSent, setAppealSent] = useState(false);

  const handleAppeal = () => {
    if (!appealText.trim()) return;
    setAppealSent(true);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Worker hero */}
      <div className="worker-hero">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 18 }}>
          <div className="worker-avatar">{WORKER.initials}</div>
          <div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.35rem', marginBottom: 3 }}>{WORKER.name}</h2>
            <p style={{ fontSize: '0.82rem', marginBottom: 8 }}>{WORKER.role} · {WORKER.shift} · {WORKER.tenure} tenure</p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {WORKER.skills.map((s) => (
                <div key={s} className="label-status muted" style={{ fontSize: '0.75rem' }}>
                  <div className="dot-indicator blue" />
                  {s}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 8 }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 3 }}>Current Assignment</div>
          <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)' }}>{WORKER.line}</div>
        </div>
      </div>

      {/* Transfer Notice */}
      <div className="card">
        <div className="card-header">
          <User size={14} color="var(--accent)" />
          <h3>Your Proposed Transfer Notice</h3>
          <div className="label-status orange" style={{ marginLeft: 'auto', fontSize: '0.75rem' }}>
            <Clock size={11} />
            24hr review window open
          </div>
        </div>

        <p style={{ fontSize: '0.83rem', lineHeight: 1.65, marginBottom: 16 }}>
          {notification?.worker_notification?.message ||
            `Dear ${WORKER.name}, you have been proposed for a transfer to ${WORKER.newRole.line} 
            under the ShiftSure Fair Reallocation Plan (Plan C). To qualify for your new role 
            (${WORKER.newRole.title}), you are recommended to complete a bridge course via SAP 
            Learning Hub. You have 24 hours to review this proposal and raise any concerns.`}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {[
            { label: 'Proposed Role', value: WORKER.newRole.title },
            { label: 'Target Line',   value: WORKER.newRole.line },
            { label: 'Shift',         value: WORKER.newRole.shift },
            { label: 'Eligibility',   value: 'Qualified after bridge course' },
          ].map(({ label, value }) => (
            <div key={label} style={{ padding: '10px 12px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 8 }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: 3 }}>{label}</div>
              <div style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)' }}>{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* SAP Learning Hub Bridge Course */}
      <div className="card">
        <div className="card-header">
          <BookOpen size={14} color="var(--green)" />
          <h3>SAP Learning Hub Bridge Course</h3>
        </div>

        <div className="course-card">
          <div className="course-icon"><BookOpen size={18} /></div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1rem', marginBottom: 4, color: 'var(--text-primary)' }}>
              {WORKER.bridgeCourse.title}
            </div>
            <p style={{ fontSize: '0.78rem', marginBottom: 10 }}>
              {WORKER.bridgeCourse.provider} · Code: {WORKER.bridgeCourse.code}
            </p>
            <div style={{ display: 'flex', gap: 20, marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 2 }}>Duration</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>{WORKER.bridgeCourse.hours} hrs</div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 2 }}>Investment</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>₹{WORKER.bridgeCourse.cost.toLocaleString()}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 2 }}>Certification</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--green)' }}>{WORKER.bridgeCourse.cert}</div>
              </div>
            </div>
            <a
              href={WORKER.bridgeCourse.url}
              target="_blank"
              rel="noreferrer"
              className="btn btn-primary"
              style={{ textDecoration: 'none', display: 'inline-flex', padding: '7px 14px', fontSize: '0.82rem' }}
            >
              <ExternalLink size={13} />
              Open in SAP Learning Hub
            </a>
          </div>
        </div>
      </div>

      {/* Appeal Form */}
      <div className="card">
        <div className="card-header">
          <MessageSquare size={14} color="var(--text-secondary)" />
          <h3>Appeal or Correct Your Skill Record</h3>
        </div>

        {!appealSent ? (
          <>
            <p style={{ fontSize: '0.83rem', marginBottom: 12 }}>
              If your skills or certifications are recorded incorrectly, or if you wish to appeal this transfer decision, submit your concern below. Your manager will respond within 24 hours.
            </p>
            <textarea
              className="appeal-textarea"
              placeholder="Describe your concern or the skill you believe is incorrectly recorded…"
              value={appealText}
              onChange={(e) => setAppealText(e.target.value)}
            />
            <button
              className="btn btn-secondary"
              style={{ marginTop: 10 }}
              onClick={handleAppeal}
              disabled={!appealText.trim()}
            >
              <MessageSquare size={13} />
              Submit Appeal
            </button>
          </>
        ) : (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
            background: 'var(--green-subtle)', border: '1px solid var(--green-border)',
            borderRadius: 8, animation: 'fadeSlideIn 0.4s ease',
          }}>
            <CheckCircle size={14} color="var(--green)" />
            <span style={{ fontSize: '0.82rem', color: 'var(--green)' }}>
              Your appeal has been submitted. Your manager will review within 24 hours.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
