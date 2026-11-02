# ShiftSure: Backend & Deterministic Optimization Core
## Detailed Implementation Plan (Phase 1)
**Document Status:** Ready for Review  
**Tone & Style:** Plain English (No Overuse of Technical Jargon)  
**Next Action:** Awaiting User "GO" to start coding

---

## 1. What This Stage Is (The "Brain and Rulebook")

Before building fancy user interfaces or AI chat screens, we need to build the core engine of ShiftSure. 

Think of this like building the engine of a car before putting on the paint and dashboard:
* It holds the records of our factory workers (their skills, safety licenses, and hours).
* It simulates what happens when machines take over human tasks (automation disruption).
* It uses a proven mathematical solver to find the best way to move displaced workers into new jobs, making sure **no safety rules are broken**, **costs are kept low**, and **work is shared fairly**.

---

## 2. The Factory & Workforce Setup (Simulated Data)

We will seed a realistic simulated factory environment so everything we test feels like a real manufacturing plant:

* **The Factory:** *Bengaluru Smart Auto Components Plant* (Plant BLR-01).
* **The People:** 60 simulated workers across 3 working shifts (Morning, Evening, Night).
* **The 3 Production Lines:**
  1. **Packaging Line (Line 03):** The line where automation happens. When new automated packing arms are turned on, 80% of manual work vanishes, leaving 5 to 8 workers with no tasks.
  2. **Assembly Line (Line 01):** Has open tasks requiring manual dexterity and machine operation.
  3. **Quality & Maintenance Line (Line 02):** Has open technical inspection tasks.
* **Our Key Demonstration Person:**
  * **Name:** Priya Sharma (Worker ID: `W-104`)
  * **Role:** Senior Assembly & Packaging Specialist
  * **Situation:** Her packing line is automated. She is at risk of having 32 hours of idle time this week.
  * **The Solution:** She already has 75% of the skills needed to run the new robotic quality station. She just needs a short 8-hour safety training bridge to be 100% qualified.

---

## 3. Strict Safety & Validation Rules (Non-Negotiable)

In a factory, placing the wrong person on a dangerous machine causes accidents. That is why **an AI is never allowed to guess assignments**. Everything must pass through strict, hard-coded rules:

1. **Safety License Check:** If a task requires a "Robotics Cell Safety Certificate," a worker *cannot* be assigned to it unless they have that certificate or complete the authorized training course first.
2. **No Double-Booking:** A worker cannot be assigned to two tasks at the same time.
3. **Shift Consistency:** Morning shift workers are not thrown into night shifts without authorization.
4. **Capacity Limits:** A worker cannot be given more hours than their weekly limit (e.g., 40 hours maximum).
5. **Supervisor Safety Ratio:** A line cannot take more than 8 workers per supervisor.

---

## 4. How the Mathematical Solver Works (In Plain English)

Instead of relying on AI guesses, we use **Google OR-Tools** (a proven mathematical optimization solver used by airlines and logistics companies worldwide).

### What the Solver Does:
1. It looks at all workers who lost their work due to automation.
2. It looks at all the open jobs across other lines in the factory.
3. It checks all safety rules and required skills.
4. It tests thousands of possible combinations in a fraction of a second.
5. It produces **3 distinct plans** so plant managers can see the trade-offs:

| Plan Option | How It Decides | The Catch / Trade-Off |
| :--- | :--- | :--- |
| **Plan 1: Supervisor Baseline** | Traditional "gut-feel" method: assigns the most senior workers first, ignores training. | Leaves newer workers completely idle and leaves complex tasks unfilled. |
| **Plan 2: Cost-Focused Plan** | Pure math focused only on lowest cost and maximum machine output. | Works well for the business, but unfairly dumps almost all idle hours onto contract workers. |
| **Plan 3: ShiftSure Fair-Balanced Plan** | Balances high output with fairness: spreads downtime evenly and funds quick training bridges for workers who are close to qualifying. | Achieves 92%+ job coverage, saves internal workers from layoffs, and treats all shifts fairly. |

---

## 5. What Metrics the Engine Calculates

For every plan generated, the engine calculates clear, undeniable numbers:
* **Idle Hours Avoided:** How many wasted worker hours were saved and turned into productive work.
* **Internal Fill Rate:** What percentage of open jobs were filled by our own workers instead of having to hire from outside.
* **Money Saved:** 
  * Cost to train an existing worker: ~₹4,500 – ₹22,500.
  * Cost to recruit and hire someone new from the market: ~₹1,85,000.
  * Net savings calculated directly.
* **Fairness Disparity Check:** Compares different groups (like permanent staff vs. contract staff) to guarantee no group gets stuck with more than a 10% difference in downtime.

---

## 6. Project Layout (Where Files Will Live)

We will create a clean, organized `backend/` directory:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # The web API server (FastAPI)
│   ├── database.py          # Local SQLite database setup
│   ├── data/
│   │   ├── seed_data.py     # Generates the 60 workers, tasks, and lines
│   │   └── courses.py       # SAP Learning Hub course catalog
│   ├── models/
│   │   ├── schemas.py       # Clear data formats for Workers, Tasks, and Plans
│   │   └── db_models.py     # Database tables for saving history
│   ├── core/
│   │   ├── rules.py         # Hard safety & certification checks
│   │   ├── solver.py        # Google OR-Tools math optimizer (the 3 plans)
│   │   ├── fairness.py      # Calculations for idle time gaps & fairness
│   │   └── counterfactual.py# "What-if" tests (proves gender/contract status doesn't bias the result)
│   └── routers/
│       ├── workers.py       # View worker profiles and submit skill corrections
│       ├── scenarios.py     # Create automation disruptions
│       └── plans.py         # Run solver, view 3-way comparisons, and approve plans
├── tests/
│   ├── test_rules.py        # Confirms safety rules cannot be broken
│   ├── test_solver.py       # Confirms solver generates valid, realistic plans
│   └── test_fairness.py     # Confirms math behind fairness scores
└── requirements.txt         # List of Python packages needed
```

---

## 7. How the Web API Will Work (Endpoints)

The backend provides simple web connections for the system:
1. `GET /api/workers`: Get the list of all factory workers.
2. `GET /api/workers/W-104`: View Priya Sharma's profile, current line, and skills.
3. `POST /api/scenarios`: Create a disruption (e.g., "Line 3 is automated by 80%").
4. `POST /api/scenarios/{id}/solve`: Run the math solver and return the 3 plan options.
5. `GET /api/plans/{id}/compare`: Compare Plan 1, Plan 2, and Plan 3 side-by-side.
6. `POST /api/plans/{id}/approve`: Manager officially signs off on the chosen plan.
7. `POST /api/workers/{id}/correct-skill`: Worker requests an update to their skills record.

---

## 8. Verification & Testing Steps (Before Moving to Agents or UI)

Before we touch any frontend screens or AI agents, we run automated checks:
1. **Safety Test:** We try to force the solver to put an uncertified worker on a robotic line. *Expected: Solver strictly refuses.*
2. **Infeasibility Test:** We ask the solver to fill 100 jobs with only 5 workers. *Expected: Solver cleanly reports "Not enough capacity", without making up fake people.*
3. **Fairness Test:** We run the "What-If" check (flipping Priya's employment status from contract to permanent). *Expected: Her assignment remains identical, proving the math is free from unfair bias.*

---

## 9. What I Need From Your Side

To get started on this stage, please review this plan and let me know:

1. **Virtual Environment Approval:**  
   Is it okay to set up a standard Python virtual environment inside `/home/kishanravi/SAP/backend/venv`?
2. **Python Version Check:**  
   Your machine runs Linux with Python 3.14 / 3.13 available. Standard packages (`ortools`, `fastapi`, `uvicorn`, `pydantic`) will be installed there.
3. **Your Final "GO":**  
   Whenever you are satisfied with this plan, simply reply with **"GO"**, and I will begin creating the files and writing the code!
