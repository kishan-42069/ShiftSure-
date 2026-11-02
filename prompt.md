You are a senior AI systems architect and hackathon technical strategist with deep experience in multi-agent systems, enterprise workforce software, and responsible AI. I am building **ShiftSure – Fair Workforce Reallocation During Automation and Disruption** for the SAP Hackfest Hackathon 2026 Grand Finale, under **Domain 2: Inclusive Workforce (Theme 2)**.

I have attached three source documents, which carry different authority:
- **SAP Participant Handbook** (authoritative for competition requirements, judging criteria, and presentation format)
- **ShiftSure Product Requirements Document (PRD)** (authoritative for our product vision, functionality, scope, and prototype boundaries)
- **ShiftSure project presentation (PPT)** (authoritative for our existing demo narrative and design decisions)

Refer to each by filename when you analyse it. Read the full documents; do not rely on summaries.

**Goal:** Produce a technically credible, fully integrated, production-quality multi-agent architecture and implementation blueprint that preserves ShiftSure's original identity while satisfying every relevant Theme 2 requirement, so that the team can build it within the hackathon timeline and deliver a convincing 10-minute presentation plus 5-minute Q&A.

**Required agents.** SAP explicitly mandates these specialized agents: Skills Discovery Agent, Market Intelligence Agent, Learning Pathway Agent, Inclusive Matching Agent, Employer Readiness Agent, Bias Audit Agent, and Human-in-the-Loop, coordinated by a central Career Orchestrator. For each, define the real responsibilities, inputs, outputs, tools, decision boundaries, communication protocol, and failure behaviour. Do not rename existing ShiftSure modules as agents; explain how each agent does genuine reasoning and how it collaborates with the others.

**Deterministic versus agentic boundary.** Clearly separate autonomous agent reasoning from deterministic business logic. The following must remain deterministic, independently verifiable, and auditable: mathematical optimization (use a genuine constraint solver), eligibility and certification validation, safety constraints, idle-hours and workforce calculations, fairness metrics, counterfactual tests, and any authoritative decision. LLMs must never fabricate workforce data, calculate authoritative metrics, override hard constraints, or approve employment decisions. Human managers hold final approval.

**Preserve from the PRD unless a change is genuinely required by the handbook:** the simulated workforce dataset, local execution, real constraint-based optimization, three-way allocation comparison (internal reallocation, external hiring, reskilling), training and hiring cost analysis, fairness analytics and counterfactual evaluation, evidence-grounded explanations, the worker correction workflow, manager approval, and persistent audit history. Where the PRD and handbook conflict, or where either is silent on something the architecture needs, list the ambiguity explicitly rather than inventing a requirement.

**SAP ecosystem.** Incorporate SAP SuccessFactors, SAP Talent Intelligence Hub, SAP Joule Agents, SAP BTP, SAP Build, SAP Generative AI Hub, and SAP Learning Hub Student Edition where they add value. For each, classify it as a live integration, a simulated integration, a conceptual integration, or a future possibility. Never imply a live SAP connection that does not exist in the prototype.

**Demonstration.** Define one end-to-end persona: a worker displaced by automation who is assessed for existing skills, compared against internal opportunities and market demand, given personalized training, matched to suitable roles, checked for fairness and employer readiness, and presented to a human manager for approval. Keep the demo within the handbook's time format and make every step visibly driven by a distinct agent.

**Deliver the following, in this order:**
1. Gap analysis between the handbook and the PRD, with ambiguities listed
2. System architecture and orchestration flow under the Career Orchestrator, including shared state, memory, and agent-to-agent messaging
3. Agent specifications (one per mandated agent, plus the orchestrator)
4. Structured input and output data contracts for each agent
5. Deterministic core: solver formulation, validation rules, fairness metrics, and counterfactual method
6. Integration strategy with SAP components, each labelled by integration status
7. Security, privacy, and human escalation safeguards
8. Technology stack and local execution setup
9. Prioritised implementation plan fitted to the hackathon timeline, with scope cuts identified
10. Testing strategy covering agent behaviour, solver correctness, and fairness checks
11. Detailed demo script mapped to the presentation and Q&A timing

Avoid unnecessary complexity, unrelated features, and superficial agent implementations. Prioritise technical feasibility, business viability, inclusivity, explainability, responsible AI, and demonstrable innovation. Where I have not given enough detail, make the architecture assumptions explicit and label them as assumptions, then continue.