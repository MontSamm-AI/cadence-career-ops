# CV Generation System

## Adaptive CV Engine — Reference Guide

---

## Overview

The CV engine converts a single structured YAML profile into multiple branded PDF CVs, each tailored to a specific job type, market, and language.

```
cv_base.yaml
    │
    ▼
cv_branded_generator.py  ──────► cv_templates/cv_branded.html.j2
    │                                           │
    ▼                                           │
Jinja2 rendering ◄──────────────────────────────┘
    │
    ▼
WeasyPrint/HTML → PDF
    │
    ▼
output/pdf/CV_SamiMonteleone_[preset]_[role]_[date].pdf
```

---

## CV Presets

| Preset | Language | Market | Use Case |
|---|---|---|---|
| `clt-ptbr` | Portuguese (BR) | Brazil CLT | Domestic employment contracts |
| `master-ptbr` | Portuguese (BR) | Brazil | General BR applications |
| `master-ptbr-1p` | Portuguese (BR) | Brazil | One-page compact version |
| `master-en` | English | Global | International and multilateral |
| `master-en-1p` | English | Global | One-page compact version |
| `upwork-en` | English | Upwork/Freelance | Freelance profiles and proposals |
| `automation-ptbr` | Portuguese (BR) | Brazil | Automation specialist focus |
| `cpqd` | Portuguese (BR) | Research | Research institution applications |

---

## cv_base.yaml Structure

The master YAML file is the single source of truth for all CV content. See `system/templates/cv_base.example.yaml` for the full annotated template.

Key sections:

```yaml
candidate:
  name: "Your Full Name"
  emails:
    primary: "career@email.com"
    secondary: "other@email.com"
  phone:
    number_e164: "+5519XXXXXXXXX"
    number_national: "(19) XXXXX-XXXX"
  location:
    city: "São Paulo"
    state: "SP"
    country: "Brazil"

headline:
  ptbr: "Especialista em IA e Automação"
  en: "AI Automation Specialist"

summary:
  ptbr: |
    [Your summary in PT-BR]
  en: |
    [Your summary in EN]

experience:  # truthful, verifiable claims only
  - role: "AI Automation Engineer"
    company: "Company Name"
    start: "2024-01"
    end: "present"
    highlights_ptbr:
      - "Built X resulting in Y"
    highlights_en:
      - "Built X resulting in Y"

skills:
  primary: [...]   # Core skills — confident claim
  secondary: [...]  # Supporting skills
  honest_gaps: [...] # Do NOT claim these

experience_defaults:  # Used by Easy Apply auto-fill
  ai_applied_years_numeric: "2"
  workflow_automation_years_numeric: "3"
  it_years_numeric: "4"

skills_truth_defaults:  # Used for Yes/No form questions
  power_bi: "No"
  uipath: "No"
  aws_bedrock_sagemaker: "No"
  # ... only claim what's true

metrics:  # Quantified achievements — must be verifiable
  - "Built X automation reducing Y by Z%"
  - "Managed N integrations across M platforms"

compensation:  # Salary targets by market
  br_clt:
    default: 18000   # BRL/month
  br_pj:
    default: 22000   # BRL/month
  international_remote:
    default: 4500    # USD/month
  freelance:
    hourly_default: 150  # BRL/hour

cv_mapping:  # Which CV file to auto-select for Easy Apply
  brazil_ai_automation:
    file: "CV_SamiMonteleone_clt-ptbr_cv_20260409.pdf"
    path: "/path/to/pdf"
  international_ai_automation:
    file: "CV_SamiMonteleone_master-en_cv_20260409.pdf"
    path: "/path/to/pdf"
```

---

## Running the Generator

```bash
source ~/.venv/jobhunter/bin/activate
cd /path/to/cv-engine/

# Generate all presets
python3 cv_branded_generator.py --all

# Generate specific preset
python3 cv_branded_generator.py --preset clt-ptbr

# Generate for specific role
python3 cv_branded_generator.py --preset master-en --job "AI Automation Engineer" --company "Acme"

# Output goes to output/pdf/ with filename:
# CV_SamiMonteleone_[preset]_[slug-of-role]_[YYYYMMDD].pdf
```

---

## Generated CV Variants (current)

24 CVs have been generated as of April 2026:

```
output/pdf/
├── CV_SamiMonteleone_clt-ptbr_cv_20260409.pdf
├── CV_SamiMonteleone_master-en_cv_20260409.pdf
├── CV_SamiMonteleone_master-en-1p_cv_20260409.pdf
├── CV_SamiMonteleone_master-ptbr_cv_20260409.pdf
├── CV_SamiMonteleone_master-ptbr-1p_cv_20260409.pdf
├── CV_SamiMonteleone_upwork-en_ai-automation-specialist_[date].pdf
├── CV_SamiMonteleone_upwork-en_cv_20260409.pdf
├── CV_SamiMonteleone_automation-ptbr_[role]_[date].pdf
├── CV_SamiMonteleone_cpqd_pesquisadora-ii_[date].pdf
├── CV_SamiMonteleone_cpqd_pesquisadora-iii_[date].pdf
├── CV_SamiMonteleone_cpqd_consultora_[date].pdf
└── [... 13 more variants ...]
```

---

## CV Auto-Selection for Easy Apply

The Easy Apply runner auto-selects the right CV based on job metadata:

```python
# From auto_apply_lib.py
def cv_for_job(self, job):
    title = job.get("role", "").lower()
    location = job.get("location", "").lower()

    if "n8n" in title:
        return self.raw["cv_mapping"]["brazil_n8n_automation"]
    if "brazil" in location or "brasil" in location:
        return self.raw["cv_mapping"]["brazil_ai_automation"]
    return self.raw["cv_mapping"]["international_ai_automation"]
```

---

## Important: Truthfulness Policy

**The CV engine enforces a strict truthfulness policy:**

- Only skills listed in `skills.primary` or `skills.secondary` are presented as strengths
- `skills_truth_defaults` maps skill names to "Yes"/"No" — used for auto-answering form questions
- `experience_defaults` provides truthful year ranges for experience questions
- `metrics` must be real, verifiable achievements
- `PROHIBITED_CLAIMS` in `application_guard.py` runtime-checks all submitted text

The system is designed to compete on real strengths, not manufactured claims.
