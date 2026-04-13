# Local / WSL Setup

This document describes the local architecture — how Windows, WSL, and Chrome interact to enable browser automation.

## Overview

```
┌──────────────────────────────────────────────────────┐
│                  Windows Host                         │
│                                                       │
│  Chrome (with CDP)  ←──── port 9222 ────→  WSL/Ubuntu│
│  └─ LinkedIn UI                              │        │
│  └─ Authenticated session              Cadence Agent  │
│  └─ Easy Apply forms                  └─ Python skills│
│                                        └─ OpenClaw    │
│                    ↕ shared localhost                 │
│             Telegram (human gate)                     │
└──────────────────────────────────────────────────────┘
```

## Why this design?

LinkedIn requires a real, persistent authenticated browser session. Server-side automation is:
- Detectable (no cookies, no session history, wrong user-agent)
- Fragile (frequent CAPTCHA challenges)
- Against LinkedIn's ToS in a more obvious way

By using Chrome running on Windows with a real user profile (logged in, with history), and driving it from WSL via CDP, we get:
- Full browser context (cookies, localStorage, session)
- Real-looking behavior (real mouse events, real timing)
- Separation of concerns (agent logic in WSL, browser UI on Windows)

## Components

### Chrome DevTools Protocol (CDP)

Chrome is launched with `--remote-debugging-port=9222`. This opens a WebSocket interface that allows any process to:
- Navigate URLs
- Read page content
- Click elements
- Fill forms
- Execute JavaScript
- Take screenshots

The Python scripts connect to `http://localhost:9222` via the `playwright` library (which wraps CDP natively).

### OpenClaw Agent (WSL)

The `cadence-profissional` agent runs inside OpenClaw on WSL. It:
- Receives task requests via the OpenClaw gateway (ws://127.0.0.1:18789)
- Calls the Python skills as subprocesses
- Manages session state (SQLite memory, JSON state files)
- Sends notifications via Telegram
- Routes complex memory/CRM operations to the VPS

### Windows Chrome Node (OpenClaw)

A separate OpenClaw node (`windows-chrome`) runs on Windows and acts as the bridge. It registers with the WSL gateway and signals that Chrome is available. The WSL agent checks for this node before any browser operation.

## Setup Steps

See [setup_chrome_cdp.sh](../../scripts/setup/setup_chrome_cdp.sh) for the automated setup.

### Manual Steps

1. **Install OpenClaw** in WSL:
   ```bash
   git clone https://github.com/openclaw/openclaw ~/openclaw-framework
   cd ~/openclaw-framework && npm install
   ```

2. **Configure** `~/.openclaw/openclaw.json` with your credentials (see [CONFIGURATION.md](../guides/CONFIGURATION.md)).

3. **Start Chrome with CDP** on Windows:
   ```
   chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\cadence-chrome-profile
   ```

4. **Log in to LinkedIn** manually in this Chrome window.

5. **Start the OpenClaw gateway** in WSL:
   ```bash
   cd ~/openclaw-framework && npm start
   ```

6. **Verify browser connection**:
   ```bash
   python3 scripts/skills/test_browser.py
   ```

## State Files

All state is stored in `~/.openclaw/workspace-linkedin/state/`:

| File | Purpose |
|---|---|
| `applications_index.json` | Master list of all applications |
| `follow_up_tracker.json` | Follow-up schedule per application |
| `auto_apply_queue.json` | Pending Easy Apply queue |
| `linkedin_posts_index.json` | Published posts index |

## Memory

SQLite databases in `~/.openclaw/memory/`:
- `cadence-profissional.sqlite` — agent working memory
- `linkedin-hunter.sqlite` — job hunter context
- `main.sqlite` — main agent memory

## Security Notes

- The CDP port (9222) binds to `localhost` only — it is not exposed to the network.
- The Chrome profile used for automation should be dedicated to this purpose.
- The Telegram human gate ensures no application is submitted without explicit approval.
