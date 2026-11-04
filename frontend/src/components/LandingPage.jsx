import { useEffect, useRef } from 'react';
import { ArrowRight, Cpu, ShieldCheck, Sparkles, BookOpen, Scale, Factory, Users, GraduationCap, BriefcaseBusiness, BadgeCheck, Cog, ArrowUpRight, Workflow, HardHat, Wrench, ClipboardCheck, Network, UserRound, Search } from 'lucide-react';

const RING1_NODES = ['Skills\nDiscovery', 'Learning\nPathways', 'CP-SAT\nOptimizer', 'Human\nReview'];
const RING2_NODES = ['Manufacturing\nDemand', 'Employee\nSkills', 'Fairness\nSignals', 'Open\nRoles'];
const FEED_ITEMS = [
  { initials: 'PS', name: 'Priya Sharma', action: 'matched to LINE-01 · assembly technician', time: 'Planning example' },
  { initials: 'RA', name: 'Rohan Anand', action: 'learning path suggested · Robotics Safety L1', time: 'Planning example' },
  { initials: 'KM', name: 'Kavita More', action: 'counterfactual allocation flagged for review', time: 'Planning example' },
  { initials: 'VP', name: 'Vijay Patil', action: 'redeployment proposal ready for manager review', time: 'Planning example' },
];

export default function LandingPage({ onNavigateToManager, onQuickStartDemo }) {
  const feedRef = useRef(null);
  useEffect(() => {
    feedRef.current?.querySelectorAll('.activity-item').forEach((el, i) => { el.style.animationDelay = `${0.2 + i * 0.1}s`; });
  }, []);
  return (
    <div className="landing-root">
      <section className="landing-hero-section">
        <div className="doodle-layer hero-doodles" aria-hidden="true">
          <span className="doodle d-plant"><Factory/></span><span className="doodle d-people"><Users/></span>
          <span className="doodle d-skills"><BadgeCheck/></span><span className="doodle d-growth"><ArrowUpRight/></span>
          <span className="doodle d-gear"><Cog/></span><span className="doodle d-hardhat"><HardHat/></span>
          <span className="doodle d-tools"><Wrench/></span><span className="doodle d-search"><Search/></span>
          <span className="doodle d-role"><BriefcaseBusiness/></span><i className="doodle-route route-left"/><i className="doodle-route route-right"/>
          <span className="doodle-sketch sketch-line"><svg viewBox="0 0 100 70" fill="none"><g stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M9 54V26l17-10 17 10v28M15 54V31h22v23M21 39h10M50 54V18h31v36M56 27h7m7 0h6M56 36h7m7 0h6M56 45h7m7 0h6M5 59c25 4 55 4 87 0"/><path d="m45 20 4-4 4 4" strokeDasharray="2 3"/></g></svg></span>
        </div>
        <div className="landing-hero-wrap">
          <div className="hero-eyebrow">Workforce resilience · Automation response</div>
          <h1 className="hero-headline">When Automation Arrives,<br/><em>People Deserve a Next Step.</em></h1>
          <p className="hero-subhead">ShiftSure helps managers explore internal roles for employees affected by automation, understand skill gaps, and review allocation fairness. The optimizer proposes matches; people make the decisions.</p>
          <div className="hero-cta-row">
            <button className="btn btn-primary" style={{padding:'11px 24px',fontSize:'.9rem',fontWeight:600}} onClick={onNavigateToManager}>Open planning workspace <ArrowRight size={16}/></button>
            <button className="btn btn-secondary" style={{padding:'11px 22px',fontSize:'.9rem'}} onClick={onQuickStartDemo}><Sparkles size={15} color="var(--accent)"/>Load Line 3 scenario</button>
          </div>
          <div className="landing-showcase">
            <div className="orbital-system">
              <div className="orbital-ring orbital-ring-1">{RING1_NODES.map((label,i)=><div key={label} className="orbital-node" style={getNodeStyle(i,4)}><span style={{whiteSpace:'pre-line',lineHeight:1.25}}>{label}</span></div>)}</div>
              <div className="orbital-ring orbital-ring-2">{RING2_NODES.map((label,i)=><div key={label} className="orbital-node" style={getNodeStyle(i,4)}><span style={{whiteSpace:'pre-line',lineHeight:1.25}}>{label}</span></div>)}</div>
              <div className="orbital-center"><div className="orbital-center-icon"><Cpu size={18} color="#fff"/></div><span>ShiftSure<br/>Planning</span></div>
            </div>
            <div className="activity-feed" ref={feedRef}>
              <div className="activity-feed-header"><div className="dot-indicator blue"/>Planning workflow · illustrative data</div>
              {FEED_ITEMS.map(item=><div key={item.initials} className="activity-item anim-fade-up"><div className="activity-avatar">{item.initials}</div><div><div className="activity-text"><strong>{item.name}</strong> <span>{item.action}</span></div><div className="activity-time">{item.time}</div></div></div>)}
            </div>
          </div>
        </div>
      </section>
      <div className="landing-status-row"><span className="landing-integration live"><i/>Live · SAP BTP &amp; GenAI Hub</span><span className="landing-integration simulated"><i/>Simulated · SAP Learning Hub</span><span className="landing-integration conceptual"><i/>Conceptual · SuccessFactors / Joule</span><span className="landing-demo-note">Sample figures shown for demonstration</span></div>
      <div className="landing-metrics-wrap"><div className="metrics-strip">{[
        {value:'180',label:'Shop-floor operators\nacross 3 production lines'},
        {value:'45',label:'Employees in the\nLine 3 scenario'},
        {value:'₹18.4L',label:'Illustrative hiring cost\navoidance estimate'},
        {value:'7',label:'Planning agents\nin the prototype'},
      ].map((m,i)=><div key={m.label} className="metric-block" style={{animationDelay:`${i*.08}s`}}><div className="metric-block-value">{m.value}</div><div className="metric-block-label">{m.label}</div></div>)}</div><div className="doodle-layer metrics-doodles" aria-hidden="true"><span className="doodle md-one"><Users/></span><span className="doodle md-two"><Workflow/></span><span className="doodle md-three"><GraduationCap/></span><span className="doodle md-four"><BadgeCheck/></span><span className="doodle md-five"><Factory/></span><span className="doodle md-six"><ArrowUpRight/></span></div></div>
      <div className="pillars-grid circular-features service-focus">
        <div className="doodle-layer feature-doodles" aria-hidden="true">
          <span className="doodle d-course"><GraduationCap/></span><span className="doodle d-role"><BriefcaseBusiness/></span>
          <span className="doodle d-team"><UserRound/></span><span className="doodle d-checklist"><ClipboardCheck/></span>
          <span className="doodle d-network"><Network/></span><span className="doodle d-match"><Workflow/></span>
          <span className="doodle d-toolbox"><Wrench/></span><span className="doodle d-badge"><BadgeCheck/></span>
          <span className="doodle-sketch sketch-training"><svg viewBox="0 0 100 70" fill="none"><g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 20c13-5 25-3 39 4v31c-14-7-26-9-39-4V20Zm78 0c-13-5-25-3-39 4v31c14-7 26-9 39-4V20ZM48 24v30M18 29c7-2 14-1 21 2m-21 5c7-2 14 0 21 3m22-8c7-3 14-4 21-2m-21 10c7-3 14-4 21-2"/><path d="m76 8 2 5 5 2-5 2-2 5-2-5-5-2 5-2 2-5Z"/></g></svg></span>
          <span className="doodle-sketch sketch-review"><svg viewBox="0 0 88 76" fill="none"><g stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17 15h12m-9-5h31c3 0 5 2 5 5v48H14V15c0-3 2-5 5-5Zm8 16h20M27 36h12M27 45h8"/><path d="m40 51 6 6 13-16"/><circle cx="67" cy="20" r="8"/><path d="M61 34c2-5 10-5 13 0M5 69c19 4 49 4 76 0" strokeDasharray="2 4"/></g></svg></span>
        </div>
        <div className="landing-pillar-heading"><p>HOW SHIFTSURE SUPPORTS DECISIONS</p><h2>Practical workforce planning, with people in control.</h2><span>Four steps that keep people at the center of automation response</span></div>
        <svg className="service-arc" viewBox="0 0 1000 150" preserveAspectRatio="none" aria-hidden="true"><path d="M 0 8 C 210 8 245 138 500 138 C 755 138 790 8 1000 8"/></svg><div className="service-hub" aria-hidden="true" title="Skills matched to meaningful work"><svg className="redeploy-doodle" viewBox="0 0 48 48" fill="none"><g stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M10.8 17.1c.1-3.1 2.3-5.3 5.1-5.2 2.8.1 4.6 2.4 4.4 5.4-.2 2.9-1.8 4.9-4.6 4.9-2.8-.1-5-2.1-4.9-5.1Z"/><path d="M7.5 34.2c.6-5.1 3.1-8.2 8-8.2 4.8 0 7.4 3 7.8 8.2M29 14.6c.2-2.4 2-4.1 4.3-4 2.3.1 3.8 2 3.6 4.4-.2 2.3-1.5 3.9-3.8 3.9-2.4-.1-4.2-1.8-4.1-4.3Z"/><path d="M26.5 28.8c.5-3.7 2.4-5.9 6.1-5.9 3.4 0 5.4 2.1 5.9 5.9M21.8 17.5c2.1-2.2 4.2-3.2 7.2-3.1M26.1 11.9l3 2.5-3.2 2.4M10 37.7c5.4 1.8 12.3 1.8 18 .1M25.6 35.3l3.1 2.5-3.2 2.3"/><path d="M9.8 16.2c.4-2.4 1.9-3.8 4.1-4.1M30.5 13c.7-1.3 1.9-1.9 3.3-1.7" opacity=".7"/></g></svg></div>
        {[
          {Icon:Cpu,title:'Skills-to-role matching',desc:'Compare employee skills and available capacity with open work. The optimizer handles constraints; it does not make final employment decisions.'},
          {Icon:Scale,title:'Fairness review signals',desc:'Inspect allocation balance and counterfactual changes. A changed result is a prompt for review, not proof of discrimination.'},
          {Icon:BookOpen,title:'Training pathways',desc:'Identify skill gaps and review suggested learning time and investment. Learning Hub enrollment is simulated in this prototype.'},
          {Icon:ShieldCheck,title:'Manager approval',desc:'Review the evidence, compare alternatives, and approve or reject a proposed plan. No transfer or employee record change happens automatically.'},
        ].map(({title,desc},i)=><article key={title} className={`service-node service-node-${i+1}`}><div className="service-node-title">{title}</div><p>{desc}</p><span className="service-node-number">0{i+1}</span></article>)}
      </div>
      <div className="governance-banner"><div className="governance-inner"><div className="governance-icon-box"><ShieldCheck size={20}/></div><div><h3>Recommendations stay reviewable</h3><p>Allocation is based on job-related constraints. Fairness indicators help managers investigate potential disparities, while final decisions remain with people.</p><div className="landing-governance-tags">{['Job-related criteria','Counterfactual review','Manager approval','Decision history'].map(t=><span key={t}>{t}</span>)}</div></div></div></div>
      <div className="trust-bar"><div className="trust-bar-label">Product context</div><div className="trust-logos">{['Manufacturing workforce planning','Constraint optimization','Skills & learning pathways','Human-reviewed decisions'].map(n=><div key={n} className="trust-logo-item">{n}</div>)}</div></div>
    </div>
  );
}

function getNodeStyle(index,total){const angle=(360/total)*index-90,rad=angle*Math.PI/180,radius=50,x=50+radius*Math.cos(rad),y=50+radius*Math.sin(rad);return{position:'absolute',left:`calc(${x}% - 25px)`,top:`calc(${y}% - 25px)`}}
