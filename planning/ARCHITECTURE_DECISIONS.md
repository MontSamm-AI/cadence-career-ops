# Architecture Decisions

## Cadence Career Ops — ADR Log

---

## ADR-001: Hybrid Local + VPS Model

**Date**: 2026-04-08  
**Status**: ✅ Decided and Operational

### Context

We needed to decide where to run what: the browser automation that interacts with LinkedIn's authenticated UI, versus the persistent services like CRM, scheduling, and workflow automation.

### Decision

Split responsibilities:
- **Local (WSL + Windows)** = browser executor
- **VPS (Hetzner Docker Swarm)** = persistent brain

### Rationale

LinkedIn requires an authenticated browser session. Replicating this server-side would require:
1. Cookie/session proxying (fragile, policy-violating)
2. Handling 2FA headlessly (unreliable)
3. Maintaining a Chrome instance on the server (resource-heavy, no real benefit)

The user's existing Chrome session with real cookies is the most reliable path. It's already running. The VPS does what persistent infrastructure does well: scheduled tasks, durable storage, API endpoints, 24/7 availability.

### Consequences

- Local agent must be running for LinkedIn actions
- VPS runs continuously for persistence and scheduling
- Bridge between them is explicit (API calls, Telegram, n8n webhooks) — not transparent
- Agents are genuinely independent, not a single distributed system

---

## ADR-002: CDP over Headless Browser

**Date**: 2026-04-06  
**Status**: ✅ Decided and Operational

### Context

Playwright can run in two modes: connecting to an existing Chrome instance via CDP, or launching a new headless browser. Both were options.

### Decision

Connect via CDP to the user's existing Chrome instance (`--remote-debugging-port=9222`).

### Rationale

- LinkedIn's bot detection is much more effective against headless browsers
- The user's real Chrome has the correct fingerprint, cookies, and session
- No need to manage login, 2FA, or session refresh
- Human can visually monitor what the agent is doing in the real browser
- The trade-off (Chrome must be running with CDP enabled) is acceptable for a daily-use system

### Consequences

- Chrome must be pre-launched with `--remote-debugging-port=9222`
- Agent assumes LinkedIn is already logged in
- No headless mode for core LinkedIn operations
- Occasional coordination needed if user is actively browsing while agent runs

---

## ADR-003: JSON-First State, Postgres as Target

**Date**: 2026-04-09  
**Status**: ✅ Decided, Postgres sync in progress

### Context

Application state could live in: JSON files, SQLite, PostgreSQL, or a hybrid.

### Decision

Start with JSON files. Evolve toward Postgres as the canonical target with JSON as local cache/projection.

### Rationale

**Why JSON first:**
- Fastest to implement and iterate
- Human-readable, easy to inspect and patch manually
- No schema migration complexity in early stages
- Version-controllable (can commit state snapshots)

**Why Postgres as target:**
- Enables n8n workflows to read/write application state
- Enables server-side dashboard
- Enables multi-agent access (local and VPS agents share state)
- Enables richer queries (response rate by company, score distribution, etc.)

### Consequences

- Current system uses JSON as primary source of truth
- Dashboard reads from JSON (not Postgres yet)
- Sync from local JSON → Postgres: partial implementation
- `application_stage_overrides.json` handles Gmail-derived corrections (layer over JSON index)

---

## ADR-004: Human Gate as Non-Negotiable Layer

**Date**: 2026-04-06  
**Status**: ✅ Decided, No exceptions

### Context

Should the system be fully autonomous (auto-submit applications) or require human approval?

### Decision

Every application requires explicit human approval via Telegram before submission is classified as final.

### Rationale

- Employment applications carry professional reputation risk
- Autonomous submission at scale without review invites quality regression
- LinkedIn's policies make mass-automation of submissions problematic
- The human review takes < 30 seconds per application with the structured notification format
- Rate limit (5/day) makes full automation less valuable anyway

### Consequences

- Agent sends structured notification + screenshot
- Human replies with `confirmar [job_id]` to approve
- System never "silently" submits
- Audit trail is perfect (screenshot + Telegram message + timestamp)
- Application speed is bounded by human responsiveness (acceptable trade-off)

---

## ADR-005: OpenClaw as Agent Framework

**Date**: 2026-04-04  
**Status**: ✅ Decided and Operational

### Context

The agent layer could have been built from scratch, used LangChain, CrewAI, AutoGen, or another framework.

### Decision

Use OpenClaw as the agent framework.

### Rationale

- OpenClaw provides workspace-based memory that persists across sessions
- Native Telegram channel integration (no custom bot code)
- Multi-LLM routing with fallbacks (GPT-5.4 → Claude → Groq → OpenRouter)
- Tool calling abstraction (browser, exec, read/write, message)
- Chrome browser tool built-in (CDP bridge)
- Lightweight compared to CrewAI/AutoGen for single-agent use case

### Consequences

- Agent identity and behavior is defined in SOUL.md, AGENTS.md, USER.md
- Memory is maintained in MEMORY.md and daily files
- Session restarts don't lose context (file-based continuity)
- OpenClaw version updates may affect agent behavior

---

## ADR-006: Telegram as Human-Agent Interface

**Date**: 2026-04-06  
**Status**: ✅ Decided and Operational

### Context

The human-agent interface could be: Telegram, WhatsApp, email, Discord, or a custom web UI.

### Decision

Telegram for all human-agent communication.

### Rationale

- Telegram Bot API is simple, reliable, and free
- Native on mobile (important for approval flow)
- Markdown support for structured notifications
- Bot creation is trivial (@BotFather)
- Multiple bots can coexist (cadence-profissional bot + main cadence bot)
- No additional infrastructure needed

### Consequences

- All notifications go via Telegram
- Human gate requires Telegram availability
- If Telegram is down, the gate blocks (safe failure mode)
- Two bots maintain separate routing (Cadence Profissional vs. main agent)
