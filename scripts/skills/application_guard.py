#!/usr/bin/env python3
"""
application_guard.py — Gate de segurança pré-candidatura
Cadence Profissional · Onda 1 · v1.0 · 2026-04-06

Valida todos os critérios antes de permitir submit de candidatura:
- Score mínimo
- Claims verificáveis
- Rate limiting diário
- Horário de operação
- Perfil da vaga vs. targets

Uso:
    python3 application_guard.py --score 75 --title "AI Automation Engineer" --company "Acme"
    python3 application_guard.py --check-rate-limit
"""

import json
import sys
import argparse
from datetime import datetime, time as dtime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
LOGS_DIR = WORKSPACE / "logs"
LOGS_DIR.mkdir(exist_ok=True)

RATE_LOG = LOGS_DIR / "daily_applications.json"

# ─── CONFIGURAÇÕES DE SEGURANÇA ───────────────────────
SCORE_MINIMUM_APPLY = 65          # Mínimo para candidatura ativa
SCORE_MINIMUM_ANALYZE = 50        # Mínimo para analisar/enriquecer
MAX_APPLICATIONS_PER_DAY = 5      # Máximo via automação por dia
OPERATION_START = dtime(7, 0)     # Início de operações
OPERATION_END = dtime(23, 0)      # Fim de operações

# Títulos que indicam vaga fora do target (hard block)
BLOCKED_TITLE_TERMS = [
    "test automation", "qa automation", "quality automation",
    "selenium", "sdet", "testing engineer",
    "industrial automation", "scada", "plc",
    "frontend", "backend", "fullstack", "full-stack",
    "data scientist", "machine learning engineer", "mlops",
    "security engineer", "penetration", "pentest",
    "accountant", "contador",
    "mobile developer", "ios developer", "android",
]

# Claims proibidos — nunca devem aparecer em candidatura
PROHIBITED_CLAIMS = [
    "duplo diploma",
    "double degree",
    "10+ anos",
    "10+ years",
    "15 anos",
    "senior software engineer",
    "staff engineer",
    "machine learning expert",
]

# ─────────────────────────────────────────────────────


def load_rate_log() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    if RATE_LOG.exists():
        data = json.loads(RATE_LOG.read_text(encoding="utf-8"))
        if data.get("date") == today:
            return data
    return {"date": today, "count": 0, "applications": []}


def save_rate_log(log: dict):
    RATE_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


def register_application(job_id: str, company: str, score: int):
    """Registra candidatura no log diário."""
    log = load_rate_log()
    log["count"] += 1
    log["applications"].append({
        "job_id": job_id,
        "company": company,
        "score": score,
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    save_rate_log(log)


class Gate:
    """Resultado de uma verificação do guard."""
    def __init__(self):
        self.passed = True
        self.blocks = []    # Bloqueios hard — impede candidatura
        self.warnings = []  # Avisos soft — permitir com cuidado

    def block(self, reason: str):
        self.passed = False
        self.blocks.append(reason)

    def warn(self, reason: str):
        self.warnings.append(reason)

    def to_dict(self):
        return {
            "passed": self.passed,
            "blocks": self.blocks,
            "warnings": self.warnings,
        }

    def to_telegram(self) -> str:
        icon = "✅" if self.passed else "🚫"
        lines = [f"{icon} APPLICATION GUARD"]
        if self.passed:
            lines.append("Todos os gates passaram — candidatura autorizada")
        else:
            lines.append("BLOQUEADO — candidatura NÃO autorizada")
            for b in self.blocks:
                lines.append(f"  ❌ {b}")
        if self.warnings:
            lines.append("\n⚠️ Avisos:")
            for w in self.warnings:
                lines.append(f"  • {w}")
        return "\n".join(lines)


def validate_application(
    score: int,
    title: str = "",
    company: str = "",
    job_id: str = "",
    cv_text: str = "",
    force: bool = False,
) -> Gate:
    """Executa todas as validações de segurança."""
    gate = Gate()

    # 1. Score mínimo
    if score < SCORE_MINIMUM_APPLY:
        gate.block(f"Score {score}/100 abaixo do mínimo ({SCORE_MINIMUM_APPLY})")
    elif score < SCORE_MINIMUM_APPLY + 10:
        gate.warn(f"Score {score}/100 acima do mínimo mas baixo — revisar")

    # 2. Título bloqueado
    title_lower = title.lower()
    for term in BLOCKED_TITLE_TERMS:
        if term in title_lower:
            gate.block(f"Título contém termo bloqueado: '{term}'")
            break

    # 3. Rate limiting diário
    log = load_rate_log()
    if log["count"] >= MAX_APPLICATIONS_PER_DAY and not force:
        gate.block(f"Limite diário atingido: {log['count']}/{MAX_APPLICATIONS_PER_DAY} candidaturas hoje")
    elif log["count"] >= MAX_APPLICATIONS_PER_DAY - 1:
        gate.warn(f"Próxima à última candidatura do dia ({log['count']}/{MAX_APPLICATIONS_PER_DAY})")

    # 4. Horário de operação
    now = datetime.now().time()
    if not (OPERATION_START <= now <= OPERATION_END):
        gate.block(f"Fora do horário de operação ({OPERATION_START.strftime('%H:%M')}-{OPERATION_END.strftime('%H:%M')})")

    # 5. Claims proibidos no CV/texto
    if cv_text:
        cv_lower = cv_text.lower()
        for claim in PROHIBITED_CLAIMS:
            if claim in cv_lower:
                gate.block(f"Claim proibido detectado no texto: '{claim}'")

    # 6. Dados mínimos presentes
    if not title:
        gate.warn("Título da vaga não informado")
    if not company:
        gate.warn("Empresa não informada")

    return gate


def main():
    parser = argparse.ArgumentParser(description="Application Guard — Gate de segurança")
    parser.add_argument("--score", type=int, default=0)
    parser.add_argument("--title", default="")
    parser.add_argument("--company", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--cv-text", default="")
    parser.add_argument("--force", action="store_true", help="Ignorar rate limit (use com cautela)")
    parser.add_argument("--check-rate-limit", action="store_true")
    parser.add_argument("--register", action="store_true", help="Registrar candidatura aprovada")
    parser.add_argument("--telegram", action="store_true")
    args = parser.parse_args()

    if args.check_rate_limit:
        log = load_rate_log()
        remaining = MAX_APPLICATIONS_PER_DAY - log["count"]
        msg = f"📊 Rate limit hoje: {log['count']}/{MAX_APPLICATIONS_PER_DAY} | Restantes: {remaining}"
        print(msg)
        return 0

    gate = validate_application(
        score=args.score,
        title=args.title,
        company=args.company,
        job_id=args.job_id,
        cv_text=args.cv_text,
        force=args.force,
    )

    if args.telegram:
        print(gate.to_telegram())
    else:
        print(json.dumps(gate.to_dict(), indent=2))

    if gate.passed and args.register:
        register_application(args.job_id, args.company, args.score)
        print(f"✅ Candidatura registrada no log diário")

    return 0 if gate.passed else 1


if __name__ == "__main__":
    sys.exit(main())
