# Cadence Operational Capability Map

## Current Capabilities — April 2026

---

## 1. What's Proven Operational

### 1.1 LinkedIn Easy Apply

**Status**: ✅ CONFIRMED_OPERATIONAL

The full Easy Apply flow has been proven in live applications:

- Navigation to job pages via CDP
- Detection and clicking of "Candidatura Simplificada" button
- Email selection (defaults to career-specific email)
- Phone auto-fill
- CV selection from uploaded files (auto-selects based on job context)
- Multi-step form completion:
  - Salary/compensation questions (salary-aware, track-intelligent)
  - Years of experience (AI: 2yr, Automation: 3yr, IT: 4yr)
  - Yes/No boolean questions (automation, remote, tools)
  - Combobox and radio group answering
- Step advancement (Avançar → Revisar → Enviar)
- Confirmation detection (Portuguese and English patterns)
- Already-applied detection (prevents duplicate submissions)
- Tab hygiene post-apply
- Artifact preservation (JSON per application)

**Key files**: `skills/linkedin_easy_apply_runner.py` (604 lines), `skills/auto_apply_lib.py`

### 1.2 Job Discovery and Scoring

**Status**: ✅ CONFIRMED_OPERATIONAL

- LinkedIn job search via real browser (no scraping API, direct CDP)
- Multi-preset queries (core_br, fresh_br, international)
- Job card collection and deduplication
- Easy Apply availability detection
- Already-applied detection
- Priority scoring based on title/role keywords
- Queue management with persistence

**Key files**: `skills/linkedin_job_search.py`, `skills/job_detail_extractor.py`

### 1.3 Application Tracking

**Status**: ✅ CONFIRMED_OPERATIONAL

- Canonical applications index (`state/applications_index.json`)
- Follow-up tracker with scheduled dates
- Auto-apply queue with status lifecycle
- Application stage overrides (from Gmail evidence)
- HTML dashboard rendered from state (dark theme, professional UI)
- Evidence tracking (artifact, queue, index, email confirmation)
- Certainty scoring per application (high/medium/low)

**Key files**: `skills/render_applications_dashboard.py`, `state/applications_index.json`

### 1.4 Human Approval Gate

**Status**: ✅ CONFIRMED_OPERATIONAL

- Pre-submission safety validation (application_guard.py)
- Score gate: minimum 65/100
- Rate limit: max 5/day
- Operating hours: 07:00-23:00 BRT
- Prohibited claims check (runtime)
- Blocked title terms (QA automation, RPA, etc.)
- Telegram notification with job details + screenshot before any submit
- Explicit "confirmar [job_id]" required from human

**Key files**: `skills/application_guard.py`, `skills/telegram_notifier.py`

### 1.5 CV Generation

**Status**: ✅ CONFIRMED_OPERATIONAL

- YAML-driven profile system
- 8 named presets for different markets and roles
- HTML template with Jinja2 rendering
- PDF export
- 24 variants generated and preserved
- Auto-selection logic in Easy Apply based on job context
- Compensation-aware (salary targets by track)

**Key files**: `cv-engine/cv_branded_generator.py`, `system/templates/cv_base.example.yaml`

### 1.6 LinkedIn Content Posting

**Status**: ✅ CONFIRMED_OPERATIONAL (1 post)

- Topic selection and editorial strategy
- Image curation for technical positioning
- Copy writing (English, professional tone)
- Alt text generation
- Browser-based publication (real UI, authenticated)
- Artifact preservation (image file, post index entry)
- Publication link captured

**Key files**: `state/linkedin_posts_index.json`, `artifacts/linkedin/`

### 1.7 VPS Infrastructure

**Status**: ✅ RUNNING

- 14 Docker Swarm services (all 1/1 replicas)
- PostgreSQL with career_tracker schema
- n8n with Google OAuth credentials
- OpenClaw VPS agent (Groq as primary LLM)
- Full reverse proxy (Traefik + TLS)
- WhatsApp API (Evolution)

---

## 2. Implemented, Validation Pending

### 2.1 PostgreSQL CRM Sync

**Status**: 🔄 IMPLEMENTED_NOT_VALIDATED

- Schema defined and applied (`career.job_applications`, `career.inbound_email_events`)
- Tables exist in `career_tracker` database on VPS
- Local JSON → Postgres sync: partial implementation
- Full bidirectional sync: not yet proven end-to-end

### 2.2 n8n Gmail Intake

**Status**: 🔄 IMPLEMENTED_NOT_VALIDATED

- Architecture defined: Gmail → n8n → Postgres → local state
- n8n credentials for Google OAuth: configured
- Workflow: blueprint exists, not fully deployed
- Gmail classification (confirmed, interview, rejection, assessment): logic defined

### 2.3 ATS-Specific Probes (CPQD, HubXP)

**Status**: 🔄 IMPLEMENTED_NOT_VALIDATED

- Scripts exist: `cpqd_assisted_probe.py`, `hubxp_probe.py`
- Tested for specific application sessions
- Not generalized or battle-tested across multiple ATS sessions

---

## 3. Planned / Backlog

### 3.1 Multi-platform Discovery

**Status**: 📋 PLANNED

- Indeed integration
- Gupy.io integration
- Catho/InfoJobs probes
- Workana for freelance

### 3.2 Interview Preparation Automation

**Status**: 📋 PLANNED

- Company research from job context
- Interview question bank generation
- Briefing documents from CRM data

### 3.3 Dashboard Backed by Postgres

**Status**: 📋 PLANNED

- Current dashboard reads local JSON
- Target: VPS-hosted dashboard backed by canonical Postgres state
- Accessible at `dashboard.example.com`

### 3.4 Automated Follow-up

**Status**: 📋 PLANNED

- n8n workflow: detect no-response after 7 days → trigger follow-up draft
- Human-in-the-loop: Telegram approval before sending

### 3.5 Replication Guide

**Status**: 📋 PLANNED

- Full step-by-step guide to replicate on a new machine
- Docker-based self-contained demo environment

---

## 4. Sources of Truth (Current)

| Domain | File |
|---|---|
| Applications (tactical) | `state/applications_index.json` |
| Follow-up schedule | `state/follow_up_tracker.json` |
| Apply queue | `state/auto_apply_queue.json` |
| LinkedIn posts | `state/linkedin_posts_index.json` |
| Compensation targets | `state/compensation_reference.json` |
| Candidate profile | `state/application_profile.json` |
| Stage overrides | `state/application_stage_overrides.json` |
| Long-term memory | `MEMORY.md` in workspace-linkedin |
| Session notes | `memory/YYYY-MM-DD.md` |
| Architecture | `docs/architecture/SYSTEM_OVERVIEW.md` |

---

## 5. Scoring System

### 4D Job Score

Each job gets a composite score across four dimensions:

| Dimension | Weight | Description |
|---|---|---|
| **Fit** | Primary | How well the role matches core competencies |
| **Stretch** | Secondary | Growth potential and learning opportunity |
| **Strategic** | Tertiary | Alignment with long-term career trajectory |
| **Value** | Quaternary | Compensation, benefits, company quality |

**Thresholds** (from `config.json`):
```
auto_apply_threshold: 75   → Auto-queue for application
review_threshold: 55        → Flag for manual review
block_threshold: 30         → Auto-reject
min_fit_score: 60           → Minimum to even consider
```

**Category Classification**:
- `CORE_FIT`: fit ≥ 70 → auto-approve
- `STRATEGIC_STRETCH`: fit ≥ 45, strategic ≥ 60 → requires review
- `HIGH_STRETCH_HIGH_VALUE`: fit ≥ 30, strategic ≥ 75 → requires referral
- `BLOCKED`: fit < 30 → auto-reject

---

## 6. Operational Constraints

| Constraint | Value | Rationale |
|---|---|---|
| Max apps/day | 5 | LinkedIn safety + quality over quantity |
| Min delay between actions | 30s | Avoid bot detection |
| Max delay | 120s | Natural browsing pace |
| No-apply hours | 23:00-07:00 BRT | Avoid suspicious off-hours activity |
| Min score for apply | 65/100 | Signal-to-noise quality gate |
| Screenshot required | Yes | Audit trail for every application |
