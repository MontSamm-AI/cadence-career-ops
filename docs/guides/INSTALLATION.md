# Installation Guide

## Cadence Career Ops — Full Setup

---

## Overview

This guide walks through setting up the Cadence Career Ops system from scratch on a Windows machine with WSL2. The system requires:

- Windows 10/11 with WSL2 (Ubuntu 22+)
- Chrome/Chromium with CDP enabled
- Python 3.11+ in WSL
- OpenClaw agent framework
- (Optional) A VPS for persistent layer

Estimated setup time: 30–60 minutes

---

## Step 1: WSL2 and Ubuntu

```bash
# In PowerShell (admin)
wsl --install -d Ubuntu-22.04
wsl --set-default Ubuntu-22.04

# After restart, open Ubuntu and update
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git curl
```

---

## Step 2: Clone the Repository

```bash
# In WSL
git clone https://github.com/MontSamm-AI/cadence-career-ops.git
cd cadence-career-ops
```

---

## Step 3: Python Virtual Environment

```bash
# Create venv (must match path expected by scripts)
python3 -m venv ~/.venv/jobhunter
source ~/.venv/jobhunter/bin/activate

# Install dependencies
pip install playwright pandas jobspy jinja2 weasyprint requests

# Install Playwright browsers
playwright install chromium

# Verify
python3 -c "import playwright, pandas, jobspy; print('Dependencies OK')"
```

---

## Step 4: Chrome CDP Setup

The system connects to Chrome via the Chrome DevTools Protocol (CDP). You need Chrome running with the remote debugging port exposed.

### Windows Chrome with CDP

Create a shortcut or script to launch Chrome with CDP:

```powershell
# PowerShell script to start Chrome with CDP
# Save as: C:\scripts\start_chrome_cdp.ps1
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$args = @(
    "--remote-debugging-port=9222",
    "--user-data-dir=C:\Users\$env:USERNAME\AppData\Local\Google\Chrome\User Data",
    "--no-first-run",
    "--no-default-browser-check"
)
Start-Process -FilePath $chromePath -ArgumentList $args
```

```bash
# In WSL, verify CDP is accessible
curl http://127.0.0.1:9222/json/version
# Should return Chrome version info
```

> **Important**: Chrome must be running with your LinkedIn session already logged in. The system uses your existing authenticated session — it does NOT handle login.

---

## Step 5: OpenClaw Setup

OpenClaw is the agent framework. Install it following the [official docs](https://openclaw.dev).

```bash
# Install OpenClaw CLI (Linux/WSL)
curl -fsSL https://openclaw.dev/install.sh | bash

# Initialize configuration
openclaw configure

# Copy the example config
cp system/config/openclaw.example.json ~/.openclaw/openclaw.json
```

Edit `~/.openclaw/openclaw.json`:
- Set your LLM API keys (OpenAI OAuth recommended, Groq free tier as fallback)
- Configure Telegram bot token (get one from @BotFather)
- Set your workspace path

---

## Step 6: Configure Your Profile

The system uses a structured YAML profile to drive all applications:

```bash
# Copy template
cp system/templates/cv_base.example.yaml cv_base.yaml

# Edit with your real information
nano cv_base.yaml
```

Key sections to configure:
- `candidate`: name, email, phone, location
- `experience_defaults`: truthful years of experience by domain
- `skills_truth_defaults`: boolean flags for each skill (be honest)
- `compensation`: salary targets by market/track
- `cv_mapping`: which CV preset to use for which job type

---

## Step 7: Configure Workspace State

```bash
# Set up the workspace-linkedin directory structure
mkdir -p ~/.openclaw/workspace-linkedin/{state,artifacts/{applications/{applied,blocked,skipped},browser/{tabs,screenshots,jobs},dashboard},logs,memory}

# Copy initial state templates
cp system/templates/state/*.json ~/.openclaw/workspace-linkedin/state/
```

Edit `state/application_profile.json` with your real profile data.

---

## Step 8: Configure Telegram Notifications

The human approval gate runs via Telegram. You need a bot.

```bash
# 1. Create bot at https://t.me/BotFather → /newbot
# 2. Get your chat ID: message @userinfobot
# 3. Configure:
python3 scripts/skills/telegram_notifier.py \
  --setup \
  --bot-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID"

# Test
python3 scripts/skills/telegram_notifier.py --test
```

---

## Step 9: Validate the Environment

Run the validation checklist:

```bash
# Check CDP
curl -s http://127.0.0.1:9222/json/version | python3 -m json.tool

# Check Python skills
source ~/.venv/jobhunter/bin/activate
python3 scripts/skills/browser_recon.py
# Should list open Chrome tabs

# Check Telegram
python3 scripts/skills/telegram_notifier.py --test

# Check rate limits
python3 scripts/skills/application_guard.py --check-rate-limit
```

---

## Step 10: First Job Search

```bash
source ~/.venv/jobhunter/bin/activate

# Run a job search (opens LinkedIn in real Chrome, collects job cards)
python3 scripts/skills/linkedin_job_search.py --preset core_br

# Review what was found
cat ~/.openclaw/workspace-linkedin/state/auto_apply_queue.json | python3 -m json.tool | head -50
```

---

## Optional: VPS Setup

For the persistent layer (PostgreSQL CRM, n8n workflows), see [VPS_SETUP.md](../architecture/VPS_SETUP.md).

The system works without the VPS — it just uses local JSON files as the state layer.

---

## Troubleshooting

### CDP not accessible
```bash
# Check if Chrome is running
# Windows PowerShell:
Get-Process chrome

# Check port binding (WSL can reach Windows localhost)
curl http://127.0.0.1:9222/json/version

# If it fails, try the Windows IP from WSL:
cat /etc/resolv.conf | grep nameserver
# Use that IP instead of 127.0.0.1
```

### LinkedIn session not found
- Make sure Chrome is logged into LinkedIn before running scripts
- Check that `--user-data-dir` in the CDP launch command points to your real Chrome profile

### Playwright connection fails
```bash
# Reinstall playwright
pip install --upgrade playwright
playwright install chromium

# Test connection
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    print(f'Connected: {len(b.contexts)} context(s)')
"
```

### Rate limit hit
```bash
# Check daily count
python3 scripts/skills/application_guard.py --check-rate-limit

# Rate limit resets at midnight
# Logs: ~/.openclaw/workspace-linkedin/logs/daily_applications.json
```
