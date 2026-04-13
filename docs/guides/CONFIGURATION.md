# Configuration Guide

## Overview

Cadence Career Ops is configured primarily through `~/.openclaw/openclaw.json`. This file controls agents, models, channels, browser settings, and credentials.

**Never commit your real `openclaw.json` to version control.** Use `system/config/openclaw.example.json` as a template.

---

## Core Configuration: openclaw.json

```json
{
  "gateway": {
    "host": "127.0.0.1",
    "port": 18789,
    "token": "YOUR_GATEWAY_TOKEN"
  },
  "agents": [
    {
      "id": "cadence-profissional",
      "displayName": "Cadence Profissional",
      "workspace": "~/.openclaw/workspace-linkedin",
      "model": "openai-codex/gpt-5.4"
    }
  ],
  "models": {
    "primary": "openai-codex/gpt-5.4",
    "fallback": ["openrouter/qwen/qwen-2.5-72b-instruct"]
  },
  "auth": {
    "openai_codex": {
      "type": "oauth",
      "account": "your-email@gmail.com"
    }
  },
  "browser": {
    "cdp_port": 9222,
    "cdp_host": "localhost"
  },
  "telegram": {
    "bots": [
      { "name": "cadence", "token": "YOUR_BOT_TOKEN", "chat_id": "YOUR_CHAT_ID" }
    ]
  }
}
```

---

## Model Configuration

### Supported Models

| Provider | Model | Notes |
|---|---|---|
| openai-codex | gpt-5.4 | Primary, via OAuth (no API key needed) |
| groq | llama-3.3-70b-versatile | Fast inference, good for VPS |
| openrouter | qwen/qwen-2.5-72b-instruct | Fallback option |

### OAuth Setup (OpenAI Codex)

OpenAI Codex CLI supports OAuth-based access (no API key required). After installing:
```bash
codex login  # Opens browser, authorize with Google account
```

---

## Telegram Configuration

Telegram is used as the human approval gate. You need:

1. **Create a bot** via [@BotFather](https://t.me/BotFather)
2. Get your **chat ID** by messaging [@userinfobot](https://t.me/userinfobot)
3. Add both to your `openclaw.json`

### Message Formats

The system sends structured Telegram messages for:
- Job application previews (with score, title, company)
- Approval/rejection prompts
- Application confirmation
- Error alerts

---

## Chrome CDP Configuration

```json
"browser": {
  "cdp_port": 9222,
  "cdp_host": "localhost",
  "default_tab_timeout": 30,
  "apply_delay_min": 30,
  "apply_delay_max": 120
}
```

Chrome must be running with `--remote-debugging-port=9222` before any browser skill is invoked.

---

## Application Guard Settings

The `application_guard.py` script enforces safety thresholds:

```python
SCORE_THRESHOLD = 65       # Minimum 4D score to allow application
MAX_DAILY_APPLICATIONS = 5 # Hard limit per day
PROHIBITED_KEYWORDS = [
  "QA automation", "test automation", "RPA",
  "testing framework", "junior", "estágio"
]
APPLY_HOURS = (7, 23)      # Only apply between 07:00-23:00 BRT
```

These are defined inside the script. Edit `scripts/skills/application_guard.py` to adjust.

---

## CV Engine Configuration

The CV engine reads `cv_base.yaml` and generates PDFs. Key sections:

```yaml
profile:
  name: "Your Name"
  email: "your@email.com"
  linkedin: "linkedin.com/in/yourprofile"
  
presets:
  clt-ptbr:
    language: pt-BR
    max_pages: 2
    focus: ["ai_automation", "workflow"]
  master-en:
    language: en
    max_pages: 2
    focus: ["all"]
```

See `system/templates/cv_base.example.yaml` for a full template.

---

## Environment Variables

Some scripts support `.env` files. Create `.env` in the repo root:

```bash
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
CDP_PORT=9222
SCORE_THRESHOLD=65
```

---

## VPS Configuration

The VPS runs its own `openclaw.json` with different model preferences (optimized for cost). See `system/config/openclaw.vps.example.json`.

VPS environment variables (set in Docker Swarm secrets or `.env`):
```
POSTGRES_URL=postgresql://user:pass@localhost:5432/career_tracker
REDIS_URL=redis://localhost:6379
N8N_WEBHOOK_URL=https://n8n.yoursite.com/webhook/
```
