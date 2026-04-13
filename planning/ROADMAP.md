# Roadmap

## Cadence Career Ops — Development Roadmap

---

## v0.1 — Foundation (✅ Current)

**Theme**: Prove the system works end-to-end on a single machine.

### Completed
- [x] LinkedIn Easy Apply runner (604-line production script)
- [x] Job discovery via Chrome CDP + LinkedIn
- [x] 4D scoring system with thresholds and categories
- [x] Human approval gate via Telegram
- [x] Application tracking (JSON index + follow-up tracker)
- [x] HTML dashboard rendered from local state
- [x] CV generation engine (YAML → PDF, 24 variants)
- [x] LinkedIn content posting (end-to-end proven)
- [x] VPS infrastructure (14 Docker Swarm services)
- [x] OpenClaw agent with workspace and Telegram channel
- [x] Application guard (score gate, rate limit, prohibited claims)
- [x] Tab hygiene post-apply
- [x] ATS-specific probes (CPQD, HubXP)
- [x] Telegram notifier with structured message formats
- [x] Chrome CDP bridge (Windows Chrome ↔ WSL agent)

---

## v0.2 — Persistence & Sync (🔄 Next)

**Theme**: Make the VPS the canonical brain. Connect local ↔ VPS reliably.

### In Progress
- [ ] PostgreSQL CRM sync (local JSON → Postgres `career_tracker`)
- [ ] n8n Gmail intake workflow (Gmail → n8n → Postgres → state override)
- [ ] Gmail classification layer (confirmed/interview/rejection/assessment)

### Planned for v0.2
- [ ] Application stage reconciliation (Gmail evidence → `application_stage_overrides.json` auto-update)
- [ ] n8n Telegram webhook for gate approvals
- [ ] VPS-side scheduled job discovery (daily at 08:00 and 18:00 BRT)
- [ ] Dashboard v2: served from VPS, backed by Postgres canonical state
- [ ] Centralized posting cadence (topic calendar in Postgres)
- [ ] Outreach log → Postgres sync

---

## v0.3 — Observability & Polish (📋 Planned)

**Theme**: Make the system self-aware and auditable without human intervention.

### Planned
- [ ] Unified audit log (every action timestamped, tool-call-level)
- [ ] Application certainty auto-promotion (3+ evidence sources → high)
- [ ] Weekly digest report (Telegram: applied/pipeline/response-rate/follow-up)
- [ ] n8n monitoring workflow (VPS health, service status, alerts)
- [ ] Follow-up automation (no-response → draft reply after N days, human gate before send)
- [ ] Post-publish metrics capture (engagement 24h, 48h, 7d after publish)
- [ ] Dashboard public link with auth (accessible externally)

---

## v1.0 — Replicable System (🎯 Target)

**Theme**: Another person (or agent) can replicate and operate this system.

### Required for v1.0
- [ ] Full replication guide (new machine → operational in < 2 hours)
- [ ] Docker-based demo environment (no real LinkedIn credentials needed)
- [ ] Generalized ATS probe framework (beyond CPQD/HubXP)
- [ ] Multi-platform job discovery (Indeed, Gupy, Catho)
- [ ] Interview prep module (company research → briefing document)
- [ ] Comprehensive test suite for core utilities
- [ ] CHANGELOG with semantic versioning
- [ ] Public docs site

---

## Backlog (Unversioned / Exploratory)

### New Platforms
- [ ] Gupy.io Easy Apply probe
- [ ] Indeed application automation
- [ ] Workana project proposal automation
- [ ] Upwork proposal drafting

### AI Enhancements
- [ ] LLM-powered job description analysis (extract required vs. nice-to-have)
- [ ] Auto-draft personalized cover letter per application
- [ ] Interview question prediction from job description
- [ ] Salary negotiation research automation

### Infrastructure
- [ ] pgvector in Postgres (semantic search over job descriptions)
- [ ] Multi-agent handoff: local agent delegates to VPS agent for persistent tasks
- [ ] OpenHands integration for code-level automation tasks

### Monitoring
- [ ] Response rate tracking by role type, company size, scoring bucket
- [ ] A/B testing framework for CV variants (which preset gets more responses)
- [ ] LinkedIn profile view tracking correlation with applications

---

## Architecture Decisions Already Made

See [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) for the rationale behind key decisions including:

- Hybrid local+VPS model
- CDP over headless browser
- JSON-first state (before Postgres sync)
- Human gate as non-negotiable safety layer
- OpenClaw as agent framework

---

## How to Contribute to the Roadmap

Open an issue with label `roadmap` to propose new items, challenge existing prioritization, or offer to work on something. See [CONTRIBUTING.md](../CONTRIBUTING.md).
