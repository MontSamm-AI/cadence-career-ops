# System Architecture Overview

## Cadence Career Ops — Architecture Reference

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          CADENCE CAREER OPS                                   │
│                                                                               │
│  ┌─────────────────┐    CDP/WebSocket    ┌──────────────────────────────────┐│
│  │  Windows Chrome  │◄──────────────────►│  WSL/Ubuntu — Cadence Agent      ││
│  │  (Port 9222)     │                    │                                   ││
│  │                  │                    │  OpenClaw Framework               ││
│  │  LinkedIn UI     │                    │  ├── cadence-profissional (agent) ││
│  │  Easy Apply      │                    │  ├── 14 Python Skills             ││
│  │  Authenticated   │                    │  ├── State files (JSON)           ││
│  │  session         │                    │  ├── Telegram gate                ││
│  └─────────────────┘                    │  └── HTML Dashboard               ││
│                                          └───────────────┬──────────────────┘│
│                                                          │                    │
│                                              Telegram / SSH / n8n webhooks   │
│                                                          │                    │
│                                          ┌───────────────▼──────────────────┐│
│                                          │  VPS — Hetzner (5.78.144.113)    ││
│                                          │  Docker Swarm — 14 services      ││
│                                          │                                   ││
│                                          │  ├── PostgreSQL (career_tracker)  ││
│                                          │  ├── n8n (workflows)              ││
│                                          │  ├── OpenClaw VPS (agent)         ││
│                                          │  ├── Traefik (reverse proxy)      ││
│                                          │  ├── Evolution API (WhatsApp)     ││
│                                          │  ├── Portainer                    ││
│                                          │  ├── Redis                        ││
│                                          │  └── Paperclip                    ││
│                                          └──────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Architectural Decision: Hybrid Model

The most important design decision in this system:

**Local/WSL = hands and eyes (executor)**
- Chrome browser via CDP — the only way to interact with LinkedIn's authenticated session
- Easy Apply form filling, screenshot capture, file uploads
- LinkedIn posting with real user profile
- Visual review and inspection

**VPS = brain and memory (persistence)**
- PostgreSQL as the canonical CRM for career data
- n8n for automated workflows (Gmail intake, notifications, schedulers)
- Docker Swarm for production-grade service orchestration
- Long-term memory, dashboards backed by canonical state

### Why This Split?

LinkedIn requires an authenticated browser session. Server-side automation would require replicating login cookies, handling 2FA, and managing session state — a fragile, policy-violating approach. The local browser with the user's real profile is the only reliable path.

The VPS does what persistent infrastructure does well: long-running jobs, scheduled tasks, durable storage, observability.

---

## Component Map

### 1. OpenClaw Agent Framework (Local)

OpenClaw is the agent runtime. It provides:
- LLM routing (primary: GPT-5.4, fallbacks: Claude, Groq, OpenRouter)
- Tool calling and skill orchestration
- Telegram channel integration
- Workspace state management
- Multi-agent coordination

**Agent: `cadence-profissional`**
- Workspace: `/path/to/workspace-linkedin`
- Identity: "Cadence Profissional" — career operations specialist
- Primary channel: Telegram bot (@cadence_profissional_bot)
- Tools: browser (CDP), exec, read/write, message, canvas

### 2. Chrome CDP Bridge (Windows ↔ WSL)

- Chrome runs on Windows with `--remote-debugging-port=9222`
- WSL accesses it at `http://127.0.0.1:9222`
- Playwright library connects to the existing Chrome instance
- All LinkedIn interactions use the user's real authenticated session

### 3. Python Skills Layer

14 specialized scripts in `scripts/skills/`:

```
Discovery layer:
  browser_recon.py       → Enumerate open Chrome tabs
  linkedin_job_search.py → Search LinkedIn for jobs via browser
  job_detail_extractor.py → Extract structured job data from pages
  browser_probe.py       → General CDP browser operations

Apply layer:
  application_guard.py        → Pre-submission safety validation
  linkedin_easy_apply_runner.py → Full Easy Apply automation
  auto_apply_lib.py           → Shared utilities and data models
  auto_apply_loop.py          → Orchestrates the apply queue
  tab_hygiene.py              → Post-apply browser tab management

ATS-specific probes:
  cpqd_assisted_probe.py  → CPQD ATS probe
  cpqd_fill_prepare.py    → CPQD form preparation
  hubxp_probe.py          → HubXP ATS probe
  hubxp_probe_wait.py     → HubXP with wait strategy

Visualization & notification:
  render_applications_dashboard.py → Generate HTML dashboard
  telegram_notifier.py             → Telegram alerts and messages
```

### 4. State & Persistence (Local)

```
state/
├── applications_index.json      → Master record of all applications
├── follow_up_tracker.json       → Follow-up schedule and status
├── auto_apply_queue.json        → Queue of jobs pending application
├── auto_apply_rules.json        → Scoring thresholds and batch limits
├── application_profile.json     → Candidate profile, CV mapping, compensation
├── compensation_reference.json  → Salary targets by track and role
├── linkedin_posts_index.json    → Canonical LinkedIn post index
└── application_stage_overrides.json → Gmail-derived stage corrections
```

### 5. CV Engine (Windows/OneDrive)

```
cv_base.yaml                → Master YAML profile with all facts/metrics
cv_branded_generator.py     → Converts YAML + preset → branded HTML → PDF
cv_templates/
└── cv_branded.html.j2      → Jinja2 HTML template
output/pdf/
└── CV_Sami_[preset]_[role]_[date].pdf  → Generated CVs (24 variants)
```

### 6. VPS Services (Docker Swarm)

| Service | Purpose | URL |
|---|---|---|
| `traefik` | Reverse proxy + TLS | (internal) |
| `postgres` | Career CRM + all app data | postgres:5432 (internal) |
| `redis` | Cache and queues | redis:6379 (internal) |
| `n8n_editor` | Workflow automation | n8n.example.com |
| `n8n-workers` | Workflow execution | (internal) |
| `openclaw_gateway` | VPS agent runtime | openclaw.example.com |
| `portainer` | Container management | portainer.example.com |
| `evolution` | WhatsApp API | evolution.example.com |
| `paperclip` | Document management | paperclip.example.com |
| `pgadmin` | DB admin interface | pgadmin.example.com |
| `redisinsight` | Redis management | redis.example.com |
| `alianca_api` | Custom FastAPI backend | api.example.com |

---

## Data Flow: Easy Apply Pipeline

```
1. DISCOVERY
   linkedin_job_search.py → browser → LinkedIn search results
   ↓ (collect job cards)
   
2. QUALIFICATION  
   job_detail_extractor.py → open job page → extract details
   ↓ (4D scoring, filter by threshold)
   
3. QUEUE
   auto_apply_queue.json → ordered by priority score
   ↓
   
4. PRE-GATE
   application_guard.py → score check, rate limit, hours, prohibited claims
   ↓ (pass or block)
   
5. EASY APPLY
   linkedin_easy_apply_runner.py:
   - Open/find job page via CDP
   - Click "Candidatura Simplificada"
   - Choose email, phone
   - Select CV preset
   - Answer form questions (salary, years exp, booleans)
   - Advance through steps
   - Detect confirmation
   ↓
   
6. HUMAN GATE (Telegram)
   → Send screenshot + summary to Sami
   → Wait for explicit "confirmar [ID]" response
   → Only then classify as "applied"
   ↓
   
7. TRACKING
   applications_index.json + follow_up_tracker.json
   artifacts/applications/applied/[job_id].json
   ↓
   
8. DASHBOARD
   render_applications_dashboard.py → HTML with evidence + follow-up queue
```

---

## Data Flow: CV Generation

```
1. cv_base.yaml — Structured YAML with:
   - Personal facts and metrics
   - Experience timeline
   - Skills with truthful defaults
   - Compensation ranges by track
   - CV preset mappings

2. cv_branded_generator.py:
   - Load YAML profile
   - Apply preset (clt-ptbr, master-en, upwork-en, cpqd, etc.)
   - Render Jinja2 HTML template
   - Convert HTML → PDF via WeasyPrint/Playwright

3. Output: CV_Sami_[preset]_[role]_[date].pdf
   - Stored in output/pdf/ and artifacts/share/
   - Referenced in application_profile.json for auto-selection
```

---

## Security Architecture

```
HUMAN GATE (mandatory)
├── Every application requires explicit Telegram approval
├── Gate: "confirmar [job_id]" message from Sami
└── No autonomous final submission

RATE LIMITING
├── Max 5 applications/day
├── 30-120s random delay between actions
└── No-apply hours: 23:00-07:00 BRT

SCORE GATE
├── Minimum 65/100 to queue for application
└── 4D scoring: fit + stretch + strategic + value

CLAIM VERIFICATION
├── All answers cross-checked against cv_base.yaml
├── Prohibited claims checked at runtime
└── "Never lie" rule enforced in application_guard.py

CREDENTIAL HANDLING
├── Tokens in .env.local (gitignored)
├── No secrets in tracked files
└── API keys in OpenClaw config (separate from this repo)
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Agent framework | OpenClaw |
| Primary LLM | GPT-5.4 (via OpenAI OAuth) |
| Fallback LLMs | Claude Sonnet, Groq Llama 3.3, OpenRouter Qwen |
| Browser automation | Playwright (CDP to existing Chrome) |
| Python runtime | Python 3.11, venv at `~/.venv/jobhunter` |
| State storage (local) | JSON files |
| State storage (VPS) | PostgreSQL 16 |
| Workflow automation | n8n |
| Notifications | Telegram Bot API |
| VPS runtime | Docker Swarm on Debian 13 (Hetzner) |
| Reverse proxy | Traefik with Let's Encrypt |
| CV templating | Jinja2 + WeasyPrint |
| Job search API | JobSpy library + LinkedIn CDP |
