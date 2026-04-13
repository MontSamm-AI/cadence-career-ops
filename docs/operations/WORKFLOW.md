# Operational Workflow

## Daily Operation Cycle

```
Morning (08:00-09:00 BRT)
  ↓ Check Telegram for overnight alerts
  ↓ Review applications_index.json for stage updates
  ↓ Check follow_up_tracker.json for due follow-ups
  ↓ Start Chrome with CDP (if not running)

Discovery Window (09:00-11:00 BRT)
  ↓ Run linkedin_job_search.py (1-2 presets)
  ↓ Jobs scored via 4D system
  ↓ Queue built in auto_apply_queue.json
  ↓ Telegram notifications for high-score jobs

Review & Approval (any time)
  ↓ Receive Telegram job previews
  ↓ Approve or reject each opportunity
  ↓ Approved jobs stay in queue

Apply Window (11:00-14:00 or 16:00-19:00 BRT)
  ↓ Run auto_apply_loop.py
  ↓ For each queued job:
      → application_guard.py validates (score, limit, prohibited)
      → Telegram sends preview with full job details
      → Wait for human approval
      → linkedin_easy_apply_runner.py fills and submits
      → tab_hygiene.py closes used tab
      → telegram_notifier.py confirms submission
      → applications_index.json updated

Content Window (varies)
  ↓ LinkedIn post drafting (AI-assisted via OpenClaw)
  ↓ Image generation for post
  ↓ Human review and publish
  ↓ linkedin_posts_index.json updated

Evening (18:00-20:00 BRT)
  ↓ Follow-up messages (Telegram gate before sending)
  ↓ Review any email responses (manual, GOG-assisted)
  ↓ Update stages in applications_index.json
```

---

## Job Discovery Workflow

```
linkedin_job_search.py
  ↓ Opens LinkedIn jobs search via CDP
  ↓ Applies preset filters (title, location, date posted, remote)
  ↓ Scrolls through results (up to --max jobs)
  ↓ For each job:
      → Extracts: title, company, URL, posting date, easy_apply flag
      → Checks against applications_index.json (skip if already applied)
  ↓ Calls job_detail_extractor.py on new jobs
  ↓ Scores each job via 4D system
  ↓ Appends qualifying jobs to auto_apply_queue.json
  ↓ Sends Telegram summary: "X new jobs found, Y queued"
```

---

## Easy Apply Workflow

```
linkedin_easy_apply_runner.py --job-url URL
  ↓ Validates URL format
  ↓ Calls application_guard.py:
      → Check score threshold (≥ 65)
      → Check daily application count (≤ 5)
      → Check prohibited keywords
      → Check apply hours (07:00-23:00)
  ↓ Opens job URL via CDP
  ↓ Reads job description
  ↓ Sends Telegram preview: title, company, score, key requirements
  ↓ Waits for human approval (timeout: 30 minutes)
  ↓ On approval:
      → Clicks "Easy Apply"
      → Fills each form page:
          * Contact info (from cv_base.yaml profile)
          * Work authorization
          * Salary expectations (from configured targets)
          * Screening questions (validated against cv_base.yaml)
          * CV upload (selects best preset for role)
      → Validates all answers against prohibited claims
      → Sends Telegram final preview
      → Waits for final confirmation
      → Clicks Submit
  ↓ On success:
      → Updates applications_index.json
      → Updates follow_up_tracker.json (+14 days follow-up)
      → Saves application artifact to artifacts/applications/applied/
      → Telegram: "✅ Applied to [title] at [company]"
  ↓ On error:
      → Telegram: "❌ Error on [title]: [error details]"
      → Saves error artifact
```

---

## Content Publishing Workflow

```
(Manual trigger or scheduled)
  ↓ Draft topic in OpenClaw agent conversation
  ↓ Generate post copy (EN or PT-BR)
  ↓ Generate image (AI image generation or manual)
  ↓ Human review of copy and image
  ↓ Post to LinkedIn via browser_probe.py
  ↓ Confirm publication URL
  ↓ Update linkedin_posts_index.json with URL and metadata
  ↓ Telegram: "📢 Post published: [URL]"
```

---

## State Reconciliation (manual, becoming automated)

When email signals arrive (interview invite, rejection, assessment):
1. Open Gmail (GOG-assisted)
2. Identify relevant application in applications_index.json
3. Update `stage` field: `awaiting_response` → `interview` or `rejected`
4. Update follow_up_tracker.json accordingly
5. Regenerate dashboard: `python3 scripts/skills/render_applications_dashboard.py`

This process will be automated in v0.2 via n8n Gmail intake workflow.

---

## Dashboard

The HTML dashboard is generated from state files:
```bash
python3 scripts/skills/render_applications_dashboard.py
```

Output: `artifacts/dashboard/applications_dashboard.html`

Open in any browser. No server required — fully self-contained HTML.
