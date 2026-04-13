# Skills — Python Automation Scripts

This directory contains the 14 operational Python scripts that power Cadence Career Ops.

All scripts are designed to:
- Run standalone from the command line
- Accept `--telegram` flag for formatted Telegram output
- Output JSON for programmatic use
- Work with Chrome via CDP at `127.0.0.1:9222`
- Use the shared `auto_apply_lib.py` utilities

## Dependencies

```bash
source ~/.venv/jobhunter/bin/activate
pip install playwright pandas jobspy requests
playwright install chromium
```

## Script Reference

### Discovery Layer

| Script | Description | Key Args |
|---|---|---|
| `browser_recon.py` | Lists all open Chrome tabs, classifies by type | `--jobs-only`, `--telegram` |
| `linkedin_job_search.py` | Searches LinkedIn for jobs via CDP, adds to queue | `--preset core_br` |
| `job_detail_extractor.py` | Extracts structured data from a job page | `--url URL`, `--scan-tabs` |
| `browser_probe.py` | General-purpose CDP browser operations | varies |

### Apply Layer

| Script | Description | Key Args |
|---|---|---|
| `application_guard.py` | Validates all safety criteria before submit | `--score N --title T --company C` |
| `linkedin_easy_apply_runner.py` | Full Easy Apply automation | `--job-id ID`, `--dry-run` |
| `auto_apply_lib.py` | Shared library (not standalone) | — |
| `auto_apply_loop.py` | Orchestrates queue processing | `--preset`, `--dry-run`, `--discover` |
| `tab_hygiene.py` | Closes completed job tabs | `--close-done` |

### ATS-Specific Probes

| Script | Description |
|---|---|
| `cpqd_assisted_probe.py` | CPQD ATS probe |
| `cpqd_fill_prepare.py` | CPQD form preparation helper |
| `hubxp_probe.py` | HubXP ATS probe |
| `hubxp_probe_wait.py` | HubXP probe with wait strategy |

### Visualization & Notification

| Script | Description | Key Args |
|---|---|---|
| `render_applications_dashboard.py` | Generates HTML dashboard from state | (no args — reads from state/) |
| `telegram_notifier.py` | Sends Telegram messages | `--message TEXT`, `--test`, `--setup` |
| `test_browser.py` | Quick CDP connectivity test | (no args) |

## Common Workflows

### Daily job search
```bash
source ~/.venv/jobhunter/bin/activate
python3 linkedin_job_search.py --preset core_br
```

### Check what's in the apply queue
```bash
cat ../../state/auto_apply_queue.json | python3 -m json.tool | grep -E '"role"|"company"|"status"'
```

### Run apply loop (dry-run first)
```bash
python3 auto_apply_loop.py --dry-run
# Review output, then:
python3 auto_apply_loop.py
```

### Regenerate dashboard
```bash
python3 render_applications_dashboard.py
# Output: ../../artifacts/dashboard/applications_dashboard.html
```

### Test Telegram connection
```bash
python3 telegram_notifier.py --test
```

### Check rate limit status
```bash
python3 application_guard.py --check-rate-limit
```

## Configuration

All scripts read from:
- `../../state/application_profile.json` — candidate profile
- `../../state/compensation_reference.json` — salary targets
- `../../state/auto_apply_rules.json` — thresholds and limits
- `../../config.json` — operational config (non-sensitive)
- `../../config.local.json` — secrets (Telegram token, gitignored)
- `../../.env.local` — environment variables (gitignored)

## Safety Notes

- **Never run `auto_apply_loop.py` without reviewing the queue first**
- The human gate via Telegram is mandatory — do not bypass it
- Rate limit is enforced in `application_guard.py` — do not use `--force` without good reason
- All submissions are logged with screenshots in `artifacts/applications/`
