# Changelog

All notable changes to Cadence Career Ops are documented here.

Format: [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`

---

## [Unreleased] — v0.2 (In Progress)

### In Progress
- PostgreSQL CRM sync (local JSON → `career_tracker` on VPS)
- n8n Gmail intake workflow (Gmail → application stage overrides)
- VPS dashboard backed by canonical Postgres state

### Planned
- Application stage reconciliation from Gmail evidence
- Automated follow-up drafts (human-gated)
- Weekly digest report via Telegram

---

## [0.1.0] — 2026-04-13 (Initial Public Release)

### Added

**Core Apply Pipeline**
- `linkedin_easy_apply_runner.py` — Full LinkedIn Easy Apply automation (604 lines)
  - Multi-step form navigation
  - Email, phone, CV auto-selection
  - Salary-aware compensation answers (BRL and USD, multiple tracks)
  - Years of experience auto-fill (AI: 2yr, automation: 3yr, IT: 4yr)
  - Boolean, combobox, radio group answering
  - Already-applied detection
  - Confirmation detection (PT-BR and EN)
- `auto_apply_loop.py` — Queue orchestrator
- `auto_apply_lib.py` — Shared utilities, `CandidateProfile`, `CompensationReference` data models

**Job Discovery**
- `linkedin_job_search.py` — LinkedIn job search via Chrome CDP
  - Multi-preset search (core_br, fresh_br)
  - Easy Apply availability detection
  - Priority scoring and queue management
- `job_detail_extractor.py` — Structured job data extraction
- `browser_recon.py` — Chrome tab reconnaissance and classification

**Safety & Control**
- `application_guard.py` — Pre-submission gate (score, rate limit, hours, claims)
- `tab_hygiene.py` — Post-apply browser tab management
- `telegram_notifier.py` — Structured Telegram notifications with message types

**ATS Probes**
- `cpqd_assisted_probe.py` — CPQD ATS-specific probe
- `cpqd_fill_prepare.py` — CPQD form preparation
- `hubxp_probe.py` / `hubxp_probe_wait.py` — HubXP ATS probes

**Tracking & Dashboard**
- `render_applications_dashboard.py` — HTML dashboard from local state
  - Dark theme professional UI
  - Follow-up queue panel
  - Evidence-based certainty scoring
  - Application stage overrides support

**CV Engine**
- `cv_branded_generator.py` — YAML → branded PDF generation
- 8 presets: clt-ptbr, master-en, master-ptbr, master-en-1p, master-ptbr-1p, upwork-en, automation-ptbr, cpqd
- 24 CV variants generated across all presets

**Configuration & Templates**
- `system/config/openclaw.example.json` — OpenClaw config template
- `system/templates/cv_base.example.yaml` — CV profile template with annotations
- `config.json` — Operational thresholds (scoring, rate limits, categories)

**Documentation**
- `README.md` + `README.pt-BR.md`
- `docs/architecture/SYSTEM_OVERVIEW.md` — Full architecture with ASCII diagrams
- `docs/guides/INSTALLATION.md` — Step-by-step setup guide
- `docs/guides/CV_SYSTEM.md` — CV engine reference
- `docs/operations/CAPABILITY_MAP.md` — Proven vs. planned capabilities
- `docs/showcase/RESULTS.md` — Evidence and metrics
- `planning/ROADMAP.md` — v0.1 → v1.0 roadmap
- `planning/ARCHITECTURE_DECISIONS.md` — 6 ADRs with rationale

### Operational Results at Release
- 40+ applications tracked
- 24 CV variants generated
- 1 LinkedIn post published end-to-end
- 14-service Docker Swarm running on Hetzner VPS
- 0 false claims submitted

---

## Pre-History (Internal Development Log)

| Date | Milestone |
|---|---|
| 2026-04-06 | First browser_recon.py, telegram_notifier.py, application_guard.py |
| 2026-04-06 | CADENCE_MISSION_BRIEFING.md — operational foundation |
| 2026-04-07 | job_detail_extractor.py, linkedin_job_search.py |
| 2026-04-08 | First Easy Apply proven in live session |
| 2026-04-09 | auto_apply_lib.py, auto_apply_loop.py, cv_branded_generator.py |
| 2026-04-09 | 24 CV variants generated |
| 2026-04-10 | Application tracking system, follow-up tracker |
| 2026-04-10 | Gmail/n8n/CRM architecture defined |
| 2026-04-11 | LinkedIn post published end-to-end |
| 2026-04-11 | CADENCE_OPERATIONAL_CAPABILITY_MAP written |
| 2026-04-13 | render_applications_dashboard.py, Gmail/Calendar access |
| 2026-04-13 | CLAUDE_DOSSIER_REPOSITORY_STRATEGY — repository planning |
| 2026-04-13 | **Repository created and published** |
