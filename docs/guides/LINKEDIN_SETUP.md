# LinkedIn Setup Guide

## Prerequisites

Before running any LinkedIn automation:
1. A real LinkedIn account with an active profile
2. Chrome installed on Windows
3. WSL2 with Ubuntu and Python 3.11+
4. OpenClaw installed and configured

---

## Step 1 — Chrome CDP Setup

LinkedIn requires an authenticated browser session. We use Chrome with the DevTools Protocol (CDP) enabled.

### Option A: Automated setup (recommended)
```bash
bash scripts/setup/setup_chrome_cdp.sh
```

### Option B: Manual launch (Windows command prompt)
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir=C:\cadence-chrome-profile
```

**IMPORTANT**: Use a dedicated Chrome profile for automation. Do not mix with your personal Chrome profile.

### Verify CDP is working
```bash
curl http://localhost:9222/json/version
```

Expected output: JSON with Chrome version info.

---

## Step 2 — LinkedIn Login

1. In the CDP-enabled Chrome window, navigate to [linkedin.com](https://linkedin.com)
2. Log in with your LinkedIn credentials
3. Complete any 2FA if required
4. Verify you can see your feed

The browser session (cookies, localStorage) is stored in the Chrome profile directory and persists across restarts. You should only need to log in once.

---

## Step 3 — Profile Verification

Run the browser recon script to verify LinkedIn is accessible:
```bash
source .venv/jobhunter/bin/activate
python3 scripts/skills/browser_recon.py
```

Expected output:
```
Current tab: linkedin.com/feed/
Session: authenticated
Profile name: [Your Name]
Ready for automation
```

---

## Step 4 — Configure Search Presets

Search presets in `linkedin_job_search.py` define what jobs to discover. Key presets:

| Preset | Target |
|---|---|
| `core_br` | AI automation / agents / workflows, Brazil, PT-BR |
| `ai_intl` | AI engineering roles, international/remote, EN |
| `automation_ptbr` | Automation, RPA with AI, Brazil |
| `strategic` | Senior roles at known AI companies |

To run a preset:
```bash
python3 scripts/skills/linkedin_job_search.py --preset core_br --max 50
```

---

## Step 5 — Easy Apply Test Run

Before running the full auto-apply loop, test with a single job:

```bash
python3 scripts/skills/linkedin_easy_apply_runner.py \
  --job-url "https://www.linkedin.com/jobs/view/JOBID" \
  --dry-run
```

`--dry-run` fills all forms but stops before the final submit button. Review the Telegram notification to see what would be submitted.

---

## Rate Limiting and Safety

The system enforces:
- **Max 5 applications per day** (configurable in `application_guard.py`)
- **30-120 second delays** between form interactions
- **07:00-23:00 BRT window** only
- **Human approval gate** — every application needs Telegram confirmation
- **Score threshold** — minimum 65/100 before queuing

---

## Troubleshooting

### "No tabs found" error
Chrome CDP is not accessible. Ensure Chrome is running with `--remote-debugging-port=9222`.

### "LinkedIn session expired"
Open the CDP Chrome window and log in to LinkedIn again.

### "Application guard blocked"
Job score is below threshold, or daily limit reached. Check `state/auto_apply_queue.json` for score breakdown.

### "Tab timeout on form"
LinkedIn changed their UI. Check the script version and open an issue at the GitHub repository.

---

## LinkedIn SSI Health

Maintain LinkedIn Social Selling Index health:
- Apply only to relevant roles (high fit score)
- Do not exceed 5-10 Easy Apply applications per day
- Keep your profile complete and up to date
- Engage with posts organically (separate from automation)
