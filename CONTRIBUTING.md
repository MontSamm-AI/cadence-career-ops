# Contributing to Cadence Career Ops

Thank you for your interest in contributing. This is an active project used in production — contributions that improve reliability, generalizability, and documentation are especially welcome.

---

## What We Need Most

1. **New ATS probes** — scripts for other job platforms (Gupy, Indeed, Workana, Recruitee, Lever, Greenhouse)
2. **CV preset improvements** — better HTML templates, new language variants
3. **Scoring improvements** — better 4D scoring logic, new signal sources
4. **Documentation** — clearer setup guides, troubleshooting, architecture explanations
5. **Tests** — unit tests for `auto_apply_lib.py`, `application_guard.py`, compensation logic

---

## Ground Rules

- **Never commit personal data**: no real names, emails, phone numbers, API keys, bot tokens, or CV content
- **Never commit secrets**: `.env`, `config.local.json`, `*.key` are all gitignored — keep it that way
- **Truthfulness principle**: any contribution to the application automation must maintain the truthfulness policy — no changes that enable or encourage false claims in applications
- **Human gate**: do not remove or weaken the human approval gate. It exists for good reasons.

---

## Development Setup

```bash
git clone https://github.com/MontSamm-AI/cadence-career-ops.git
cd cadence-career-ops

# Python environment
python3 -m venv .venv/dev
source .venv/dev/bin/activate
pip install playwright pandas jobspy jinja2 requests pytest

# Run tests (when they exist)
pytest tests/
```

---

## Pull Request Process

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/gupy-probe`
3. Make your changes, following the code style of existing scripts
4. Run any relevant tests
5. Submit a PR with:
   - What problem it solves
   - What part of the system it touches
   - How you tested it (or why you couldn't test it without real credentials)
   - If it changes the Easy Apply flow, describe the safeguards

---

## Issue Labels

| Label | Use For |
|---|---|
| `bug` | Something broken in the existing flow |
| `enhancement` | Improvement to existing capability |
| `new-ats` | New job platform probe |
| `cv-engine` | CV generation improvements |
| `docs` | Documentation only |
| `scoring` | Job scoring logic |
| `infra` | VPS/Docker/n8n related |
| `roadmap` | Roadmap discussion |
| `good-first-issue` | Good for newcomers |

---

## Code Style

- Follow the existing script style: type hints, dataclasses, clear function names
- Scripts should be runnable standalone (`if __name__ == '__main__': main()`)
- Argparse for CLI interface
- JSON output format for tool integration
- Telegram-formatted output mode where relevant (`--telegram` flag)
- Path handling via `pathlib.Path`, not string concatenation
- No hardcoded personal paths — use environment variables or config files

---

## Questions?

Open an issue with the `question` label or reach out via LinkedIn.
