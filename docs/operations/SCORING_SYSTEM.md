# 4D Job Scoring System

## Overview

Every job discovered by the system is scored before it enters the application queue. The scoring system prevents low-signal applications and surfaces the highest-value opportunities.

## The Four Dimensions

### 1. Fit Score (0-100)

Measures alignment between the job requirements and the candidate's confirmed skills.

**Factors:**
- Keyword overlap (skills, tools, technologies)
- Experience level match (years required vs. years confirmed in `cv_base.yaml`)
- Contract type match (CLT/PJ/international vs. preferred)
- Location match (remote vs. hybrid vs. on-site preference)

**Red flags that reduce fit:**
- "QA automation" or "test automation" as primary requirement
- "Junior" or "Estagiário" as explicit level
- Pure RPA (UiPath/Automation Anywhere without AI component)
- Power systems, telecom, hardware engineering

### 2. Stretch Score (0-100)

Measures how much this role would expand the candidate's capabilities.

**High stretch (good):**
- Technologies or domains the candidate has exposure but not deep experience in
- Roles at companies known for technical excellence
- Responsibilities that require learning new systems

**Too much stretch (bad):**
- Core requirement is something completely outside the profile
- Would require misrepresenting experience level

### 3. Strategic Score (0-100)

Measures how valuable this opportunity is for long-term career positioning.

**High strategic value:**
- Companies known in the AI/automation space
- Roles with public visibility (blog posts, talks, open source)
- International exposure
- Compensation at or above target
- Referral or warm connection available

### 4. Value Score (0-100)

Measures total compensation and working conditions.

**Factors:**
- Base salary vs. target (CLT R$18k/mo, PJ R$22k/mo, international US$4.5k/mo)
- Benefits package
- Remote work flexibility
- Company stability

---

## Combined Score

```
final_score = (fit * 0.4) + (stretch * 0.2) + (strategic * 0.25) + (value * 0.15)
```

Fit is weighted highest because applying without meeting requirements wastes everyone's time and harms LinkedIn SSI.

## Thresholds

| Score | Action |
|---|---|
| ≥ 85 | Priority apply — Telegram notification immediately |
| 65–84 | Queue for next apply window |
| 50–64 | Hold — review manually if queue is small |
| < 50 | Skip — logged but not queued |

The `application_guard.py` enforces the minimum threshold of 65 before any submission proceeds.

## Scoring in Practice

Scoring runs inside `auto_apply_loop.py` and `job_detail_extractor.py`. The process:

1. **Discovery**: `linkedin_job_search.py` finds jobs matching search presets
2. **Extraction**: `job_detail_extractor.py` extracts full JD, requirements, salary (if visible), company info
3. **Scoring**: Score calculated against `cv_base.yaml` profile and current targets
4. **Queue**: Jobs above threshold added to `auto_apply_queue.json` with score breakdown
5. **Human review**: Telegram notification with score breakdown and job preview
6. **Gate**: Apply only after explicit approval

## Score Transparency

Every application artifact (`artifacts/applications/applied/`) includes the full score breakdown:

```json
{
  "job_id": "...",
  "scores": {
    "fit": 82,
    "stretch": 71,
    "strategic": 88,
    "value": 75,
    "final": 81.15
  },
  "score_notes": {
    "fit_positives": ["Python automation", "AI agents", "API integration"],
    "fit_negatives": ["Salesforce not in profile"],
    "strategic_reason": "Series B startup, AI-first, remote-first"
  }
}
```

## Calibration

The scoring weights and thresholds can be adjusted based on:
- Response rate data (which score buckets get responses)
- Market conditions (tighten in low-demand periods)
- Personal priorities (increase strategic weight if pivoting industries)

See `planning/ROADMAP.md` for planned A/B testing of scoring parameters.
