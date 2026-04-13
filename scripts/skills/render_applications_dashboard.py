#!/home/monts/.venv/jobhunter/bin/python
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

WORKSPACE = Path('/home/monts/.openclaw/workspace-linkedin')
STATE = WORKSPACE / 'state'
ARTIFACTS = WORKSPACE / 'artifacts' / 'applications'
DASHBOARD_DIR = WORKSPACE / 'artifacts' / 'dashboard'
INDEX_PATH = STATE / 'applications_index.json'
QUEUE_PATH = STATE / 'auto_apply_queue.json'
FOLLOWUP_PATH = STATE / 'follow_up_tracker.json'
HTML_PATH = DASHBOARD_DIR / 'applications_dashboard.html'
JSON_PATH = DASHBOARD_DIR / 'applications_dashboard.json'
OVERRIDES_PATH = STATE / 'application_stage_overrides.json'


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_json_if_exists(path: Path):
    if not path.exists():
        return None
    return load_json(path)


def iso_now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def parse_date(value: str | None):
    if not value:
        return None
    value = value.strip()
    try:
        if 'T' in value:
            return datetime.fromisoformat(value)
        return datetime.fromisoformat(value + 'T09:00:00-03:00')
    except Exception:
        return None


def artifact_exists(status: str, job_id: str | None) -> bool:
    if not job_id:
        return False
    return (ARTIFACTS / status / f'{job_id}.json').exists()


def tracking_channels(app: dict) -> list[str]:
    channels = []
    src = (app.get('source') or '').lower()
    if 'linkedin' in src:
        channels.append('LinkedIn')
    if any(k in src for k in ['recruitee', 'ats']):
        channels.append('ATS')
    if app.get('email_confirmation'):
        channels.append('Gmail')
    else:
        channels.append('Gmail')
    return channels


def certainty(app: dict, queue_map: dict[str, dict]) -> tuple[str, list[str]]:
    evidence = []
    job_id = app.get('linkedin_job_id')
    if app.get('status') == 'applied':
        evidence.append('index=applied')
    if job_id and job_id in queue_map and queue_map[job_id].get('status') == 'applied':
        evidence.append('queue=applied')
    if artifact_exists('applied', job_id):
        evidence.append('artifact=applied')
    notes = (app.get('notes') or '').lower()
    if app.get('email_confirmation') or 'email' in notes:
        evidence.append('email_confirmation')
    if 'applied state' in notes or 'confirmation' in notes or 'candidatura enviada' in notes:
        evidence.append('page_confirmation')
    if len(evidence) >= 3:
        return 'high', evidence
    if len(evidence) == 2:
        return 'medium', evidence
    return 'low', evidence


def next_follow_up(app: dict):
    if app.get('follow_up_date'):
        return app['follow_up_date']
    if app.get('next_check_after'):
        return app['next_check_after'][:10]
    applied = parse_date(app.get('applied_date'))
    if applied:
        return (applied + timedelta(days=7)).date().isoformat()
    return None


def stage_for(app: dict):
    status = app.get('status')
    if status == 'applied':
        return 'awaiting_response'
    if status in {'pipeline', 'analyzed', 'hold', 'observe'}:
        return status
    return status or 'unknown'


def build_tracker(index: dict, queue: dict):
    overrides_data = load_json_if_exists(OVERRIDES_PATH) or {}
    overrides = overrides_data.get('overrides', {})
    queue_map = {item.get('linkedin_job_id'): item for item in queue.get('items', []) if item.get('linkedin_job_id')}
    records = []
    for app in index.get('applications', []):
        cert, evidence = certainty(app, queue_map)
        override = overrides.get(app.get('id'), {})
        merged_evidence = list(dict.fromkeys(evidence + override.get('evidence_append', [])))
        status = override.get('status', app.get('status'))
        stage = override.get('stage', stage_for(app))
        next_date = override.get('next_follow_up', next_follow_up(app))
        notes = override.get('notes') or app.get('notes', '')
        rec = {
            'id': app.get('id'),
            'company': app.get('company'),
            'role': app.get('role'),
            'linkedin_job_id': app.get('linkedin_job_id'),
            'status': status,
            'stage': stage,
            'applied_date': app.get('applied_date'),
            'source': app.get('source'),
            'location': app.get('location'),
            'next_follow_up': next_date,
            'tracking_channels': tracking_channels(app),
            'certainty': cert,
            'evidence': merged_evidence,
            'notes': notes,
            'url': app.get('url'),
        }
        records.append(rec)
    records.sort(key=lambda x: (x.get('status') != 'applied', x.get('next_follow_up') or '9999-12-31', x.get('company') or ''))
    hold_observe = {'analyzed', 'hold', 'observe', 'hold_observe'}
    return {
        'generated_at': iso_now(),
        'summary': {
            'total_records': len(records),
            'applied': sum(1 for r in records if r['status'] == 'applied'),
            'pipeline': sum(1 for r in records if r['status'] == 'pipeline'),
            'hold_observe': sum(1 for r in records if r['status'] in hold_observe),
            'rejected': sum(1 for r in records if r['status'] == 'rejected'),
            'active_process': sum(1 for r in records if r['stage'] in {'screening', 'assessment', 'interview', 'action_required'} and r['status'] != 'rejected'),
            'high_certainty_applied': sum(1 for r in records if r['status'] == 'applied' and r['certainty'] == 'high'),
            'medium_certainty_applied': sum(1 for r in records if r['status'] == 'applied' and r['certainty'] == 'medium'),
            'low_certainty_applied': sum(1 for r in records if r['status'] == 'applied' and r['certainty'] == 'low'),
        },
        'records': records,
    }


def badge(text: str, kind: str) -> str:
    return f'<span class="badge {escape(kind)}">{escape(text)}</span>'


def render_html(tracker: dict):
    records = tracker['records']
    summary = tracker['summary']
    applied = [r for r in records if r['status'] == 'applied']
    pipeline = [r for r in records if r['status'] != 'applied']
    followups = sorted([r for r in applied if r.get('next_follow_up')], key=lambda x: x['next_follow_up'])

    def row(rec: dict) -> str:
        channels = ' '.join(badge(ch, 'channel') for ch in rec.get('tracking_channels', []))
        ev = '<br>'.join(escape(e) for e in rec.get('evidence', []))
        stage_badge = ''
        if rec.get('stage') and rec.get('stage') not in {rec.get('status'), 'awaiting_response'}:
            stage_badge = '<div style="margin-top:6px;">' + badge(rec.get('stage'), rec.get('stage')) + '</div>'
        return (
            '<tr>'
            f'<td><strong>{escape(rec.get("company") or "-")}</strong><div class="muted">{escape(rec.get("role") or "-")}</div></td>'
            f'<td>{badge(rec.get("status") or "-", rec.get("status") or "neutral")}{stage_badge}</td>'
            f'<td>{badge(rec.get("certainty") or "-", rec.get("certainty") or "neutral")}</td>'
            f'<td>{escape(rec.get("applied_date") or "-")}</td>'
            f'<td>{escape(rec.get("next_follow_up") or "-")}</td>'
            f'<td>{channels}</td>'
            f'<td class="small">{ev or "-"}</td>'
            '</tr>'
        )

    html = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cadence Profissional • Dashboard de Candidaturas</title>
<style>
:root {{
  --bg:#0b1020; --card:#131a2e; --card2:#0f1527; --text:#eef3ff; --muted:#9fb0d3;
  --line:#263252; --green:#31d0aa; --yellow:#f5c451; --red:#ff6b7a; --blue:#6ea8ff; --gray:#7f8db0;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; background:linear-gradient(180deg,#0b1020,#0f1730 45%,#0b1020); color:var(--text); }}
.wrapper {{ max-width:1400px; margin:0 auto; padding:28px; }}
.hero {{ display:flex; justify-content:space-between; align-items:end; gap:24px; margin-bottom:24px; }}
.hero h1 {{ margin:0; font-size:34px; }}
.hero p {{ margin:6px 0 0; color:var(--muted); }}
.grid {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:14px; margin-bottom:20px; }}
.card {{ background:rgba(19,26,46,.9); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 8px 30px rgba(0,0,0,.25); }}
.kpi {{ font-size:30px; font-weight:800; margin-top:10px; }}
.label {{ color:var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:.08em; }}
.panels {{ display:grid; grid-template-columns:1.2fr .8fr; gap:18px; margin-bottom:18px; }}
.panel-title {{ margin:0 0 14px; font-size:18px; }}
.list {{ display:flex; flex-direction:column; gap:10px; }}
.item {{ padding:12px 14px; border:1px solid var(--line); border-radius:14px; background:rgba(15,21,39,.7); }}
.item strong {{ display:block; margin-bottom:4px; }}
.muted {{ color:var(--muted); }}
.badge {{ display:inline-block; padding:4px 9px; border-radius:999px; font-size:12px; font-weight:700; margin:2px 4px 2px 0; }}
.badge.applied {{ background:rgba(49,208,170,.14); color:var(--green); }}
.badge.pipeline, .badge.analyzed, .badge.observe, .badge.hold {{ background:rgba(245,196,81,.12); color:var(--yellow); }}
.badge.rejected {{ background:rgba(255,107,122,.14); color:var(--red); }}
.badge.screening, .badge.assessment, .badge.action_required, .badge.interview {{ background:rgba(110,168,255,.14); color:var(--blue); }}
.badge.high {{ background:rgba(49,208,170,.14); color:var(--green); }}
.badge.medium {{ background:rgba(110,168,255,.14); color:var(--blue); }}
.badge.low {{ background:rgba(255,107,122,.14); color:var(--red); }}
.badge.channel {{ background:rgba(127,141,176,.14); color:#d7e0f5; }}
.badge.neutral {{ background:rgba(127,141,176,.14); color:#d7e0f5; }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ text-align:left; padding:12px 10px; border-top:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
.small {{ font-size:12px; color:var(--muted); }}
.footer {{ color:var(--muted); font-size:12px; margin-top:14px; }}
@media (max-width: 1100px) {{ .grid, .panels {{ grid-template-columns:1fr 1fr; }} }}
@media (max-width: 800px) {{ .grid, .panels, .hero {{ grid-template-columns:1fr; display:block; }} .card{{margin-bottom:14px;}} }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="hero">
    <div>
      <h1>Dashboard de Candidaturas</h1>
      <p>Cadence Profissional • visão consolidada de aplicações, follow-up e evidências</p>
    </div>
    <div class="small">Gerado em {escape(tracker['generated_at'])}</div>
  </div>

  <section class="grid">
    <div class="card"><div class="label">Total de registros</div><div class="kpi">{summary['total_records']}</div></div>
    <div class="card"><div class="label">Applied</div><div class="kpi">{summary['applied']}</div></div>
    <div class="card"><div class="label">Pipeline</div><div class="kpi">{summary['pipeline']}</div></div>
    <div class="card"><div class="label">Hold / Observe</div><div class="kpi">{summary['hold_observe']}</div></div>
    <div class="card"><div class="label">Processos ativos</div><div class="kpi">{summary['active_process']}</div></div>
    <div class="card"><div class="label">Rejected</div><div class="kpi">{summary['rejected']}</div></div>
    <div class="card"><div class="label">Applied alta certeza</div><div class="kpi">{summary['high_certainty_applied']}</div></div>
  </section>

  <section class="panels">
    <div class="card">
      <h2 class="panel-title">Fila de follow-up</h2>
      <div class="list">
        {''.join(f'<div class="item"><strong>{escape(r["company"])} • {escape(r["role"] or "")}</strong><div class="muted">Próximo follow-up: {escape(r.get("next_follow_up") or "-")} • canais: {escape(', '.join(r.get("tracking_channels", [])))}</div></div>' for r in followups[:8]) or '<div class="item">Nenhum follow-up calculado.</div>'}
      </div>
    </div>
    <div class="card">
      <h2 class="panel-title">Canais de retorno que importam</h2>
      <div class="list">
        <div class="item"><strong>1. Gmail</strong><div class="muted">Canal principal para confirmação, entrevista, rejection, teste, follow-up e replies de ATS.</div></div>
        <div class="item"><strong>2. LinkedIn</strong><div class="muted">Útil para Easy Apply, status em Minhas Vagas e mensagens de recrutadores.</div></div>
        <div class="item"><strong>3. ATS / portais próprios</strong><div class="muted">Recruitee e outros portais podem ter status próprio, mas quase sempre também disparam email.</div></div>
        <div class="item"><strong>4. Telefone / WhatsApp / SMS</strong><div class="muted">Baixa frequência, mas precisa de registro manual quando ocorrer.</div></div>
      </div>
    </div>
  </section>

  <section class="card">
    <h2 class="panel-title">Applied consolidados</h2>
    <table>
      <thead><tr><th>Empresa / Cargo</th><th>Status</th><th>Certeza</th><th>Applied</th><th>Follow-up</th><th>Canais</th><th>Evidências</th></tr></thead>
      <tbody>{''.join(row(r) for r in applied)}</tbody>
    </table>
  </section>

  <section class="card" style="margin-top:18px;">
    <h2 class="panel-title">Pipeline / processos ativos / rejeições</h2>
    <table>
      <thead><tr><th>Empresa / Cargo</th><th>Status</th><th>Certeza</th><th>Applied</th><th>Follow-up</th><th>Canais</th><th>Evidências</th></tr></thead>
      <tbody>{''.join(row(r) for r in pipeline)}</tbody>
    </table>
    <div class="footer">Arquivo canônico recomendado: <code>state/follow_up_tracker.json</code>. Pastas por status em <code>artifacts/applications/*</code> ainda contêm resíduos históricos e não devem ser a única fonte de verdade.</div>
  </section>
</div>
</body>
</html>'''
    return html


def main():
    index = load_json(INDEX_PATH)
    queue = load_json(QUEUE_PATH)
    tracker = build_tracker(index, queue)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    FOLLOWUP_PATH.write_text(json.dumps(tracker, ensure_ascii=False, indent=2), encoding='utf-8')
    JSON_PATH.write_text(json.dumps(tracker, ensure_ascii=False, indent=2), encoding='utf-8')
    HTML_PATH.write_text(render_html(tracker), encoding='utf-8')
    print(json.dumps({
        'generated_at': tracker['generated_at'],
        'followup_json': str(FOLLOWUP_PATH),
        'dashboard_json': str(JSON_PATH),
        'dashboard_html': str(HTML_PATH),
        'summary': tracker['summary'],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
