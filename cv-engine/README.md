# CV Engine

Adaptive CV generation system: YAML profile → branded PDF with multiple presets.

## Files

```
cv-engine/
├── README.md                   # This file
├── cv_base.template.yaml       # Template with annotated fields (use system/templates/ for full version)
└── cv_branded_generator.py     # Generator script
```

The full annotated template is at `system/templates/cv_base.example.yaml`.

## Quick Start

```bash
source ~/.venv/jobhunter/bin/activate

# Copy and fill in your profile
cp ../system/templates/cv_base.example.yaml cv_base.yaml
nano cv_base.yaml  # Fill in your real data

# Generate a specific preset
python3 cv_branded_generator.py --preset master-en

# Generate all presets
python3 cv_branded_generator.py --all

# Generate for a specific role
python3 cv_branded_generator.py --preset clt-ptbr --job "AI Automation Specialist" --company "Acme"
```

## Presets

| Preset | Language | Target Market |
|---|---|---|
| `clt-ptbr` | Portuguese (BR) | Brazil CLT employment |
| `master-ptbr` | Portuguese (BR) | Brazil general |
| `master-ptbr-1p` | Portuguese (BR) | Brazil — 1 page compact |
| `master-en` | English | International |
| `master-en-1p` | English | International — 1 page compact |
| `upwork-en` | English | Upwork / freelance |
| `automation-ptbr` | Portuguese (BR) | Automation specialist focus |
| `cpqd` | Portuguese (BR) | Research institutions |

## Output

Files saved to `output/pdf/` with naming:
```
CV_[YourName]_[preset]_[role-slug]_[YYYYMMDD].pdf
```

## See Also

Full CV system documentation: [docs/guides/CV_SYSTEM.md](../docs/guides/CV_SYSTEM.md)
