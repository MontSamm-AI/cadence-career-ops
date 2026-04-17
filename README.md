# Cadence Career Ops 🎯

[![Status](https://img.shields.io/badge/status-operational-31d0aa?style=flat-square)](./docs/showcase/RESULTS.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](./scripts/skills/)
[![OpenClaw](https://img.shields.io/badge/powered_by-OpenClaw-6ea8ff?style=flat-square)](./docs/architecture/SYSTEM_OVERVIEW.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](./LICENSE)

> **AI-powered career automation system** — from job discovery to Easy Apply, adaptive CV generation, application tracking, and hybrid local + VPS architecture.

Built on the [OpenClaw](https://openclaw.dev) agent framework. Operates a real browser (Chrome CDP) against LinkedIn's authenticated UI, with a persistent VPS as the "brain" for CRM, workflows, and observability.

---

## What This Is

A **full-stack career operations pipeline** — not a toy demo or a spam bot. It is a production system built and operated by [Sami Monteleone](https://www.linkedin.com/in/samimonteleone) to solve the real problem of managing a high-signal, high-velocity job search with precision and auditability.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CADENCE CAREER OPS SYSTEM                        │
│                                                                     │
│  Windows Chrome ←── CDP ──→ WSL/Ubuntu (Cadence Agent)             │
│       │                            │                                │
│  LinkedIn UI                  14 Python Skills                      │
│  Easy Apply forms             SQLite / JSON State                   │
│  Authenticated session        Telegram Gate (human approval)        │
│                               ↕                                     │
│                          VPS (Hetzner)                              │
│                          PostgreSQL CRM                             │
│                          n8n Workflows                              │
│                          Docker Swarm (14 services)                 │
└─────────────────────────────────────────────────────────────────────┘
```

### What's Live Today

| Capability | Status | Details |
|---|---|---|
| Job discovery via browser | ✅ Operational | LinkedIn search via real CDP browser |
| 4D job scoring | ✅ Operational | fit, stretch, strategic, value dimensions |
| LinkedIn Easy Apply | ✅ Proven | Full form fill + salary-aware answers + CV selection |
| Human approval gate | ✅ Operational | Telegram-based gate before every submission |
| Application tracking | ✅ Operational | JSON-backed index + follow-up tracker |
| Adaptive CV generation | ✅ Operational | YAML → branded PDF (24 variants generated) |
| HTML dashboard | ✅ Operational | Local self-contained dashboard from state files |
| LinkedIn content posting | ✅ Proven | End-to-end post flow with image and copy |
| VPS persistence layer | ✅ Running | 14-service Docker Swarm on Hetzner |
| PostgreSQL CRM | 🔄 In progress | Schema ready, sync in progress |
| n8n Gmail intake | 🔄 In progress | Workflow architecture defined |

---

## Quick Start

### Prerequisites

- WSL2 (Ubuntu 22+) on Windows
- Python 3.11+ with a virtual environment
- Chrome/Chromium running with [CDP enabled](./docs/guides/LINKEDIN_SETUP.md)
- [OpenClaw](https://openclaw.dev) installed locally

### 3-Step Setup

```bash
# 1. Clone and configure
git clone https://github.com/MontSamm-AI/cadence-career-ops.git
cd cadence-career-ops
cp system/config/openclaw.example.json ~/.openclaw/openclaw.json
# Edit with your models/tokens

# 2. Install Python dependencies
python3 -m venv .venv/jobhunter
source .venv/jobhunter/bin/activate
pip install playwright pandas jobspy
playwright install chromium

# 3. Configure your profile and run
cp system/templates/cv_base.example.yaml cv_base.yaml
# Edit with your real profile data
python3 scripts/skills/linkedin_job_search.py --preset core_br
```

See [INSTALLATION.md](./docs/guides/INSTALLATION.md) for the full setup guide.

---

## Architecture

The system uses a **hybrid model** — deliberately separating concerns:

- **Local (WSL + Windows)** → browser executor: Chrome CDP, Easy Apply, LinkedIn posting, visual review, file uploads
- **VPS (Hetzner/Docker Swarm)** → persistent brain: PostgreSQL CRM, n8n workflows, schedulers, alerts, dashboard, long-term memory

This split is a core architectural decision: LinkedIn requires an **authenticated browser session** that cannot be replicated server-side without complex auth proxying. The VPS does what persistent infrastructure does best.

Full architecture details: [SYSTEM_OVERVIEW.md](./docs/architecture/SYSTEM_OVERVIEW.md)

---

## The 14 Python Skills

The `scripts/skills/` directory contains the operational core:

| Script | Role |
|---|---|
| `linkedin_easy_apply_runner.py` | Full Easy Apply automation (604 lines) |
| `auto_apply_loop.py` | Orchestrates the apply queue |
| `auto_apply_lib.py` | Shared utilities, profile, compensation logic |
| `linkedin_job_search.py` | Job discovery via LinkedIn CDP |
| `job_detail_extractor.py` | Structured extraction of job details |
| `browser_recon.py` | Chrome tab reconnaissance |
| `browser_probe.py` | General-purpose browser probing |
| `application_guard.py` | Pre-submission safety gate |
| `tab_hygiene.py` | Manages open browser tabs post-apply |
| `render_applications_dashboard.py` | Renders HTML dashboard from state |
| `telegram_notifier.py` | Sends formatted Telegram alerts |
| `cpqd_assisted_probe.py` | ATS-specific probe (CPQD) |
| `cpqd_fill_prepare.py` | ATS-specific form preparation |
| `hubxp_probe.py` / `hubxp_probe_wait.py` | ATS-specific probes (HubXP) |

---

## CV Engine

The adaptive CV system converts a structured YAML profile into branded PDFs:

```
cv_base.yaml  →  cv_branded_generator.py  →  CV_Sami_[preset]_[role]_[date].pdf
```

Presets: `clt-ptbr`, `master-en`, `master-ptbr`, `upwork-en`, `automation-ptbr`, `cpqd`

24 CV variants have been generated across multiple roles and markets.

Details: [CV_SYSTEM.md](./docs/guides/CV_SYSTEM.md)

---

## Security & Ethics

This system is built with safety at its core:

- **Human gate**: every application requires explicit Telegram approval from Sami before submission
- **Rate limiting**: max 5 applications/day via automation, 30–120s delays between actions
- **Score threshold**: minimum score of 65/100 before any application is even queued
- **Prohibited claims**: runtime checks prevent false claims in any submitted application
- **No-apply hours**: system respects 07:00–23:00 Brasília window
- **Blocked keywords**: QA automation, test automation, RPA, and unrelated roles are auto-filtered

---

## Results

- **40+ applications** tracked across multiple ATS systems and LinkedIn
- **24 CV variants** generated across 6 preset profiles
- **1 LinkedIn post** published end-to-end (topic selection → image → copy → publication)
- **0 false claims** submitted — every answer is validated against `cv_base.yaml`
- **4D scoring system** filtering hundreds of discovered jobs to a high-signal queue

See [RESULTS.md](./docs/showcase/RESULTS.md) for details.

---

## Project Structure

```
cadence-career-ops/
├── README.md                          # This file
├── README.pt-BR.md                    # Portuguese version
├── docs/
│   ├── architecture/                  # System design docs
│   ├── guides/                        # Setup and usage guides
│   ├── operations/                    # Runbooks and capability maps
│   └── showcase/                      # Results and evidence
├── system/
│   ├── config/                        # Config templates (no secrets)
│   └── templates/                     # CV and workspace templates
├── scripts/
│   ├── setup/                         # Installation scripts
│   └── skills/                        # The 14 operational Python scripts
├── cv-engine/                         # CV generation system
└── planning/                          # Roadmap and architecture decisions
```

---

## Roadmap

| Version | Status | Focus |
|---|---|---|
| v0.1 (current) | ✅ Operational | Easy Apply, job scoring, CV generation, tracking, posting |
| v0.2 | 🔄 In progress | PostgreSQL CRM sync, n8n Gmail intake, posting cadence |
| v0.3 | 📋 Planned | VPS dashboard backed by canonical state, hybrid queue |
| v1.0 | 🎯 Target | Multi-platform (Indeed, Gupy), interview prep, replicate guide |

Full roadmap: [ROADMAP.md](./planning/ROADMAP.md)

---

## Built By

**Sami Monteleone** — Applied AI automation engineer, agent builder, workflow architect.

- 🔗 [LinkedIn](https://linkedin.com/in/sami-monteleone)
- 💬 Public contact: LinkedIn DM / GitHub Issues
- 🌍 Brazil | Open to remote international roles

> This project is a live portfolio artifact — it demonstrates applied AI engineering, browser automation, agent orchestration, hybrid infrastructure, and production-grade Python, all in a real operational context.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). PRs welcome for new ATS probes, CV presets, scoring improvements, and documentation.

---

## License

MIT — see [LICENSE](./LICENSE).
