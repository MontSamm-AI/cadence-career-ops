#!/home/monts/.venv/jobhunter/bin/python
"""Utilitários compartilhados para o pipeline LinkedIn Easy Apply.
Cadence Profissional · 2026-04-09
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE = Path("/home/monts/.openclaw/workspace-linkedin")
STATE_DIR = WORKSPACE / "state"
ARTIFACTS_DIR = WORKSPACE / "artifacts" / "applications"
BROWSER_DIR = WORKSPACE / "artifacts" / "browser"
CDP_URL = "http://127.0.0.1:9222"

PROFILE_PATH = STATE_DIR / "application_profile.json"
RULES_PATH = STATE_DIR / "auto_apply_rules.json"
QUEUE_PATH = STATE_DIR / "auto_apply_queue.json"
INDEX_PATH = STATE_DIR / "applications_index.json"
COMPENSATION_PATH = STATE_DIR / "compensation_reference.json"


@dataclass
class CandidateProfile:
    raw: Dict[str, Any]

    @property
    def primary_email(self) -> str:
        return self.raw["candidate"]["emails"]["primary"]

    @property
    def all_emails(self) -> List[str]:
        emails = self.raw["candidate"]["emails"]
        return [v for v in emails.values() if v]

    @property
    def phone_e164(self) -> str:
        return self.raw["candidate"]["phone"]["number_e164"]

    @property
    def phone_national(self) -> str:
        return self.raw["candidate"]["phone"]["number_national"]

    @property
    def city_country(self) -> str:
        loc = self.raw["candidate"]["location"]
        return f"{loc['city']}, {loc['country']}"

    @property
    def approved_short_answers(self) -> Dict[str, str]:
        return self.raw.get("approved_short_answers", {})

    @property
    def experience_defaults(self) -> Dict[str, Any]:
        return self.raw.get("experience_defaults", {})

    @property
    def skills_truth_defaults(self) -> Dict[str, Any]:
        return self.raw.get("skills_truth_defaults", {})

    def cv_for_job(self, job: Dict[str, Any]) -> Dict[str, str]:
        title = (job.get("role") or job.get("title") or "").lower()
        location = (job.get("location") or "").lower()
        url = (job.get("url") or "").lower()
        if "n8n" in title:
            return self.raw["cv_mapping"]["brazil_n8n_automation"]
        if any(x in location for x in ["brazil", "brasil", "sp"]) or "linkedin.com/jobs" in url and "brazil" in location:
            return self.raw["cv_mapping"]["brazil_ai_automation"]
        return self.raw["cv_mapping"]["international_ai_automation"]


@dataclass
class CompensationReference:
    raw: Dict[str, Any]

    def role_family_for_job(self, job: Dict[str, Any]) -> str:
        title = f"{job.get('role', '')} {job.get('title', '')}".lower()
        if any(k in title for k in ["n8n", "workflow", "no-code", "nocode", "automa"]):
            return "automation_consulting"
        if any(k in title for k in ["freelance", "contract", "contractor"]):
            return "automation_consulting"
        return "ai_automation"

    def job_override(self, job: Dict[str, Any]) -> Dict[str, Any]:
        job_id = job.get("linkedin_job_id")
        return self.raw.get("job_overrides", {}).get(job_id, {})

    def seniority_multiplier(self, job: Dict[str, Any]) -> float:
        title = f"{job.get('role', '')} {job.get('title', '')}".lower()
        modifiers = self.raw.get("seniority_modifiers", {})
        if any(k in title for k in ["head", "principal"]):
            return modifiers.get("head_principal", 1.20)
        if "lead" in title:
            return modifiers.get("lead", 1.18)
        if "senior" in title or "sênior" in title:
            return modifiers.get("senior", 1.12)
        if "specialist" in title or "especialista" in title:
            return modifiers.get("specialist", 1.08)
        return modifiers.get("base", 1.0)

    def infer_track(self, job: Dict[str, Any], question_text: str) -> str:
        question = question_text.lower()
        location = (job.get("location") or "").lower()
        if any(k in question for k in ["usd", "us$", "dollar", "dólar"]):
            return "international_remote"
        if any(k in question for k in ["hour", "hourly", "/hr", "hora", "horário", "hora/aula"]):
            return "freelance"
        if any(k in question for k in ["daily", "per day", "dia", "diária", "diario", "diária"]):
            return "freelance"
        if "clt" in question:
            return "br_clt"
        if any(k in question for k in ["freelance", "contract", "contractor", "pj", "pessoa jurídica", "prestador"]):
            return "br_pj"
        override = self.job_override(job)
        if override.get("track"):
            return override["track"]
        if any(k in location for k in ["remote", "remoto", "worldwide", "global"]) and "brazil" not in location and "brasil" not in location:
            return "international_remote"
        return "br_clt"

    def _track_defaults(self, track: str) -> Dict[str, Any]:
        return self.raw.get("tracks", {}).get(track, {})

    def target_amount(self, job: Dict[str, Any], track: str) -> float:
        override = self.job_override(job)
        if track in override:
            return float(override[track])
        role_family = self.role_family_for_job(job)
        family = self.raw.get("role_families", {}).get(role_family, {})
        if track in family and family[track].get("default") is not None:
            base = float(family[track]["default"])
        else:
            base = float(self._track_defaults(track).get("default", 0))
        return round(base * self.seniority_multiplier(job), 2)

    def format_amount(self, amount: float, track: str, unit: str = "monthly", numeric_only: bool = False) -> str:
        if track == "international_remote":
            value = int(round(amount))
            if numeric_only:
                return str(value)
            if unit == "annual":
                return f"USD {value:,}/year".replace(",", ".")
            if unit == "hourly":
                return f"USD {value}/hour"
            if unit == "daily":
                return f"USD {value}/day"
            return f"USD {value:,}/month".replace(",", ".")
        value = int(round(amount))
        if numeric_only:
            return str(value)
        if unit == "annual":
            return f"R$ {value:,}/ano".replace(",", ".")
        if unit == "hourly":
            return f"R$ {value}/hora"
        if unit == "daily":
            return f"R$ {value}/dia"
        return f"R$ {value:,}/mês".replace(",", ".")

    def compensation_answer(self, job: Dict[str, Any], question_text: str, numeric_only: bool = False) -> Dict[str, Any]:
        question = question_text.lower()
        track = self.infer_track(job, question)
        unit = "monthly"
        if any(k in question for k in ["annual", "annually", "yearly", "per year", "anual", "ano"]):
            unit = "annual"
        elif any(k in question for k in ["hour", "hourly", "/hr", "hora", "horário"]):
            unit = "hourly"
        elif any(k in question for k in ["daily", "per day", "dia", "diária", "diario"]):
            unit = "daily"

        amount = self.target_amount(job, track)
        track_defaults = self._track_defaults(track)

        if unit == "annual":
            amount = amount * float(track_defaults.get("annual_multiplier", 12))
        elif unit == "hourly":
            amount = float(track_defaults.get("hourly_default", amount))
        elif unit == "daily":
            amount = float(track_defaults.get("daily_default", amount))

        return {
            "track": track,
            "unit": unit,
            "amount": amount,
            "answer": self.format_amount(amount, track, unit=unit, numeric_only=numeric_only),
        }

    def range_choice(self, options: List[str], target_amount: float) -> Optional[str]:
        def extract_numbers(text: str) -> List[int]:
            numbers = re.findall(r"\d+[\d.,]*", text)
            parsed = []
            for n in numbers:
                digits = re.sub(r"\D", "", n)
                if digits:
                    parsed.append(int(digits))
            return parsed

        for option in options:
            nums = extract_numbers(option)
            if not nums:
                continue
            if len(nums) >= 2 and nums[0] <= target_amount <= nums[1]:
                return option
            if len(nums) == 1 and abs(nums[0] - target_amount) <= max(500, target_amount * 0.15):
                return option
        scored = []
        for option in options:
            nums = extract_numbers(option)
            if nums:
                scored.append((abs(nums[0] - target_amount), option))
        if scored:
            scored.sort(key=lambda x: x[0])
            return scored[0][1]
        return None


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_profile() -> CandidateProfile:
    return CandidateProfile(load_json(PROFILE_PATH))


def load_rules() -> Dict[str, Any]:
    return load_json(RULES_PATH)


def load_compensation_reference() -> CompensationReference:
    return CompensationReference(load_json(COMPENSATION_PATH))


def load_queue() -> Dict[str, Any]:
    return load_json(QUEUE_PATH)


def save_queue(data: Dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    save_json(QUEUE_PATH, data)


def load_index() -> Dict[str, Any]:
    return load_json(INDEX_PATH)


def save_index(data: Dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    save_json(INDEX_PATH, data)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")[:120]


def artifact_path(status: str, job: Dict[str, Any]) -> Path:
    job_id = job.get("linkedin_job_id") or slugify(job.get("url", "job"))
    return ARTIFACTS_DIR / status / f"{job_id}.json"


def write_artifact(status: str, payload: Dict[str, Any]) -> Path:
    path = artifact_path(status, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def detect_job_id(url: str) -> Optional[str]:
    m = re.search(r"/jobs/view/(\d+)", url or "")
    return m.group(1) if m else None


def update_index_with_result(job: Dict[str, Any], result: Dict[str, Any]) -> None:
    idx = load_index()
    apps = idx.setdefault("applications", [])
    linkedin_job_id = job.get("linkedin_job_id") or detect_job_id(job.get("url", ""))
    existing = None
    for app in apps:
        if app.get("linkedin_job_id") == linkedin_job_id:
            existing = app
            break
    record = {
        "id": result.get("record_id") or f"{slugify(job.get('company','company'))}_{slugify(job.get('role','role'))}_{datetime.now().strftime('%Y%m%d')}",
        "company": job.get("company"),
        "role": job.get("role") or job.get("title"),
        "linkedin_job_id": linkedin_job_id,
        "url": job.get("url"),
        "status": result.get("status"),
        "applied_date": datetime.now().strftime("%Y-%m-%d"),
        "source": result.get("source", "linkedin_easy_apply"),
        "cv_used": result.get("cv_used"),
        "location": job.get("location"),
        "notes": result.get("notes", ""),
        "tags": result.get("tags", []),
    }
    if existing:
        existing.update(record)
    else:
        apps.append(record)
    summary = idx.setdefault("summary", {})
    summary["total"] = len(apps)
    summary["applied"] = len([a for a in apps if a.get("status") == "applied"])
    summary["pipeline"] = len([a for a in apps if a.get("status") == "pipeline"])
    summary["hold_observe"] = len([a for a in apps if a.get("status") in {"analyzed", "hold", "observe"}])
    save_index(idx)


def update_queue_item(job_id: str, updates: Dict[str, Any]) -> None:
    queue = load_queue()
    for item in queue.get("items", []):
        if item.get("linkedin_job_id") == job_id:
            item.update(updates)
    save_queue(queue)
