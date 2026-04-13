#!/usr/bin/env python3
"""
browser_recon.py — Reconnaissance de abas abertas no Chrome via CDP
Cadence Profissional · Onda 1 · v1.0 · 2026-04-06

Conecta ao Chrome via CDP, lista todas as abas abertas,
classifica por tipo (linkedin, ats, other) e salva snapshot JSON.

Uso:
    python3 browser_recon.py
    python3 browser_recon.py --output /path/to/output.json
    python3 browser_recon.py --open-jobs   # só abas de vagas
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
import urllib.request

# Caminhos
WORKSPACE = Path(__file__).parent.parent
ARTIFACTS = WORKSPACE / "artifacts" / "browser" / "tabs"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

CDP_URL = "http://127.0.0.1:9222"

# Classificadores de URL
JOB_PLATFORMS = {
    "linkedin.com/jobs": "linkedin_jobs",
    "linkedin.com/in/": "linkedin_profile",
    "linkedin.com/feed": "linkedin_feed",
    "glassdoor.com": "glassdoor",
    "indeed.com": "indeed",
    "infojobs": "infojobs",
    "pandapé": "pandape",
    "pandape": "pandape",
    "recruitee.com": "recruitee_ats",
    "greenhouse.io": "greenhouse_ats",
    "lever.co": "lever_ats",
    "workday.com": "workday_ats",
    "hubxp.com.br": "hubxp",
    "workana.com": "workana",
    "upwork.com": "upwork",
    "gupy.io": "gupy",
    "vagas.com": "vagas_br",
    "catho.com": "catho",
}


def check_cdp():
    """Verifica se CDP está acessível."""
    try:
        req = urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=3)
        data = json.loads(req.read())
        return True, data.get("Browser", "Chrome")
    except Exception as e:
        return False, str(e)


def get_tabs():
    """Lista todas as abas abertas no Chrome."""
    try:
        req = urllib.request.urlopen(f"{CDP_URL}/json/list", timeout=5)
        tabs = json.loads(req.read())
        return [t for t in tabs if t.get("type") == "page"]
    except Exception as e:
        print(f"[ERRO] Não foi possível listar abas: {e}")
        return []


def classify_tab(tab: dict) -> dict:
    """Classifica uma aba por tipo e relevância."""
    url = tab.get("url", "").lower()
    title = tab.get("title", "")

    platform = "other"
    for pattern, platform_name in JOB_PLATFORMS.items():
        if pattern in url:
            platform = platform_name
            break

    is_job = any(kw in url + title.lower() for kw in [
        "job", "vaga", "cargo", "posit", "career", "hiring",
        "engineer", "especialist", "developer", "analyst",
        "engenheiro", "analista", "especialista", "recrutamento",
        "pesquisador", "automation", "automação", "ia ", "ai "
    ])

    return {
        "tab_id": tab.get("id"),
        "url": tab.get("url"),
        "title": title,
        "platform": platform,
        "is_job_page": is_job,
        "websocket_url": tab.get("webSocketDebuggerUrl"),
    }


def extract_tab_text_via_playwright(tab: dict) -> str:
    """Extrai texto principal de uma aba via Playwright CDP."""
    try:
        from playwright.sync_api import sync_playwright
        ws_url = tab.get("websocket_url")
        if not ws_url:
            return ""

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            for ctx in browser.contexts:
                for page in ctx.pages:
                    if page.url == tab["url"]:
                        # Extrair texto relevante da página
                        text = page.evaluate("""() => {
                            const selectors = [
                                '.job-details-jobs-unified-top-card__job-title',
                                '.jobs-unified-top-card__company-name',
                                '.jobs-description__content',
                                'h1', 'h2', '.job-title', '.company-name',
                                '[data-test="job-title"]', '.position-title'
                            ];
                            let texts = [];
                            for (let sel of selectors) {
                                let els = document.querySelectorAll(sel);
                                els.forEach(el => {
                                    let t = el.innerText?.trim();
                                    if (t && t.length > 3) texts.push(t);
                                });
                            }
                            // Fallback: body text (limitado)
                            if (texts.length === 0) {
                                texts.push(document.body.innerText.slice(0, 2000));
                            }
                            return texts.join(' | ');
                        }""")
                        return text[:3000] if text else ""
            browser.close()
    except Exception as e:
        pass
    return ""


def run_recon(extract_text: bool = False, jobs_only: bool = False) -> dict:
    """Executa recon completo e retorna dados estruturados."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Verificar CDP
    cdp_ok, browser_info = check_cdp()
    if not cdp_ok:
        return {"error": f"CDP não acessível: {browser_info}", "timestamp": ts}

    # Listar abas
    tabs = get_tabs()
    classified = [classify_tab(t) for t in tabs]

    if jobs_only:
        classified = [t for t in classified if t["is_job_page"]]

    # Extrair texto se solicitado
    if extract_text:
        for tab in classified:
            tab["extracted_text"] = extract_tab_text_via_playwright(tab)

    result = {
        "timestamp": ts,
        "cdp_ok": cdp_ok,
        "browser": browser_info,
        "total_tabs": len(get_tabs()),
        "tabs_returned": len(classified),
        "tabs": classified,
        "summary": {
            "job_pages": len([t for t in classified if t["is_job_page"]]),
            "platforms": list({t["platform"] for t in classified}),
        }
    }

    # Salvar snapshot
    output_path = ARTIFACTS / f"recon_{ts_file}.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    return result


def format_telegram(result: dict) -> str:
    """Formata resultado para mensagem Telegram."""
    if "error" in result:
        return f"❌ RECON FALHOU: {result['error']}"

    tabs = result.get("tabs", [])
    job_tabs = [t for t in tabs if t["is_job_page"]]

    lines = [
        f"🔍 RECON DO BROWSER — {result['timestamp']}",
        f"Abas totais: {result['total_tabs']} | Vagas: {result['summary']['job_pages']}",
        "",
    ]

    if job_tabs:
        lines.append("📋 VAGAS ABERTAS NO CHROME:")
        for tab in job_tabs[:8]:
            lines.append(f"  [{tab['platform']}] {tab['title'][:60]}")
            lines.append(f"  {tab['url'][:80]}")
    else:
        lines.append("(Nenhuma aba de vaga detectada)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Browser Recon via CDP")
    parser.add_argument("--jobs-only", action="store_true", help="Só abas de vagas")
    parser.add_argument("--extract-text", action="store_true", help="Extrair texto das páginas")
    parser.add_argument("--output", help="Caminho de saída JSON")
    parser.add_argument("--telegram", action="store_true", help="Formato Telegram")
    args = parser.parse_args()

    result = run_recon(extract_text=args.extract_text, jobs_only=args.jobs_only)

    if args.telegram:
        print(format_telegram(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.output:
        Path(args.output).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return 0 if result.get("cdp_ok") else 1


if __name__ == "__main__":
    sys.exit(main())
