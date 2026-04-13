# Quickstart — 5 Minutes to Your First Job Search

This guide gets you from zero to running a job search in ~5 minutes, assuming you already have WSL2 and Chrome installed.

---

## Prerequisites Checklist

- [ ] Windows 10/11 with WSL2 (Ubuntu 22+)
- [ ] Python 3.11+ in WSL (`python3 --version`)
- [ ] Chrome browser installed on Windows
- [ ] LinkedIn account logged in to Chrome

---

## Step 1: Clone and Setup Python (2 min)

```bash
# In WSL terminal
git clone https://github.com/MontSamm-AI/cadence-career-ops.git
cd cadence-career-ops

python3 -m venv ~/.venv/jobhunter
source ~/.venv/jobhunter/bin/activate
pip install playwright pandas jobspy requests
playwright install chromium
```

---

## Step 2: Launch Chrome with CDP (1 min)

Open PowerShell and run:

```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  -ArgumentList "--remote-debugging-port=9222", `
    "--user-data-dir=$env:LOCALAPPDATA\Google\Chrome\User Data"
```

Log into LinkedIn in this Chrome window if not already logged in.

Verify CDP is working (in WSL):
```bash
curl -s http://127.0.0.1:9222/json/version | python3 -m json.tool
# Should show Chrome version info
```

---

## Step 3: Configure Your Profile (2 min)

```bash
# Copy templates
cp system/templates/cv_base.example.yaml state_config/cv_base.yaml
cp system/config/openclaw.example.json ~/.openclaw/openclaw.json

# Edit cv_base.yaml with your data
nano state_config/cv_base.yaml
# Fill in: name, email, phone, experience, skills, salary targets
```

---

## Step 4: Run Your First Job Search

```bash
source ~/.venv/jobhunter/bin/activate
cd cadence-career-ops

python3 scripts/skills/linkedin_job_search.py --preset core_br
```

This opens LinkedIn in your real Chrome, searches for AI automation jobs in Brazil, and adds qualifying jobs to the queue.

---

## Step 5: View What Was Found

```bash
# See the queue
python3 -c "
import json
queue = json.load(open('state/auto_apply_queue.json'))
for item in queue.get('items', [])[:5]:
    print(f\"{item['priority']:2d}. {item['role']} @ {item['company']} — {item['location']}\")
"
```

---

## Next Steps

- [Full installation guide](INSTALLATION.md) — OpenClaw, Telegram bot, VPS
- [CV system guide](CV_SYSTEM.md) — generate your first PDF CV
- [Architecture overview](../architecture/SYSTEM_OVERVIEW.md) — understand the full system
- [Capability map](../operations/CAPABILITY_MAP.md) — what's proven vs. planned

---

> **Note**: The Easy Apply runner requires additional configuration (Telegram bot for the human gate, `application_profile.json` with your real data). See [INSTALLATION.md](INSTALLATION.md) for the complete setup.
