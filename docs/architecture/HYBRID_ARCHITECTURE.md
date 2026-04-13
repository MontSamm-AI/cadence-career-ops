# Hybrid Architecture: Local + VPS

## Design Philosophy

The system deliberately splits responsibilities between the local machine (Windows + WSL) and a remote VPS (Hetzner). This is not a cost-optimization decision — it is an architectural requirement.

## The Split

```
LOCAL (Windows + WSL)                    VPS (Hetzner, Debian 13)
─────────────────────                    ────────────────────────
• Chrome CDP browser                     • PostgreSQL career_tracker
• LinkedIn Easy Apply                    • n8n workflow orchestration
• Authenticated sessions                 • Docker Swarm (14 services)
• Visual review of forms                 • Redis cache
• CV file uploads                        • Evolution API (WhatsApp)
• Telegram approval gate                 • Traefik reverse proxy
• Python skills (14 scripts)             • OpenClaw VPS agent
• SQLite working memory                  • Cadence VPS agent
• JSON state files                       • Long-term CRM memory
• OpenClaw local gateway                 • Scheduled workflows
                                         • Public dashboards (planned)
```

## Why Not Fully Local?

A laptop's state is ephemeral. Power cycles, network changes, and WSL restarts lose context. For an operation tracking 40+ active applications across weeks, persistence matters.

## Why Not Fully Remote?

LinkedIn will not work from a VPS IP:
- Data center IPs are immediately flagged
- No stored browser history or cookies to build trust
- Easy Apply requires file uploads from local disk
- CAPTCHA triggers are near-certain

The VPS cannot own the browser. The browser must live on the local machine.

## Communication Flow

```
1. Job Discovery (local)
   Python skill → Chrome CDP → LinkedIn search → JSON results

2. Scoring (local)
   auto_apply_loop.py → 4D scoring → queue filtered jobs

3. Human Gate (Telegram)
   telegram_notifier.py → bot sends job preview → Sami approves/rejects

4. Application (local)
   linkedin_easy_apply_runner.py → CDP → form fill → submit

5. State Update (local)
   applications_index.json updated → SQLite memory updated

6. CRM Sync (local → VPS) [in progress]
   Nightly sync → PostgreSQL career_tracker on VPS

7. Gmail Intake (VPS) [in progress]
   n8n workflow → Gmail API → classify signal → state override → notify
```

## VPS Services (Docker Swarm)

| Service | URL | Purpose |
|---|---|---|
| Traefik | Automatic | Reverse proxy + SSL |
| n8n | n8n.montsam.site | Workflow orchestration |
| PostgreSQL | Internal | Primary CRM database |
| Redis | Internal | Cache + pub/sub |
| Evolution API | evolution.montsam.site | WhatsApp automation |
| OpenClaw VPS | openclaw.montsam.site | VPS agent gateway |
| Portainer | portainer.montsam.site | Container management |

## OpenClaw Gateway

Both environments run an OpenClaw instance with their own gateway:

| Environment | Gateway |
|---|---|
| Local (WSL) | ws://127.0.0.1:18789 |
| VPS | wss://openclaw.montsam.site |

Agents register with their local gateway. The `windows-chrome` node on Windows also registers with the WSL gateway, making Chrome available to WSL agents.

## State Canonicalization (Roadmap v0.2)

Currently, state lives in local JSON files. The roadmap calls for:
1. Local JSON as write-first (fast, offline-capable)
2. Nightly sync to PostgreSQL on VPS (canonical)
3. Gmail intake workflow auto-promoting states based on email evidence
4. VPS dashboard serving canonical state publicly

This preserves local-first operation while making the VPS the persistent record of truth.
