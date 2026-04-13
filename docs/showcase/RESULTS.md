# Results & Evidence

## Cadence Career Ops — What's Actually Running

---

## Operational Results (April 2026)

### Applications

| Metric | Value |
|---|---|
| Total applications tracked | 40+ |
| Applications via Easy Apply automation | Majority |
| ATS portals (external apply) | Multiple |
| Days of operation | ~7 active days |
| Max applications per day (enforced) | 5 |
| False claims submitted | 0 |
| Human gate violations | 0 |

### CV Generation

| Metric | Value |
|---|---|
| Total PDF CVs generated | 24 |
| Unique presets | 8 (clt-ptbr, master-en, master-ptbr, upwork-en, automation-ptbr, cpqd, master-en-1p, master-ptbr-1p) |
| Languages | Portuguese (BR) + English |
| Markets targeted | Brazil CLT, Brazil PJ, International Remote, Freelance/Upwork, Research |

### LinkedIn Content

| Metric | Value |
|---|---|
| Posts published (automated flow) | 1 (proven end-to-end) |
| Post index entries | Multiple (tracking history) |
| Positioning strategy | Applied AI automation, agents, n8n, production delivery |

### Infrastructure

| Metric | Value |
|---|---|
| Docker Swarm services running | 14 (all 1/1) |
| VPS uptime | Continuous |
| Python skills implemented | 14 scripts |
| State files maintained | 7 JSON files |
| Total lines of operational Python code | 2,500+ |

---

## Technical Evidence

### Easy Apply — Proven Capabilities

The LinkedIn Easy Apply runner (`linkedin_easy_apply_runner.py`) has been proven to handle:

- ✅ Multi-step forms (up to 8 steps)
- ✅ Email selection from dropdown
- ✅ Phone auto-fill (E.164 format)
- ✅ CV selection from uploaded files
- ✅ Yes/No boolean questions
- ✅ Combobox (select) questions
- ✅ Radio group questions
- ✅ Numeric text inputs (years, salary)
- ✅ Salary/compensation fields (BRL and USD, multiple units)
- ✅ PT-BR form detection and Portuguese answers
- ✅ Already-applied detection (prevents duplicates)
- ✅ Confirmation page detection (PT-BR and EN patterns)
- ✅ Blocked question detection (work authorization, visa, disability)

### Scoring System — What Gets Through

The 4D scoring system + rate gate ensures:
- Only roles matching AI automation, n8n, workflow, LLM, GenAI, agentic focus
- Roles blocked: QA automation, test automation, RPA, SCADA, pure ML/data science, frontend/backend generic
- Minimum score 65/100 to enter the queue
- Manual review threshold 55-64
- Auto-block below 30

### CV Engine — Accuracy

Every CV variant is generated from a single `cv_base.yaml` source of truth:
- All metrics are real and verifiable
- No inflated years of experience
- Prohibited claims checked at both generation time and submission time
- Experience anchored: AI/applied AI from 2024 (2 years), automation 3 years, IT broadly 4 years

---

## Architecture Evidence

### Hybrid Model (Proven)

The architectural split between local (browser executor) and VPS (persistent brain) was validated by operational experience:

- LinkedIn Easy Apply **requires** an authenticated browser session
- Session cannot be reliably replicated server-side without policy violations
- VPS services (n8n, Postgres) run continuously without the browser constraint
- Local agent can pause/resume without affecting VPS persistence

### Chrome CDP Integration (Proven)

The CDP bridge at `127.0.0.1:9222` has been used for:
- Tab enumeration and classification
- Navigation to job pages
- Element interaction (clicking, filling, selecting)
- Screenshot capture
- File upload via file chooser
- Multi-context handling

---

## What This Demonstrates as a Portfolio Project

### Applied AI Engineering

- Real LLM integration (GPT-5.4, Claude, Groq as fallbacks)
- Agent framework usage (OpenClaw) with workspace and memory management
- Telegram as a human-in-the-loop channel
- Context-aware decision making (salary tracks, CV selection, form interpretation)

### Production Python

- 14 specialized scripts with clean separation of concerns
- Shared library pattern (`auto_apply_lib.py`)
- Proper error handling and retry logic
- Artifact preservation pattern
- State management with JSON + overrides layer

### Browser Automation

- CDP vs. Selenium/standard Playwright: using CDP against existing session
- Resilient element finding (multiple selector strategies)
- Form interaction at scale (comboboxes, radios, text inputs, file uploads)
- Confirmation detection via text pattern matching

### Infrastructure

- Docker Swarm: 14-service production stack
- Traefik: automatic TLS, subdomain routing
- PostgreSQL: schema design for career tracking CRM
- n8n: workflow automation with Google OAuth
- Self-hosted, fully owned infrastructure

### System Design

- Hybrid architecture: right tool for each layer
- State machine for application lifecycle
- Audit trail via artifacts + tracker + dashboard
- Security-first design (gates, rate limits, claim validation)
